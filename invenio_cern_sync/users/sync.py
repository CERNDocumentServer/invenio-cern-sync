# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync users sync API."""

import logging

from invenio_accounts.models import User, UserIdentity
from invenio_db import db

from ..ldap.client import LdapClient
from .api import update_existing_user
from .serializer import serialize_ldap_users

logger = logging.getLogger("sync")


def _update_existing(ldap_users):
    """."""
    missing = []
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
                logger.warning(
                    f"User `{invenio_ldap_user["email"]}` (username `{invenio_ldap_user["username"]}`) has different profile id. Local db: `{user_identity.id}` - LDAP: `{invenio_ldap_user["person_id"]}`"
                )

        if (user and not user_identity) or (user_identity and not user):
            # Something very wrong here, should never happen
            logger.error(
                f"User and user_identity are not correctly linked for user f{user} and user_identity f{user_identity}"
            )
        elif user and user_identity:
            # User found, update info
            update_existing_user(user, user_identity, invenio_ldap_user)
        else:
            # The user does not exist in the DB.
            # The creation of new users is done after all updates completed,
            # to avoid conflicts in case other `person_id` have changed
            missing.append(invenio_ldap_user)

    # persist changes before inserting
    db.session.commit()
    return missing


def sync():
    """."""
    ldap_client = LdapClient()
    ldap_users = ldap_client.get_primary_accounts()

    missing_invenio_users = _update_existing(ldap_users)
    # _insert_missing(missing_invenio_users)
