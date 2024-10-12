# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Sync users tests."""

from unittest import mock
from unittest.mock import patch

from invenio_accounts.models import User
from invenio_oauthclient.models import RemoteAccount, UserIdentity

from invenio_cern_sync.sso import cern_remote_app_name
from invenio_cern_sync.users.sync import sync
from invenio_cern_sync.utils import first_or_default, first_or_raise


def _assert_log_called(mock_log_info):
    """Assert log called."""
    expected_log_uuid = mock_log_info.call_args.kwargs["log_uuid"]

    mock_log_info.assert_any_call(
        "users-sync",
        dict(action="fetching-cern-users", status="started", method=mock.ANY),
        log_uuid=expected_log_uuid,
    )
    mock_log_info.assert_any_call(
        "users-sync",
        dict(action="updating-existing-users", status="started"),
        log_uuid=expected_log_uuid,
    )
    mock_log_info.assert_any_call(
        "users-sync",
        dict(
            action="updating-existing-users", status="completed", updated_count=mock.ANY
        ),
        log_uuid=expected_log_uuid,
    )
    mock_log_info.assert_any_call(
        "users-sync",
        dict(action="inserting-missing-users", status="started"),
        log_uuid=expected_log_uuid,
    )
    mock_log_info.assert_any_call(
        "users-sync",
        dict(
            action="inserting-missing-users",
            status="completed",
            inserted_count=mock.ANY,
        ),
        log_uuid=expected_log_uuid,
    )
    mock_log_info.assert_any_call(
        "users-sync",
        dict(status="completed", time=mock.ANY),
        log_uuid=expected_log_uuid,
    )


def _assert_cern_identity(expected_identity, client_id):
    """Assert CERN identity."""
    user = User.query.filter_by(email=expected_identity["primaryAccountEmail"]).one()
    user_identity = UserIdentity.query.filter_by(id=expected_identity["personId"]).one()
    remote_account = RemoteAccount.get(user.id, client_id)
    # assert user data
    assert user.username == expected_identity["upn"]
    assert user.email == expected_identity["primaryAccountEmail"]
    profile = user.user_profile
    assert profile["affiliations"] == expected_identity["instituteName"]
    assert profile["department"] == expected_identity["cernDepartment"]
    assert profile["group"] == expected_identity["cernGroup"]
    assert profile["section"] == expected_identity["cernSection"]
    assert profile["family_name"] == expected_identity["lastName"]
    assert profile["full_name"] == expected_identity["displayName"]
    assert profile["given_name"] == expected_identity["firstName"]
    assert profile["mailbox"] == expected_identity.get("postOfficeBox", "")
    assert profile["person_id"] == expected_identity["personId"]
    preferences = user.preferences
    assert preferences["locale"] == expected_identity["preferredCernLanguage"].lower()
    # assert user identity data
    assert user_identity.id_user == user.id
    assert user_identity.method == cern_remote_app_name
    # assert remote account data
    assert remote_account.extra_data["identity_id"] == expected_identity["personId"]
    assert remote_account.extra_data["uidNumber"] == expected_identity["uid"]
    assert remote_account.extra_data["username"] == expected_identity["upn"]


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
    client_id = app.config["CERN_APP_CREDENTIALS"]["consumer_key"]

    results = sync(method="AuthZ")

    for expected_identity in list(cern_identities):
        _assert_cern_identity(expected_identity, client_id)

    assert len(results) == len(cern_identities)
    _assert_log_called(mock_log_info)


