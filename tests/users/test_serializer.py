# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Tests users serializers."""

from invenio_cern_sync.users.serializer import serialize_ldap_users


def test_serialize_ldap_users(app, ldap_users):
    """."""
    invenio_users = serialize_ldap_users(ldap_users)
    first_user = next(invenio_users)

    assert first_user["email"] == "ldap.user123456@cern.ch"
    assert first_user["username"] == "newuser1"
    assert first_user["active"]
    assert first_user["user_identity_id"] == "uid123456"
    assert first_user["preferences"]["preferredLanguage"] == "en"

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
