# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync test AuthZ client."""

from unittest.mock import MagicMock, patch

import pytest

from invenio_cern_sync.authz.client import AuthZService, KeycloakService


@pytest.fixture
def app_with_extra_config(app):
    """Application with extra configuration."""
    app.config.update(
        {
            "CERN_SYNC_KEYCLOAK_BASE_URL": "https://keycloak.test",
            "CERN_APP_CREDENTIALS": {
                "consumer_key": "test-client-id",
                "consumer_secret": "test-client-secret",
            },
            "CERN_SYNC_AUTHZ_BASE_URL": "https://authz.test",
        }
    )
    yield app


@pytest.fixture
def mock_keycloak_service():
    """Mock Keycloak service."""
    mock_service = MagicMock()
    mock_service.get_authz_token.return_value = "test-token"
    return mock_service


@pytest.fixture
def mock_request_with_retries():
    """Mock request with retries."""
    with patch("invenio_cern_sync.authz.client.request_with_retries") as mock_request:
        yield mock_request


def test_get_authz_token(app_with_extra_config, mock_request_with_retries):
    """Test getting the authorization token."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"access_token": "test-token"}
    mock_request_with_retries.return_value = mock_response

    keycloak_service = KeycloakService()
    token = keycloak_service.get_authz_token()

    assert token == "test-token"
    mock_request_with_retries.assert_called_once_with(
        url="https://keycloak.test/auth/realms/cern/api-access/token",
        method="POST",
        payload={
            "grant_type": "client_credentials",
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "audience": "authorization-service-api",
        },
    )


def test_get_identities(
    app_with_extra_config, mock_keycloak_service, mock_request_with_retries
):
    """Test getting identities from the AuthZ."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": [
            {
                "upn": "jdoe",
                "displayName": "John Doe",
                "firstName": "John",
                "lastName": "Doe",
                "personId": "12345",
                "uid": 22222,
                "gid": 1111,
                "cernDepartment": "IT",
                "cernGroup": "CA",
                "cernSection": "IR",
                "instituteName": "CERN",
                "instituteAbbreviation": "CERN",
                "preferredCernLanguage": "EN",
                "orcid": "0000-0002-2227-1229",
                "primaryAccountEmail": "john.doe@cern.ch",
                "blocked": False,
            }
        ],
        "pagination": {"total": 1},
    }
    mock_request_with_retries.return_value = mock_response

    authz_service = AuthZService(mock_keycloak_service, limit=1)
    identities = list(authz_service.get_identities())
    assert len(identities) == 1
    assert identities[0]["upn"] == "jdoe"
    mock_request_with_retries.assert_called()


def test_get_groups(
    app_with_extra_config, mock_keycloak_service, mock_request_with_retries
):
    """Test getting groups from the AuthZ."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": [
            {
                "groupIdentifier": "authorization-service-administrators",
                "displayName": "AuthZ Administrators",
                "description": "Full control on the AuthZ.",
            }
        ],
        "pagination": {"total": 1},
    }
    mock_request_with_retries.return_value = mock_response

    authz_service = AuthZService(mock_keycloak_service, limit=1)
    groups = list(authz_service.get_groups())

    assert len(groups) == 1
    assert groups[0]["groupIdentifier"] == "authorization-service-administrators"
    mock_request_with_retries.assert_called()


def test_fetch_all_pagination(
    app_with_extra_config,
    cern_identities,
    mock_keycloak_service,
    mock_request_with_retries,
):
    """Test fetching all identities with pagination."""
    mocked_responses = []
    total = 3
    for i in range(total):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [cern_identities[i]],
            "pagination": {"total": total},
        }
        mocked_responses.append(mock_response)

    mock_request_with_retries.side_effect = mocked_responses

    authz_service = AuthZService(mock_keycloak_service, limit=1)
    url = "https://authz.test/api/v1.0/Identity?limit=1&filter=type:Person"
    headers = {"Authorization": "Bearer test-token"}

    results = list(authz_service._fetch_all(url, headers))

    assert len(results) == total
    assert mock_request_with_retries.call_count == 3
    for i in range(len(results)):
        mock_request_with_retries.assert_any_call(
            url=f"https://authz.test/api/v1.0/Identity?limit=1&filter=type:Person&offset={i}",
            method="GET",
            headers=headers,
        )
        # cannot easily test response values with multithreading
        # assert results[i][0]["upn"] == f"jdoe{i}"


def test_get_identities_empty(
    app_with_extra_config, mock_keycloak_service, mock_request_with_retries
):
    """Test getting identities from the AuthZ when there are no identities."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": [],
        "pagination": {"total": 0},
    }
    mock_request_with_retries.return_value = mock_response

    authz_service = AuthZService(mock_keycloak_service, limit=1)
    identities = list(authz_service.get_identities())

    assert len(identities) == 0
    mock_request_with_retries.assert_called()


def test_get_groups_empty(
    app_with_extra_config, mock_keycloak_service, mock_request_with_retries
):
    """Test getting groups from the AuthZ when there are no groups."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": [],
        "pagination": {"total": 0},
    }
    mock_request_with_retries.return_value = mock_response

    authz_service = AuthZService(mock_keycloak_service, limit=1)
    groups = list(authz_service.get_groups())

    assert len(groups) == 0
    mock_request_with_retries.assert_called()
