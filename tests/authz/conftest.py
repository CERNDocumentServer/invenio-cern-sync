# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Pytest conftest."""

import pytest


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
                "primaryAccountEmail": f"john.doe{i}@test.com",
            }
        )
    return identities
