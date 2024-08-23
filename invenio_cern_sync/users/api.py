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


class InvenioUserCreator:
    """Create an Invenio user."""

    def __init__(self, app_client_id, remote_app_name):
        """Constructor."""
        self._app_client_id = app_client_id
        self._remote_app_name = (
            remote_app_name or current_app.config["OAUTH_REMOTE_APP_NAME"]
        )

    def _create_user(self, user, active=True):
        """Create new user."""
        user = User(
            email=user["email"],
            username=user["username"],
            active=active,
            user_profile=user["user_profile"],
        )
        db.session.add(user)
        # necessary to get the auto-generated `id`
        db.session.commit()
        return user

    def _create_user_identity(self, user_id, user):
        """Create new user identity."""
        return UserIdentity(
            id=user["user_identity_id"],
            method=self._remote_app_name,
            id_user=user_id,
        )

    def _create_remote_account(self, user_id, user):
        """Return new user entry."""
        return RemoteAccount.create(
            client_id=self._app_client_id,
            user_id=user_id,
            extra_data=dict(
                keycloak_id=user["username"],
                **user.get("remote_account_extra_data", {})
            ),
        )

    def create(self, user, active=True, auto_confirm=True):
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
        user = self._create_user(user, active=active)
        user_id = user.id

        identity = self._create_user_identity(user_id, user)
        db.session.add(identity)

        remote_account = self._create_remote_account(user_id, user)
        db.session.add(remote_account)

        if auto_confirm:
            # Automatically confirm the user
            confirm_user(user)
        return user_id


class InvenioUserUpdater:
    """Create an Invenio user."""

    def _update_useridentity(self, user_identity, invenio_user):
        """Update User profile col, when necessary."""
        changed = user_identity.id != invenio_user["user_identity_id"]
        if changed:
            user_identity.id = invenio_user["user_identity_id"]

    def _update_user(self, user, invenio_user):
        """Update User table, when necessary."""
        changed = (
            user.email != invenio_user["email"]
            or user.username != invenio_user["username"].lower()
            or user.displayname != invenio_user["username"]
            or user.active != invenio_user["active"]
        )  # or \

        # changes = dictdiffer.diff(old_mapping, mapping)

        # user.user_profile..... fix me or \
        # user.preferences["locale"] != invenio_user["userpreferences"]["locale"]

        if changed:
            user.email = invenio_user["email"]
            user.username = invenio_user["username"].lower()
            user.displayname = invenio_user["displayname"]
            user.active = invenio_user["active"]
            # PROFILE FIX ME
            # user.preferences["locale"] = invenio_user["userpreferences"]["locale"]

    def update(self, user, user_identity, invenio_user):
        """Update all user tables, when necessary, to avoid updating `updated` date."""
        self._update_user(user, invenio_user)
        self._update_useridentity(user_identity, invenio_user)
        self._update

        ra = self.remote_account
        ra.extra_data["keycloak_id"] = ldap_user["user_username"]
        ra.extra_data["department"] = ldap_user["remote_account_department"]

        self.user_profile.full_name = ldap_user["user_profile_full_name"]
