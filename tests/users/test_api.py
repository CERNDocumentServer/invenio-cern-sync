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

from invenio_cern_sync.users.api import update_existing_user
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


def test_update_existing_user_by_person_id(app, monkeypatch, ldap_users):
    """."""
    invenio_ldap_user = serialize_ldap_user(ldap_users[0])

    # prepare config
    monkeypatch.setitem(app.config, "ACCOUNTS_USER_PROFILE_SCHEMA", CustomProfile())
    client_id = "rdm_prod"
    remote_app_name = "cern"
    monkeypatch.setitem(app.config, "CERN_SYNC_CLIENT_ID", client_id)

    # pre-create existing user to update
    user = _datastore.create_user(
        email=invenio_ldap_user["email"],
        username=invenio_ldap_user["username"],
        password=123456,
    )
    _datastore.commit()
    user.active = False
    user.profile = dict(full_name="John Doe")
    user.preferences["locale"] = "en"
    UserIdentity.create(user, remote_app_name, invenio_ldap_user["user_identity_id"])
    RemoteAccount.create(
        user.id, client_id, dict(keycloak_id=invenio_ldap_user["username"])
    )
    db.session.commit()

    ui = UserIdentity.query.filter(
        UserIdentity.id_user == user.id, UserIdentity.method == remote_app_name
    ).one()
    update_existing_user(user, ui, invenio_ldap_user)
    db.session.commit()

    user = User.query.filter(User.id == user.id).one()

    assert user.email == invenio_ldap_user["email"]
    assert user.username == invenio_ldap_user["username"].lower()
    assert user.active == invenio_ldap_user["active"]

    profile = user.user_profile
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

    prefs = user.preferences
    assert prefs["locale"] == "en"
    assert prefs["timezone"]
    assert prefs["visibility"]
    assert prefs["email_visibility"]

    extra_data = RemoteAccount.get(user.id, client_id).extra_data
    assert extra_data["keycloak_id"] == invenio_ldap_user["username"].lower()
    assert extra_data["person_id"] == "eid123456"
    assert extra_data["uidNumber"] == "uid123456"
    assert extra_data["username"] == "newuser1"
