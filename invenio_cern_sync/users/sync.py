# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync users sync API."""

import time
import uuid
from datetime import datetime, timezone

from flask import current_app
from invenio_accounts.models import User, UserIdentity
from invenio_db import db
from sqlalchemy.orm.exc import NoResultFound

from ..authz.client import AuthZService, KeycloakService
from ..authz.serializer import serialize_cern_identities
from ..ldap.client import LdapClient
from ..ldap.serializer import serialize_ldap_users
from ..logging import log_info, log_warning
from ..sso import cern_remote_app_name
from .api import create_user, update_existing_user


def _log_user_data_changed(
    log_uuid,
    log_name,
    log_action,
    ra_extra_data,
    identity_id,
    previous_username,
    previous_email,
    new_username,
    new_email,
):
    """Log a warning about username/e-mail change."""
    log_msg = f"Username/e-mail changed for UserIdentity.id #{identity_id}. Local DB username/e-mail: `{previous_username}` `{previous_email}`. New from CERN DB: `{new_username}` `{new_email}`."
    log_warning(log_name, dict(action=log_action, msg=log_msg), log_uuid=log_uuid)

    # record this change in the RemoteAccount.extra_data
    ra_extra_data.append(
        dict(
            datetime=datetime.now(tz=timezone.utc).isoformat(),
            action="userdata_changed",
            previous_username=previous_username,
            previous_email=previous_email,
            new_username=new_username,
            new_email=new_email,
        )
    )
    return ra_extra_data


def _log_identity_id_changed(
    log_uuid,
    log_name,
    log_action,
    ra_extra_data,
    username,
    email,
    previous_identity_id,
    new_identity_id,
):
    """Log a warning about Identity Id change."""
    log_msg = f"Identity Id changed for User `{username}` `{email}`. Previous UserIdentity.id in the local DB: `{previous_identity_id}` - New Identity Id from CERN DB: `{new_identity_id}`."
    log_warning(log_name, dict(action=log_action, msg=log_msg), log_uuid=log_uuid)

    # record this change in the RemoteAccount.extra_data
    ra_extra_data.append(
        dict(
            datetime=datetime.now(tz=timezone.utc).isoformat(),
            action="identityId_changed",
            previous_identity_id=previous_identity_id,
            new_identity_id=new_identity_id,
        )
    )
    return ra_extra_data


def _update_existing(users, serializer_fn, log_uuid, log_name, persist_every=500):
    """Update existing users in batches and return a list of missing users to insert."""
    missing = []
    updated = set()
    log_action = "updating-existing-users"
    log_info(log_name, dict(action=log_action, status="started"), log_uuid=log_uuid)

    processed_count = 0

    for invenio_user in serializer_fn(users):
        user = user_identity = None

        # Fetch the local user by `identity_id`, the CERN unique id
        user_identity = UserIdentity.query.filter_by(
            id=invenio_user["user_identity_id"]
        ).one_or_none()
        # Fetch the local user also by email and username, so we can compare
        user = User.query.filter_by(
            email=invenio_user["email"], username=invenio_user["username"]
        ).one_or_none()
        is_missing = not user_identity and not user
        if is_missing:
            # The user does not exist in the DB.
            # The creation of new users is done after all updates completed,
            # to avoid conflicts in case other `identity_id` have changed.
            missing.append(invenio_user)
            continue
        else:
            # We start checking first if we found the user by `identity_id`
            # The assumption is that `identity_id` and `e-mail/username` cannot both
            # have changed since the previous sync.
            if user_identity and (not user or user.id != user_identity.id_user):
                # The `e-mail/username` changed.
                # The User `e-mail/username` referenced by this `identity_id`
                # will have to be updated.
                user = user_identity.user
                _ra_extra_data = invenio_user["remote_account_extra_data"].get(
                    "changes", []
                )
                ra_extra_data = _log_user_data_changed(
                    log_uuid,
                    log_name,
                    log_action,
                    ra_extra_data=_ra_extra_data,
                    identity_id=invenio_user["user_identity_id"],
                    previous_username=user.username,
                    previous_email=user.email,
                    new_username=invenio_user["username"],
                    new_email=invenio_user["email"],
                )
                invenio_user["remote_account_extra_data"]["changes"] = ra_extra_data
            elif user and (not user_identity or user_identity.id_user != user.id):
                # The `identity_id` changed or it does not exist yet.
                try:
                    user_identity = UserIdentity.query.filter_by(id_user=user.id).one()
                except NoResultFound:
                    UserIdentity.create(
                        user,
                        cern_remote_app_name,
                        invenio_user["user_identity_id"],
                    )
                    db.session.flush()
                    user_identity = UserIdentity.query.filter_by(id_user=user.id).one()

                _ra_extra_data = invenio_user["remote_account_extra_data"].get(
                    "changes", []
                )
                ra_extra_data = _log_identity_id_changed(
                    log_uuid,
                    log_name,
                    log_action,
                    ra_extra_data=_ra_extra_data,
                    username=invenio_user["username"],
                    email=invenio_user["email"],
                    previous_identity_id=user_identity.id,
                    new_identity_id=invenio_user["user_identity_id"],
                )
                invenio_user["remote_account_extra_data"]["changes"] = ra_extra_data
            else:
                # Both found, make sure that the `identity_id` and the `e-mail/username`
                # are associated to the same user.
                assert (
                    user.id == user_identity.id_user
                ), f"User and UserIdentity are not correctly linked for user #{user.id} and user_identity #{user_identity.id}"

        if update_existing_user(user, user_identity, invenio_user):
            updated.add(user.id)

        processed_count += 1
        # Commit every `persist_every` iterations
        if processed_count % persist_every == 0:
            db.session.commit()

    # Final commit for any remaining uncommitted changes
    db.session.commit()

    log_info(
        log_name,
        dict(action=log_action, status="completed", updated_count=len(updated)),
        log_uuid=log_uuid,
    )
    return missing, updated


