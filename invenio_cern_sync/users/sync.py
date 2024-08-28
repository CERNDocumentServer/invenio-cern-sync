# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync users sync API."""

import uuid
import time

from invenio_accounts.models import User, UserIdentity
from invenio_db import db
from invenio_users_resources.services.users.tasks import reindex_users

from ..logging import log_info, log_error, log_warning
from ..ldap.client import LdapClient
from .api import create_user, update_existing_user
from .serializer import serialize_ldap_users


def _update_existing(ldap_users, log_uuid):
    """Update existing users and return a list of missing users to insert."""
    missing = []
    updated = set()
    log_action = "updating_existing_users"
    log_info(log_uuid, log_action, dict(status="started"))

    for invenio_ldap_user in serialize_ldap_users(ldap_users):
        user = user_identity = None

        # The unique CERN id to find previously inserted users should be the `person_id`
        user_identity = UserIdentity.query.filter_by(
            id=invenio_ldap_user["person_id"]
        ).one_or_none()
        if user_identity:
            user = user_identity.user
        else:
            # user identity not found by `person_id`. Might be a new user, or
            # the person id might have changed (because of a human mistake).
            # Try to look up the user by matching both `username` and `e-mail`, in
            # case the `person_id` changed.
            user = User.query.filter_by(
                email=invenio_ldap_user["email"], username=invenio_ldap_user["username"]
            ).one_or_none()
            if user:
                # user found, looks like that the `person_id` was updated!
                user_identity = UserIdentity.query.filter_by(id_user=user.id).first()

                log_msg = f"User `{invenio_ldap_user["email"]}` (username `{invenio_ldap_user["username"]}`) has different profile id. Local db: `{user_identity.id}` - LDAP: `{invenio_ldap_user["person_id"]}`"
                log_warning(log_uuid, log_action, dict(msg=log_msg))

        if (user and not user_identity) or (user_identity and not user):
            # Something very wrong here, should never happen
            log_msg = f"User and user_identity are not correctly linked for user f{user} and user_identity f{user_identity}"
            log_error(log_uuid, log_action, dict(msg=log_msg))
        elif user and user_identity:
            # User found, update info
            update_existing_user(user, user_identity, invenio_ldap_user)
            updated.add(user.id)
        else:
            # The user does not exist in the DB.
            # The creation of new users is done after all updates completed,
            # to avoid conflicts in case other `person_id` have changed
            missing.append(invenio_ldap_user)

    # persist changes before inserting
    db.session.commit()
    log_info(log_uuid, log_action, dict(status="completed", updated_count=len(updated)))
    return missing, updated


def _insert_missing(invenio_ldap_users, log_uuid):
    """Insert users."""
    log_info(
        log_uuid,
        "inserting_missing_users",
        dict(status="started", count=len(invenio_ldap_users)),
    )

    inserted = set()
    for invenio_ldap_user in invenio_ldap_users:
        _id = create_user(invenio_ldap_user)
        inserted.add(_id)

    db.session.commit()
    log_info(
        log_uuid,
        "inserting_missing_users",
        dict(status="completed", inserted_count=len(inserted)),
    )
    return inserted


def sync(**kwargs):
    """Sync CERN LDAP db with local db."""
    log_uuid = str(uuid.uuid4())
    log_info(log_uuid, "ldap_users_fetch", dict(status="started"))
    start_time = time.time()

    ldap_client = LdapClient(**kwargs.get("ldap", dict()))
    ldap_users = ldap_client.get_primary_accounts()

    log_info(
        log_uuid, "ldap_users_fetch", dict(status="completed", count=len(ldap_users))
    )

    missing_invenio_users, updated_ids = _update_existing(ldap_users, log_uuid)
    inserted_ids = _insert_missing(missing_invenio_users, log_uuid)

    reindex_users.delay(updated_ids + inserted_ids)

    total_time = time.time() - start_time
    log_info(log_uuid, "sync_done", dict(time=total_time))
