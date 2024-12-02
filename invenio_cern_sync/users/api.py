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

from invenio_cern_sync.sso import cern_remote_app_name
from invenio_cern_sync.utils import is_different


def _create_user(cern_user):
    """Create new user."""
    user = User(
        email=cern_user["email"],
        username=cern_user["username"],
        active=True,
        user_profile=cern_user["user_profile"],
        preferences=cern_user["preferences"],
    )
    db.session.add(user)
    # necessary to get the auto-generated `id`
    db.session.flush()
    return user


def _create_user_identity(user, cern_user):
    """Create new user identity."""
    assert cern_remote_app_name
    return UserIdentity.create(
        user,
        cern_remote_app_name,
        cern_user["user_identity_id"],
    )


def _create_remote_account(user, cern_user):
    """Return new user entry."""
    client_id = current_app.config["CERN_APP_CREDENTIALS"]["consumer_key"]
    assert client_id
    return RemoteAccount.create(
        client_id=client_id,
        user_id=user.id,
        extra_data=dict(
            keycloak_id=cern_user["username"],
            **cern_user.get("remote_account_extra_data", {})
        ),
    )


def create_user(cern_user, auto_confirm=True):
    """Create Invenio user.

    :param user: dict. Expected format:
        {
            email: <string>,
            username: <string>,
            user_profile: CERNUserProfileSchema or configured schema,
            user_identity_id: <string>,
            remote_account_extra_data: <dict> (optional)
        }
    :param auto_confirm: set the user `confirmed`
    :return: the newly created Invenio user id.
    """
    user = _create_user(cern_user)
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
    user_updated = (
        user.email != cern_user["email"]
        or user.username != cern_user["username"].lower()
    )
    if user_updated:
        user.email = cern_user["email"]
        user.username = cern_user["username"]

    # check if any key/value in CERN is different from the local user.user_profile
    local_up = user.user_profile
    cern_up = cern_user["user_profile"]
    up_updated = is_different(cern_up, local_up)
    if up_updated:
        user.user_profile = {**dict(user.user_profile), **cern_up}

    # check if any key/value in CERN is different from the local user.preferences
    local_prefs = user.preferences
    cern_prefs = cern_user["preferences"]
    prefs_updated = (
        len(
            [
                key
                for key in cern_prefs.keys()
                if local_prefs.get(key, "") != cern_prefs[key]
            ]
        )
        > 0
    )
    if prefs_updated:
        user.preferences = {**dict(user.preferences), **cern_prefs}

    return user_updated or up_updated or prefs_updated


def _update_useridentity(user_id, user_identity, cern_user):
    """Update User profile col, when necessary."""
    updated = (
        user_identity.id != cern_user["user_identity_id"]
        or user_identity.id_user != user_id
    )
    if updated:
        user_identity.id = cern_user["user_identity_id"]
        user_identity.id_user = user_id

    return updated


def _update_remote_account(user, cern_user):
    """Update RemoteAccount table."""
    updated = False
    extra_data = cern_user["remote_account_extra_data"]
    client_id = current_app.config["CERN_APP_CREDENTIALS"]["consumer_key"]
    assert client_id
    remote_account = RemoteAccount.get(user.id, client_id)

    if not remote_account:
        # should probably never happen
        RemoteAccount.create(user.id, client_id, extra_data)
        updated = True
    elif is_different(extra_data, remote_account.extra_data):
        remote_account.extra_data.update(**extra_data)
        updated = True

    return updated


def update_existing_user(local_user, local_user_identity, cern_user):
    """Update all user tables, when necessary."""
    user_updated = _update_user(local_user, cern_user)
    identity_updated = _update_useridentity(
        local_user.id, local_user_identity, cern_user
    )
    remote_updated = _update_remote_account(local_user, cern_user)
    return user_updated or identity_updated or remote_updated