def _insert_missing(invenio_users, log_uuid, log_name, persist_every=500):
    """Insert users in batches."""
    log_action = "inserting-missing-users"
    log_info(log_name, dict(action=log_action, status="started"), log_uuid=log_uuid)

    inserted = set()
    processed_count = 0

    for invenio_user in invenio_users:
        try:
            if invenio_user["username"].startswith("_"):
                # Seems that the auth team uses this as a temporal solution for
                # users that need to be imported in the system after they left CERN
                current_app.logger.warning(
                    f"Skipping user with username starting with `_`: {invenio_user}"
                )
                continue

            with db.session.begin_nested():
                _id = create_user(invenio_user)
                inserted.add(_id)

            processed_count += 1

            # Commit every `persist_every` iterations
            if processed_count % persist_every == 0:
                db.session.commit()

        except Exception as e:
            current_app.logger.warning(
                f"Error creating user from CERN data: {e}. Skipping this user... User: {invenio_user}"
            )
            continue

    # Final commit for any remaining uncommitted changes
    db.session.commit()

    log_info(
        log_name,
        dict(action=log_action, status="completed", inserted_count=len(inserted)),
        log_uuid=log_uuid,
    )
    return inserted


def sync(method="AuthZ", **kwargs):
    """Sync CERN accounts with local db."""
    if method not in ["AuthZ", "LDAP"]:
        raise ValueError(
            f"Unknown param method {method}. Possible values `AuthZ` or `LDAP`."
        )

    log_uuid = str(uuid.uuid4())
    log_name = "users-sync"
    log_info(
        log_name,
        dict(action="fetching-cern-users", status="started", method=method),
        log_uuid=log_uuid,
    )
    start_time = time.time()

    if method == "AuthZ":
        overridden_params = kwargs.get("keycloak_service", dict())
        keycloak_service = KeycloakService(**overridden_params)

        overridden_params = kwargs.get("authz_service", dict())
        authz_client = AuthZService(keycloak_service, **overridden_params)

        overridden_params = kwargs.get("identities", dict())
        users = authz_client.get_identities(**overridden_params)
        serializer_fn = serialize_cern_identities
    elif method == "LDAP":
        overridden_params = kwargs.get("ldap", dict())
        ldap_client = LdapClient(**overridden_params)
        users = ldap_client.get_primary_accounts()
        serializer_fn = serialize_ldap_users
    else:
        raise ValueError(
            f"Unknown param method {method}. Possible values `AuthZ` or `LDAP`."
        )

    missing_invenio_users, updated_ids = _update_existing(
        users, serializer_fn, log_uuid, log_name
    )
    inserted_ids = _insert_missing(missing_invenio_users, log_uuid, log_name)

    total_time = time.time() - start_time
    log_info(log_name, dict(status="completed", time=total_time), log_uuid=log_uuid)

    return list(updated_ids.union(inserted_ids))
