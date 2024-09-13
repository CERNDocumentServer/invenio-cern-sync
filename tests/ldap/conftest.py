# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest conftest."""

import pytest


@pytest.fixture(scope="module")
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
                "mail": [bytes("john.doe" + str(i) + "@test.com", encoding="utf-8")],
                "postOfficeBox": [bytes("M123ABC" + str(i), encoding="utf-8")],
                "preferredLanguage": [b"EN"],
                "sn": [bytes("Doe " + str(i), encoding="utf-8")],
                "uidNumber": [bytes("22222" + str(i), encoding="utf-8")],
            }
        )
    return users
