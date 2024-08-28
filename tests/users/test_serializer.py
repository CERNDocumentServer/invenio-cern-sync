# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Tests users serializers."""

from copy import deepcopy

import pytest

from invenio_cern_sync.users.errors import InvalidLdapUser
from invenio_cern_sync.users.serializer import serialize_ldap_users


def test_serialize_ldap_users(app, ldap_users):
    """Test serialization of existing LDAP user."""
    invenio_users = serialize_ldap_users(ldap_users)
    first_user = next(invenio_users)

    assert first_user["email"] == "ldap.user123456@cern.ch"
    assert first_user["username"] == "newuser1"
    assert first_user["active"]
    assert first_user["user_identity_id"] == "eid123456"
    assert first_user["preferences"]["locale"] == "en"

    profile = first_user["user_profile"]
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

    extra_data = first_user["remote_account_extra_data"]
    assert extra_data["person_id"] == "eid123456"
    assert extra_data["uidNumber"] == "uid123456"
    assert extra_data["username"] == "newuser1"


def test_serialize_alternative_mappers(app, monkeypatch, ldap_users):
    """Test serialization of existing LDAP user."""
    # Temporarily change config variables for custom mappers
    monkeypatch.setitem(
        app.config,
        "CERN_SYNC_USERPROFILE_MAPPER",
        lambda _: dict(fake_key="fake_profile_value"),
    )
    monkeypatch.setitem(
        app.config,
        "CERN_SYNC_USER_EXTRADATA_MAPPER",
        lambda _: dict(fake_key="fake_extra_data_value"),
    )

    invenio_users = serialize_ldap_users(ldap_users)
    first_user = next(invenio_users)

    assert first_user["email"] == "ldap.user123456@cern.ch"
    assert first_user["username"] == "newuser1"
    assert first_user["active"]
    assert first_user["user_identity_id"] == "eid123456"
    assert first_user["preferences"]["locale"] == "en"

    profile = first_user["user_profile"]
    assert len(profile.keys()) == 1
    assert profile["fake_key"] == "fake_profile_value"

    extra_data = first_user["remote_account_extra_data"]
    assert len(extra_data.keys()) == 1
    assert extra_data["fake_key"] == "fake_extra_data_value"


@pytest.mark.parametrize(
    "missing_field",
    [
        "employeeID",
        "mail",
        "cn",
        "uidNumber",
    ],
)
def test_serialize_invalid_ldap_users(app, missing_field):
    """Test serialization of invalid LDAP user."""
    required_fields = {
        "employeeID": [b"eid123456"],
        "mail": [b"ldap.user123456@cern.ch"],
        "cn": [b"newuser1"],
        "uidNumber": [b"uid123456"],
    }
    employeeID = "eid123456" if missing_field != "employeeID" else "unknown"
    error_msg = (
        f"Missing {missing_field} field or invalid value for employeeID {employeeID}"
    )
    # import ipdb;ipdb.set_trace()
    with pytest.raises(InvalidLdapUser, match=error_msg):
        without_missing_field = deepcopy(required_fields)
        del without_missing_field[missing_field]
        next(serialize_ldap_users([without_missing_field]))


def test_serialize_ldap_users_missing_optional_fields(app):
    """Test serialization of LDAP user with missing fields."""
    ldap_users = [
        {
            "employeeID": [b"eid123456"],
            "mail": [b"ldap.user123456@cern.ch"],
            "cn": [b"newuser1"],
            "uidNumber": [b"uid123456"],
        }
    ]

    invenio_users = serialize_ldap_users(ldap_users)
    first_user = next(invenio_users)

    assert first_user["email"] == "ldap.user123456@cern.ch"
    assert first_user["username"] == "newuser1"
    assert first_user["active"]
    assert first_user["user_identity_id"] == "eid123456"
    assert first_user["preferences"]["locale"] == "en"

    profile = first_user["user_profile"]
    assert profile["cern_department"] == ""
    assert profile["family_name"] == ""
    assert profile["full_name"] == ""
    assert profile["given_name"] == ""
    assert profile["cern_group"] == ""
    assert profile["institute_abbreviation"] == ""
    assert profile["institute"] == ""
    assert profile["mailbox"] == ""
    assert profile["person_id"] == "eid123456"
    assert profile["cern_section"] == ""

    extra_data = first_user["remote_account_extra_data"]
    assert extra_data["person_id"] == "eid123456"
    assert extra_data["uidNumber"] == "uid123456"
    assert extra_data["username"] == "newuser1"
