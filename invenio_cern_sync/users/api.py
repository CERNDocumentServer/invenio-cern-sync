# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync users importer API."""

from flask import current_app
from flask_security.confirmable import confirm_user
from invenio_accounts.models import User
from invenio_db import db
from invenio_oauthclient.models import RemoteAccount, UserIdentity


def _create_user(invenio_ldap_user, active=True):
    """Create new user."""
    user = User(
        email=invenio_ldap_user["email"],
        username=invenio_ldap_user["username"],
        active=active,
        user_profile=invenio_ldap_user["user_profile"],
        preferences=invenio_ldap_user["preferences"],
    )
    db.session.add(user)
    # necessary to get the auto-generated `id`
    db.session.commit()
    return user


def _create_user_identity(user, invenio_ldap_user):
    """Create new user identity."""
    remote_app_name = current_app.config["CERN_SYNC_REMOTE_APP_NAME"]
    assert remote_app_name
    return UserIdentity.create(
        user,
        remote_app_name,
        invenio_ldap_user["user_identity_id"],
    )


def _create_remote_account(user, invenio_ldap_user):
    """Return new user entry."""
    client_id = current_app.config["CERN_SYNC_CLIENT_ID"]
    assert client_id
    return RemoteAccount.create(
        client_id=client_id,
        user_id=user.id,
        extra_data=dict(
            keycloak_id=invenio_ldap_user["username"],
            **invenio_ldap_user.get("remote_account_extra_data", {})
        ),
    )


def create_user(invenio_ldap_user, active=True, auto_confirm=True):
    """Create Invenio user.

    :param user: dict. Expected format:
        {
            email: <string>,
            username: <string>,
            user_profile: CERNUserProfileSchema or configured schema,
            user_identity_id: <string>,
            remote_account_extra_data: <dict> (optional)
        }
    :param active: set the user `active`
    :param auto_confirm: set the user `confirmed`
    :return: the newly created Invenio user id.
    """
    user = _create_user(invenio_ldap_user, active=active)
    user_id = user.id

    _create_user_identity(user, invenio_ldap_user)
    _create_remote_account(user, invenio_ldap_user)

    if auto_confirm:
        # Automatically confirm the user
        confirm_user(user)
    return user_id


###################################################################################
# User update


def _update_user(user, invenio_ldap_user):
    """Update User table, when necessary."""
    user_changed = (
        user.email != invenio_ldap_user["email"]
        or user.username != invenio_ldap_user["username"].lower()
        or user.active != invenio_ldap_user["active"]
    )
    if user_changed:
        user.email = invenio_ldap_user["email"]
        user.username = invenio_ldap_user["username"]
        user.active = invenio_ldap_user["active"]

    # check if any key/value in LDAP is different from the local user.user_profile
    local_up = user.user_profile
    ldap_up = invenio_ldap_user["user_profile"]
    up_changed = (
        len([key for key in ldap_up.keys() if local_up.get(key, "") != ldap_up[key]])
        > 0
    )
    if up_changed:
        user.user_profile = {**dict(user.user_profile), **ldap_up}

    # check if any key/value in LDAP is different from the local user.preferences
    local_prefs = user.preferences
    ldap_prefs = invenio_ldap_user["preferences"]
    prefs_changed = (
        len(
            [
                key
                for key in ldap_prefs.keys()
                if local_prefs.get(key, "") != ldap_prefs[key]
            ]
        )
        > 0
    )
    if prefs_changed:
        user.preferences = {**dict(user.preferences), **ldap_prefs}


def _update_useridentity(user_identity, invenio_ldap_user):
    """Update User profile col, when necessary."""
    changed = user_identity.id != invenio_ldap_user["user_identity_id"]
    if changed:
        user_identity.id = invenio_ldap_user["user_identity_id"]


def _update_remote_account(user, invenio_ldap_user):
    """Update RemoteAccount table."""
    client_id = current_app.config["CERN_SYNC_CLIENT_ID"]
    assert client_id
    remote_account = RemoteAccount.get(user.id, client_id)

    new_extra_data = invenio_ldap_user["remote_account_extra_data"]
    if not remote_account:
        RemoteAccount.create(user.id, client_id, new_extra_data)
    else:
        remote_account.extra_data.update(**new_extra_data)


def update_existing_user(local_user, local_user_identity, invenio_ldap_user):
    """Update all user tables, when necessary."""
    _update_user(local_user, invenio_ldap_user)
    _update_useridentity(local_user_identity, invenio_ldap_user)
    _update_remote_account(local_user, invenio_ldap_user)