@patch("invenio_cern_sync.users.sync.LdapClient")
@patch("invenio_cern_sync.users.sync.log_info")
def test_sync_ldap(mock_log_info, MockLdapClient, app, ldap_users):
    """Test sync with LDAP."""
    MockLdapClient.return_value.get_primary_accounts.return_value = ldap_users
    client_id = app.config["CERN_APP_CREDENTIALS"]["consumer_key"]

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
        profile = user.user_profile
        assert profile["affiliations"] == first_or_default(
            ldap_user, "cernInstituteName"
        )
        assert profile["department"] == first_or_default(ldap_user, "division")
        assert profile["group"] == first_or_default(ldap_user, "cernGroup")
        assert profile["section"] == first_or_default(ldap_user, "cernSection")
        assert profile["family_name"] == first_or_default(ldap_user, "sn")
        assert profile["full_name"] == first_or_default(ldap_user, "displayName")
        assert profile["given_name"] == first_or_default(ldap_user, "givenName")
        assert profile["mailbox"] == first_or_default(ldap_user, "postOfficeBox")
        assert profile["person_id"] == person_id
        preferences = user.preferences
        assert (
            preferences["locale"]
            == first_or_default(ldap_user, "preferredLanguage", "en").lower()
        )
        # assert user identity data
        assert user_identity.id_user == user.id
        assert user_identity.method == cern_remote_app_name
        # assert remote account data
        assert remote_account.extra_data["identity_id"] == first_or_raise(
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


@patch("invenio_cern_sync.users.sync.KeycloakService")
@patch("invenio_cern_sync.users.sync.AuthZService")
def test_sync_update_insert(
    MockAuthZService,
    MockKeycloakService,
    app,
    cern_identities,
):
    """Test sync personId change."""
    # prepare the db with the initial data
    client_id = app.config["CERN_APP_CREDENTIALS"]["consumer_key"]

    MockAuthZService.return_value.get_identities.return_value = cern_identities
    sync(method="AuthZ")

    # prepare update
    first = cern_identities[0]
    first["firstName"] = "Mario"
    first["lastName"] = "Rossi"
    first["displayName"] = "Mario Rossi"
    first["cernDepartment"] = "EN"
    first["cernGroup"] = "AA"
    first["cernSection"] = "BB"
    first["orcid"] = "0000-0002-2227-122999"

    # prepare insert
    new_user = {
        "upn": f"fbar",
        "displayName": f"Foo Bar",
        "firstName": "Foo",
        "lastName": f"Bar",
        "personId": f"076512",
        "uid": 39587,
        "gid": 494853,
        "cernDepartment": "LL",
        "cernGroup": "TT",
        "cernSection": "EE",
        "instituteName": "CERN",
        "postOfficeBox": "M31120",
        "instituteAbbreviation": "CERN",
        "preferredCernLanguage": "EN",
        "orcid": f"0000-0002-2227-8888",
        "primaryAccountEmail": f"foo.bar@cern.ch",
    }

    MockAuthZService.return_value.get_identities.return_value = [first, new_user]
    sync(method="AuthZ")

    for expected_identity in [first, new_user]:
        _assert_cern_identity(expected_identity, client_id)


@patch("invenio_cern_sync.users.sync.KeycloakService")
@patch("invenio_cern_sync.users.sync.AuthZService")
@patch("invenio_cern_sync.users.sync.log_warning")
def test_sync_person_id_change(
    mock_log_warning,
    MockAuthZService,
    MockKeycloakService,
    app,
    cern_identities,
):
    """Test sync personId change."""
    # prepare the db with the initial data
    client_id = app.config["CERN_APP_CREDENTIALS"]["consumer_key"]

    MockAuthZService.return_value.get_identities.return_value = cern_identities
    sync(method="AuthZ")

    # change the personId of the first user
    first = cern_identities[0]
    previous_person_id = first["personId"]
    first["personId"] = "99999"
    MockAuthZService.return_value.get_identities.return_value = [first]
    sync(method="AuthZ")

    # check that the user identity was updated, but the user was not duplicated
    assert UserIdentity.query.filter_by(id=previous_person_id).one_or_none() is None
    user = User.query.filter_by(email=first["primaryAccountEmail"]).one()
    assert user.username == first["upn"]
    user_identity = UserIdentity.query.filter_by(id_user=user.id).one()
    assert user_identity.id == first["personId"]
    remote_account = RemoteAccount.get(user.id, client_id)
    ra_change = remote_account.extra_data["changes"][0]
    assert ra_change["action"] == "identityId_changed"
    assert ra_change["previous_identity_id"] == previous_person_id
    assert ra_change["new_identity_id"] == first["personId"]

    expected_log_msg = f"Identity Id changed for User `{user.username}` `{user.email}`. Previous UserIdentity.id in the local DB: `{previous_person_id}` - New Identity Id from CERN DB: `{first['personId']}`."
    mock_log_warning.assert_any_call(
        "users-sync",
        dict(action="updating-existing-users", msg=expected_log_msg),
        log_uuid=mock.ANY,
    ),


@patch("invenio_cern_sync.users.sync.KeycloakService")
@patch("invenio_cern_sync.users.sync.AuthZService")
@patch("invenio_cern_sync.users.sync.log_warning")
def test_sync_username_email_change(
    mock_log_warning,
    MockAuthZService,
    MockKeycloakService,
    app,
    cern_identities,
):
    """Test sync username/email change."""
    # prepare the db with the initial data
    client_id = app.config["CERN_APP_CREDENTIALS"]["consumer_key"]

    MockAuthZService.return_value.get_identities.return_value = cern_identities
    sync(method="AuthZ")

    # change the email/username of the first user
    first = cern_identities[0]
    previous_username = first["upn"]
    previous_email = first["primaryAccountEmail"]
    first["upn"] = "mrossi"
    first["primaryAccountEmail"] = "mrossi@cern.ch"
    MockAuthZService.return_value.get_identities.return_value = [first]
    sync(method="AuthZ")

    # check that the user identity was updated, but the user was not duplicated
    assert User.query.filter_by(username=previous_username).one_or_none() is None
    assert User.query.filter_by(email=previous_email).one_or_none() is None
    user_identity = UserIdentity.query.filter_by(id=first["personId"]).one()
    user = user_identity.user
    assert user.username == first["upn"]
    assert user.email == first["primaryAccountEmail"]
    remote_account = RemoteAccount.get(user.id, client_id)
    ra_change = remote_account.extra_data["changes"][0]
    assert ra_change["action"] == "userdata_changed"
    assert ra_change["previous_username"] == previous_username
    assert ra_change["previous_email"] == previous_email
    assert ra_change["new_username"] == first["upn"]
    assert ra_change["new_email"] == first["primaryAccountEmail"]

    expected_log_msg = f"Username/e-mail changed for UserIdentity.id #{first['personId']}. Local DB username/e-mail: `{previous_username}` `{previous_email}`. New from CERN DB: `{first['upn']}` `{first['primaryAccountEmail']}`."
    mock_log_warning.assert_any_call(
        "users-sync",
        dict(action="updating-existing-users", msg=expected_log_msg),
        log_uuid=mock.ANY,
    ),
