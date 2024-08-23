# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync users sync API."""

from invenio_accounts.models import User, UserIdentity
from invenio_db import db

from ..ldap.client import LdapClient
from .serializer import serialize_ldap_users


def _update_existing(ldap_users):
    """."""
    missing = []
    for invenio_user in serialize_ldap_users(ldap_users):
        user = user_identity = None

        user_identity = UserIdentity.query.filter_by(
            id=invenio_user["person_id"]
        ).one_or_none()
        if user_identity:
            user = user_identity.user
        else:
            # user identity not found by `person_id`. Might be a new user, or
            # the person id might have changed (because of a human error)
            # Try to find the user by matching both username and e-mail
            # to make sure that it is the right user.
            user = User.query.filter_by(
                email=invenio_user["email"], username=invenio_user["username"]
            ).one_or_none()
            if user:
                # user found, looks like that the `person_id` was updated!
                user_identity = UserIdentity.query.filter_by(
                    id=invenio_user["person_id"]
                ).first()
                # LOG-ME HERE!!!!!!!!

        if user and user_identity:
            # update_invenio_user(user, user_identity, invenio_user)
            pass
        else:
            # the user does not exist in the DB, create it after all updates,
            # to avoid conflicts in case other `person_id` have been changed
            missing.append(invenio_user)

    # persist changes before inserting
    db.session.commit()
    return missing


def sync():
    """."""
    ldap_client = LdapClient()
    ldap_users = ldap_client.get_primary_accounts()

    missing_invenio_users = _update_existing(ldap_users)
    # _insert_missing(missing_invenio_users)
