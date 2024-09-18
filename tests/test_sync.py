# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Sync tests."""

from unittest import mock
from unittest.mock import patch

from invenio_accounts.models import User
from invenio_oauthclient.models import RemoteAccount, UserIdentity

from invenio_cern_sync.users.sync import sync
from invenio_cern_sync.utils import first_or_default, first_or_raise


def _assert_log_called(mock_log_info):
    """Assert log called."""
    expected_log_uuid = mock_log_info.call_args.args[0]

    mock_log_info.assert_any_call(
        expected_log_uuid,
        "users_sync",
        dict(status="fetching-cern-users", method=mock.ANY),
    ),
    mock_log_info.assert_any_call(
        expected_log_uuid, "updating_existing_users", dict(status="started")
    ),
    mock_log_info.assert_any_call(
        expected_log_uuid,
        "updating_existing_users",
        dict(status="completed", updated_count=mock.ANY),
    ),
    mock_log_info.assert_any_call(
        expected_log_uuid, "inserting_missing_users", dict(status="started")
    ),
    mock_log_info.assert_any_call(
        expected_log_uuid,
        "inserting_missing_users",
        dict(status="completed", inserted_count=mock.ANY),
    ),
    mock_log_info.assert_any_call(
        expected_log_uuid, "users_sync", dict(status="completed", time=mock.ANY)
    )


@patch("invenio_cern_sync.users.sync.KeycloakService")
@patch("invenio_cern_sync.users.sync.AuthZService")
@patch("invenio_cern_sync.users.sync.log_info")
def test_sync_authz(
    mock_log_info,
    MockAuthZService,
    MockKeycloakService,
    app,
    cern_identities,
):
    """Test sync with AuthZ."""
    MockAuthZService.return_value.get_identities.return_value = cern_identities
    client_id = app.config["CERN_SYNC_KEYCLOAK_CLIENT_ID"]
    remote_app_name = app.config["CERN_SYNC_REMOTE_APP_NAME"]

    results = sync(method="AuthZ")

    for cern_identity in list(cern_identities):
        user = User.query.filter_by(email=cern_identity["primaryAccountEmail"]).one()
        user_identity = UserIdentity.query.filter_by(id=cern_identity["personId"]).one()
        remote_account = RemoteAccount.get(user.id, client_id)
        # assert user data
        assert user.username == cern_identity["upn"]
        assert user.email == cern_identity["primaryAccountEmail"]
        profile = user.user_profile
        assert profile["cern_department"] == cern_identity["cernDepartment"]
        assert profile["cern_group"] == cern_identity["cernGroup"]
        assert profile["cern_section"] == cern_identity["cernSection"]
        assert profile["family_name"] == cern_identity["lastName"]
        assert profile["full_name"] == cern_identity["displayName"]
        assert profile["given_name"] == cern_identity["firstName"]
        assert (
            profile["institute_abbreviation"] == cern_identity["instituteAbbreviation"]
        )
        assert profile["institute"] == cern_identity["instituteName"]
        assert profile["mailbox"] == cern_identity.get("postOfficeBox", "")
        assert profile["person_id"] == cern_identity["personId"]
        preferences = user.preferences
        assert preferences["locale"] == cern_identity["preferredCernLanguage"].lower()
        # assert user identity data
        assert user_identity.id_user == user.id
        assert user_identity.method == remote_app_name
        # assert remote account data
        assert remote_account.extra_data["person_id"] == cern_identity["personId"]
        assert remote_account.extra_data["uidNumber"] == cern_identity["uid"]
        assert remote_account.extra_data["username"] == cern_identity["upn"]

    assert len(results) == len(cern_identities)
    _assert_log_called(mock_log_info)


@patch("invenio_cern_sync.users.sync.LdapClient")
@patch("invenio_cern_sync.users.sync.log_info")
def test_sync_ldap(mock_log_info, MockLdapClient, app, ldap_users):
    """Test sync with LDAP."""
    MockLdapClient.return_value.get_primary_accounts.return_value = ldap_users
    client_id = app.config["CERN_SYNC_KEYCLOAK_CLIENT_ID"]
    remote_app_name = app.config["CERN_SYNC_REMOTE_APP_NAME"]

    results = sync(method="LDAP")

    for ldap_user in ldap_users:
        person_id = first_or_default(ldap_user, "employeeID")
        email = first_or_raise(ldap_user, "mail")
        user = User.query.filter_by(email=email).one()
        user_identity = UserIdentity.query.filter_by(id=person_id).one()
        remote_account = RemoteAccount.get(user.id, client_id)
        # assert user data
        assert user.username == first_or_raise(ldap_user, "cn").lower()
        assert user.email == email.lower()
        assert user.active
        profile = user.user_profile
        assert profile["cern_department"] == first_or_default(ldap_user, "division")
        assert profile["cern_group"] == first_or_default(ldap_user, "cernGroup")
        assert profile["cern_section"] == first_or_default(ldap_user, "cernSection")
        assert profile["family_name"] == first_or_default(ldap_user, "sn")
        assert profile["full_name"] == first_or_default(ldap_user, "displayName")
        assert profile["given_name"] == first_or_default(ldap_user, "givenName")
        assert profile["institute_abbreviation"] == first_or_default(
            ldap_user, "cernInstituteAbbreviation"
        )
        assert profile["institute"] == first_or_default(ldap_user, "cernInstituteName")
        assert profile["mailbox"] == first_or_default(ldap_user, "postOfficeBox")
        assert profile["person_id"] == person_id
        preferences = user.preferences
        assert (
            preferences["locale"]
            == first_or_default(ldap_user, "preferredLanguage", "en").lower()
        )
        # assert user identity data
        assert user_identity.id_user == user.id
        assert user_identity.method == remote_app_name
        # assert remote account data
        assert remote_account.extra_data["person_id"] == first_or_raise(
            ldap_user, "employeeID"
        )
        assert remote_account.extra_data["uidNumber"] == first_or_raise(
            ldap_user, "uidNumber"
        )
        assert (
            remote_account.extra_data["username"]
            == first_or_raise(ldap_user, "cn").lower()
        )

    assert len(results) == len(ldap_users)
    _assert_log_called(mock_log_info)
