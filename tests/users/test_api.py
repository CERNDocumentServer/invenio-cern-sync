# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Tests users apis."""

from flask import current_app
from invenio_accounts.models import User, UserIdentity
from invenio_db import db
from invenio_oauthclient.models import RemoteAccount
from marshmallow import Schema, fields
from werkzeug.local import LocalProxy

from invenio_cern_sync.users.api import create_user, update_existing_user
from invenio_cern_sync.users.serializer import serialize_ldap_user

_datastore = LocalProxy(lambda: current_app.extensions["security"].datastore)


class CustomProfile(Schema):
    """A custom user profile schema that matches the default mapper."""

    cern_department = fields.String()
    cern_group = fields.String()
    cern_section = fields.String()
    family_name = fields.String()
    full_name = fields.String()
    given_name = fields.String()
    institute_abbreviation = fields.String()
    institute = fields.String()
    mailbox = fields.String()
    person_id = fields.String()


def _create_user(
    email, username, full_name, user_identity_id, client_id, remote_app_name
):
    """Create user."""
    # pre-create existing user to update
    user = _datastore.create_user(
        email=email,
        username=username,
        password=123456,
    )
    _datastore.commit()
    user.active = False
    user.profile = dict(full_name=full_name)
    user.preferences["locale"] = "en"
    UserIdentity.create(user, remote_app_name, user_identity_id)
    RemoteAccount.create(user.id, client_id, dict(keycloak_id=username))
    db.session.commit()
    return user


def assert_user(db_user, expected_user, client_id, remote_app_name):
    """Assert user data."""
    assert db_user.email == expected_user["email"]
    assert db_user.username == expected_user["username"].lower()
    assert db_user.active == expected_user["active"]

    profile = db_user.user_profile
    assert profile["cern_department"] == "IT"
    assert profile["family_name"] == "User 1"
    assert profile["full_name"] == "New User 1"
    assert profile["given_name"] == "New"
    assert profile["cern_group"] == "ABC"
    assert profile["institute_abbreviation"] == "CERN"
    assert profile["institute"] == "CERN"
    assert profile["mailbox"] == "M123ABC"
    assert profile["person_id"] == "eid123456"
    assert profile["cern_section"] == "DEF"

    prefs = db_user.preferences
    assert prefs["locale"] == "en"
    assert prefs["timezone"]
    assert prefs["visibility"]
    assert prefs["email_visibility"]

    UserIdentity.query.filter(
        UserIdentity.id_user == db_user.id, UserIdentity.method == remote_app_name
    ).count() == 1

    extra_data = RemoteAccount.get(db_user.id, client_id).extra_data
    assert extra_data["keycloak_id"] == expected_user["username"].lower()
    assert extra_data["person_id"] == "eid123456"
    assert extra_data["uidNumber"] == "uid123456"
    assert extra_data["username"] == "newuser1"


def test_update_existing_user(
    app, db, monkeypatch, ldap_users, client_id, remote_app_name
):
    """Test update existing user."""
    invenio_ldap_user = serialize_ldap_user(ldap_users[0])

    # pre-insert user
    monkeypatch.setitem(app.config, "ACCOUNTS_USER_PROFILE_SCHEMA", CustomProfile())
    user = _create_user(
        invenio_ldap_user["email"],
        invenio_ldap_user["username"],
        "John Doe",
        invenio_ldap_user["user_identity_id"],
        client_id,
        remote_app_name,
    )

    ui = UserIdentity.query.filter(
        UserIdentity.id_user == user.id, UserIdentity.method == remote_app_name
    ).first()
    update_existing_user(user, ui, invenio_ldap_user)
    db.session.commit()

    db_user = User.query.filter(User.id == user.id).one()
    assert_user(db_user, invenio_ldap_user, client_id, remote_app_name)


def test_create_new_user(app, db, monkeypatch, ldap_users, client_id, remote_app_name):
    """Test create new user."""
    assert User.query.count() == 0
    monkeypatch.setitem(app.config, "ACCOUNTS_USER_PROFILE_SCHEMA", CustomProfile())

    invenio_ldap_user = serialize_ldap_user(ldap_users[0])
    user_id = create_user(invenio_ldap_user)
    db.session.commit()

    assert User.query.count() == 1
    db_user = User.query.first()
    assert user_id == db_user.id
    assert_user(db_user, invenio_ldap_user, client_id, remote_app_name)
