# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync users sync API."""

import time
import uuid
from datetime import datetime

from invenio_accounts.models import User, UserIdentity
from invenio_db import db
from invenio_users_resources.services.users.tasks import reindex_users
from py import log
from pytz import UTC

from ..authz.client import AuthZService, KeycloakService
from ..authz.serializer import serialize_cern_identities
from ..ldap.client import LdapClient
from ..ldap.serializer import serialize_ldap_users
from ..logging import log_info, log_warning
from .api import create_user, update_existing_user


def _log_user_data_changed(
    log_uuid,
    log_action,
    ra_extra_data,
    person_id,
    previous_username,
    previous_email,
    new_username,
    new_email,
):
    """Log a warning about username/e-mail change."""
    log_msg = f"Username/e-mail changed for UserIdentity.id #{person_id}. Local DB username/e-mail: `{previous_username}` `{previous_email}`. New from CERN DB: `{new_username}` `{new_email}`."
    log_warning(log_uuid, log_action, dict(msg=log_msg))

    # record this change in the RemoteAccount.extra_data
    ra_extra_data.append(
        dict(
            date=datetime.now(datetime.UTC),
            action="userdata_changed",
            previous_username=previous_username,
            previous_email=previous_email,
            new_username=new_username,
            new_email=new_email,
        )
    )
    return ra_extra_data


def _log_person_id_changed(
    log_uuid,
    log_action,
    ra_extra_data,
    username,
    email,
    previous_person_id,
    new_person_id,
):
    """Log a warning about Person Id change."""
    log_msg = f"Person Id changed for User `{username}` `{email}`. Previous UserIdentity.id in the local DB: `{previous_person_id}` - New Person Id from CERN DB: `{new_person_id}`."
    log_warning(log_uuid, log_action, dict(msg=log_msg))

    # record this change in the RemoteAccount.extra_data
    ra_extra_data.append(
        dict(
            date=datetime.now(datetime.UTC),
            action="personId_changed",
            previous_person_id=previous_person_id,
            new_person_id=new_person_id,
        )
    )
    return ra_extra_data


def _update_existing(invenio_users, log_uuid):
    """Update existing users and return a list of missing users to insert."""
    missing = []
    updated = set()
    log_action = "updating_existing_users"
    log_info(log_uuid, log_action, dict(status="started"))

    for invenio_user in invenio_users(invenio_users):
        user = user_identity = None

        # Fetch the local user by `person_id`, the CERN unique id
        user_identity = UserIdentity.query.filter_by(
            id=invenio_user["person_id"]
        ).one_or_none()
        # Fetch the local user also by email and username, so we can compare
        user = User.query.filter_by(
            email=invenio_user["email"], username=invenio_user["username"]
        ).one_or_none()
        is_missing = not user_identity and not user
        if is_missing:
            # The user does not exist in the DB.
            # The creation of new users is done after all updates completed,
            # to avoid conflicts in case other `person_id` have changed.
            missing.append(invenio_user)
            continue
        else:
            # We start checking first if we found the user by `person_id`
            # The assumption is that `person_id` and `e-mail/username` cannot both
            # have changed since the previous sync.
            if user_identity and not user or user.id != user_identity.id_user:
                # The `e-mail/username` changed.
                # The User `e-mail/username` referenced by this `person_id`
                # will have to be updated.
                user = user_identity.user
                _ra_extra_data = invenio_user["remote_account_extra_data"].get(
                    "changes", []
                )
                ra_extra_data = _log_user_data_changed(
                    log_uuid,
                    log_action,
                    ra_extra_data=_ra_extra_data,
                    person_id=invenio_user["person_id"],
                    previous_username=user.username,
                    previous_email=user.email,
                    new_username=invenio_user["username"],
                    new_email=invenio_user["email"],
                )
                invenio_user["remote_account_extra_data"]["changes"] = ra_extra_data
            elif user and not user_identity or user_identity.id_user != user.id:
                # The `person_id` changed.
                # The `person_id` of the UserIdentity associated to the User
                # will have to be updated.
                user_identity = UserIdentity.query.filter_by(id_user=user.id).one()

                _ra_extra_data = invenio_user["remote_account_extra_data"].get(
                    "changes", []
                )
                ra_extra_data = _log_person_id_changed(
                    log_uuid,
                    log_action,
                    ra_extra_data=_ra_extra_data,
                    username=invenio_user["username"],
                    email=invenio_user["email"],
                    previous_person_id=user_identity.id,
                    new_person_id=invenio_user["person_id"],
                )
                invenio_user["remote_account_extra_data"]["changes"] = ra_extra_data
            else:
                # Both found, make sure that the `person_id` and the `e-mail/username`
                # are associated to the same user.
                assert (
                    user.id == user_identity.id_user
                ), f"User and UserIdentity are not correctly linked for user #{user.id} and user_identity #{user_identity.id}"

        update_existing_user(user, user_identity, invenio_user)
        updated.add(user.id)

    # persist changes before starting with the inserting of missing users
    db.session.commit()
    log_info(log_uuid, log_action, dict(status="completed", updated_count=len(updated)))
    return missing, updated


def _insert_missing(invenio_users, log_uuid):
    """Insert users."""
    log_info(
        log_uuid,
        "inserting_missing_users",
        dict(status="started", count=len(invenio_users)),
    )

    inserted = set()
    for invenio_user in invenio_users:
        _id = create_user(invenio_user)
        inserted.add(_id)

    db.session.commit()
    log_info(
        log_uuid,
        "inserting_missing_users",
        dict(status="completed", inserted_count=len(inserted)),
    )
    return inserted


def sync(method="AuthZ", **kwargs):
    """Sync CERN accounts with local db."""
    if method not in ["AuthZ", "LDAP"]:
        raise ValueError(
            f"Unknown param method {method}. Possible values `AuthZ` or `LDAP`."
        )

    log_uuid = str(uuid.uuid4())
    log_info(log_uuid, "users_sync", dict(status="started", method=method))
    start_time = time.time()

    if method == "AuthZ":
        overridden_params = kwargs.get("keycloak_service", dict())
        keycloak_service = KeycloakService(**overridden_params)

        overridden_params = kwargs.get("authz_service", dict())
        authz_client = AuthZService(keycloak_service, **overridden_params)

        overridden_params = kwargs.get("identities_fields", dict())
        cern_identities = authz_client.get_identities(**overridden_params)
        invenio_users = serialize_cern_identities(cern_identities)
    elif method == "LDAP":
        overridden_params = kwargs.get("ldap", dict())
        ldap_client = LdapClient(**overridden_params)
        ldap_users = ldap_client.get_primary_accounts()
        invenio_users = serialize_ldap_users(ldap_users)
    else:
        raise ValueError(
            f"Unknown param method {method}. Possible values `AuthZ` or `LDAP`."
        )

    log_info(log_uuid, "users_sync", dict(status="completed", count=len(invenio_users)))

    missing_invenio_users, updated_ids = _update_existing(invenio_users, log_uuid)
    inserted_ids = _insert_missing(missing_invenio_users, log_uuid)

    reindex_users.delay(updated_ids + inserted_ids)

    total_time = time.time() - start_time
    log_info(log_uuid, "sync_done", dict(time=total_time))
