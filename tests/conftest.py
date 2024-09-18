# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration."""

import pytest
from invenio_app.factory import create_app as _create_app
from marshmallow import Schema, fields


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


@pytest.fixture(scope="module")
def client_id(app_config):
    """Return a test client id."""
    return "rdm_prod"


@pytest.fixture(scope="module")
def remote_app_name(app_config):
    """Return a test remote app name."""
    return "cern"


@pytest.fixture(scope="module")
def app_config(app_config, client_id, remote_app_name):
    """Application config override."""
    app_config["CERN_SYNC_REMOTE_APP_NAME"] = remote_app_name
    app_config["CERN_SYNC_KEYCLOAK_CLIENT_ID"] = client_id
    app_config["ACCOUNTS_USER_PROFILE_SCHEMA"] = CustomProfile()
    return app_config


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Application factory fixture."""
    return _create_app


@pytest.fixture()
def cern_identities():
    """Return CERN identities test data."""
    identities = []
    for i in range(10):
        identities.append(
            {
                "upn": f"jdoe{i}",
                "displayName": f"John Doe {i}",
                "firstName": "John",
                "lastName": f"Doe {i}",
                "personId": f"1234{i}",
                "uid": 22222 + i,
                "gid": 1111 + i,
                "cernDepartment": "IT",
                "cernGroup": "CA",
                "cernSection": "IR",
                "instituteName": "CERN",
                "instituteAbbreviation": "CERN",
                "preferredCernLanguage": "EN",
                "orcid": f"0000-0002-2227-122{i}",
                "primaryAccountEmail": f"john.doe{i}@cern.ch",
            }
        )
    return identities


@pytest.fixture()
def ldap_users():
    """Return LDAP test data."""
    users = []
    for i in range(10):
        users.append(
            {
                "cernAccountType": [b"Primary"],
                "cernActiveStatus": [b"Active"],
                "cernGroup": [b"CA"],
                "cernInstituteAbbreviation": [b"CERN"],
                "cernInstituteName": [b"CERN"],
                "cernSection": [b"IR"],
                "cn": [bytes("jdoe" + str(i), encoding="utf-8")],
                "department": [b"IT/CA"],
                "displayName": [bytes("John Doe " + str(i), encoding="utf-8")],
                "division": [b"IT"],
                "employeeID": [bytes("1234" + str(i), encoding="utf-8")],
                "givenName": [b"John"],
                "mail": [bytes("john.doe" + str(i) + "@cern.ch", encoding="utf-8")],
                "postOfficeBox": [bytes("M123ABC" + str(i), encoding="utf-8")],
                "preferredLanguage": [b"EN"],
                "sn": [bytes("Doe " + str(i), encoding="utf-8")],
                "uidNumber": [bytes("22222" + str(i), encoding="utf-8")],
            }
        )
    return users
