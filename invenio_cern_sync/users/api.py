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

from invenio_cern_sync.utils import _is_different


def _create_user(cern_user, active=True):
    """Create new user."""
    user = User(
        email=cern_user["email"],
        username=cern_user["username"],
        active=active,
        user_profile=cern_user["user_profile"],
        preferences=cern_user["preferences"],
    )
    db.session.add(user)
    # necessary to get the auto-generated `id`
    db.session.commit()
    return user


def _create_user_identity(user, cern_user):
    """Create new user identity."""
    remote_app_name = current_app.config["CERN_SYNC_REMOTE_APP_NAME"]
    assert remote_app_name
    return UserIdentity.create(
        user,
        remote_app_name,
        cern_user["user_identity_id"],
    )


def _create_remote_account(user, cern_user):
    """Return new user entry."""
    client_id = current_app.config["CERN_SYNC_KEYCLOAK_CLIENT_ID"]
    assert client_id
    return RemoteAccount.create(
        client_id=client_id,
        user_id=user.id,
        extra_data=dict(
            keycloak_id=cern_user["username"],
            **cern_user.get("remote_account_extra_data", {})
        ),
    )


def create_user(cern_user, active=True, auto_confirm=True):
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
    user = _create_user(cern_user, active=active)
    user_id = user.id

    _create_user_identity(user, cern_user)
    _create_remote_account(user, cern_user)

    if auto_confirm:
        # Automatically confirm the user
        confirm_user(user)
    return user_id


###################################################################################
# User update


def _update_user(user, cern_user):
    """Update User table, when necessary."""
    user_changed = (
        user.email != cern_user["email"]
        or user.username != cern_user["username"].lower()
        or user.active != cern_user["active"]
    )
    if user_changed:
        user.email = cern_user["email"]
        user.username = cern_user["username"]
        user.active = cern_user["active"]

    # check if any key/value in CERN is different from the local user.user_profile
    local_up = user.user_profile
    cern_up = cern_user["user_profile"]
    up_changed = _is_different(cern_up, local_up)
    if up_changed:
        user.user_profile = {**dict(user.user_profile), **cern_up}

    # check if any key/value in CERN is different from the local user.preferences
    local_prefs = user.preferences
    cern_prefs = cern_user["preferences"]
    prefs_changed = (
        len(
            [
                key
                for key in cern_prefs.keys()
                if local_prefs.get(key, "") != cern_prefs[key]
            ]
        )
        > 0
    )
    if prefs_changed:
        user.preferences = {**dict(user.preferences), **cern_prefs}


def _update_useridentity(user_id, user_identity, cern_user):
    """Update User profile col, when necessary."""
    changed = (
        user_identity.id != cern_user["user_identity_id"]
        or user_identity.id_user != user_id
    )
    if changed:
        user_identity.id = cern_user["user_identity_id"]
        user_identity.id_user = user_id


def _update_remote_account(user, cern_user):
    """Update RemoteAccount table."""
    extra_data = cern_user["remote_account_extra_data"]
    client_id = current_app.config["CERN_SYNC_KEYCLOAK_CLIENT_ID"]
    assert client_id
    remote_account = RemoteAccount.get(user.id, client_id)

    if not remote_account:
        # should probably never happen
        RemoteAccount.create(user.id, client_id, extra_data)
    elif _is_different(remote_account.extra_data, extra_data):
        remote_account.extra_data.update(**extra_data)


def update_existing_user(local_user, local_user_identity, cern_user):
    """Update all user tables, when necessary."""
    _update_user(local_user, cern_user)
    _update_useridentity(local_user.id, local_user_identity, cern_user)
    _update_remote_account(local_user, cern_user)
