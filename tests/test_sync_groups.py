# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Sync groups tests."""

from unittest import mock
from unittest.mock import patch

from invenio_accounts.proxies import current_datastore

from invenio_cern_sync.groups.sync import sync


@patch("invenio_cern_sync.groups.sync.KeycloakService")
@patch("invenio_cern_sync.groups.sync.AuthZService")
def test_sync_groups(
    MockAuthZService,
    MockKeycloakService,
    app,
    authz_groups,
):
    """Test sync with AuthZ."""
    MockAuthZService.return_value.get_groups.return_value = authz_groups

    results = sync()

    for expected_group in list(authz_groups):
        role = current_datastore.find_role_by_id(expected_group["groupIdentifier"])
        assert role.name == expected_group["displayName"]
        assert role.description == expected_group["description"]

    assert len(results) == len(authz_groups)


@patch("invenio_cern_sync.groups.sync.KeycloakService")
@patch("invenio_cern_sync.groups.sync.AuthZService")
def test_sync_groups_update(
    MockAuthZService,
    MockKeycloakService,
    app,
    authz_groups,
):
    """Test sync with AuthZ."""
    # prepare the db with the initial data
    MockAuthZService.return_value.get_groups.return_value = authz_groups
    sync()

    new_group = {
        "groupIdentifier": "cern-primary-accounts",
        "displayName": "CERN Primary Accounts",
        "description": "Group for primary CERN accounts",
    }
    updated_group = {
        "groupIdentifier": "cern-accounts3",
        "displayName": "New display name",
        "description": "New description",
    }

    MockAuthZService.return_value.get_groups.return_value = [new_group, updated_group]
    sync()

    for expected_group in [new_group, updated_group]:
        role = current_datastore.find_role_by_id(expected_group["groupIdentifier"])
        assert role.name == expected_group["displayName"]
        assert role.description == expected_group["description"]
