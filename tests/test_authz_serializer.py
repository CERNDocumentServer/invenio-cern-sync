# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.
"""Invenio-CERN-sync CERN test serializer."""

from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest

from invenio_cern_sync.authz.serializer import serialize_cern_identities
from invenio_cern_sync.errors import InvalidCERNIdentity


@pytest.mark.parametrize("missing_field", ["personId", "primaryAccountEmail", "upn"])
@patch("invenio_cern_sync.authz.serializer.current_app")
def test_missing_required_fields(mock_app, app, cern_identities, missing_field):
    """Test missing required fields."""
    mock_logger = MagicMock()
    mock_app.logger = mock_logger

    cern_identity = deepcopy(cern_identities[0])
    del cern_identity[missing_field]

    person_id = "12340" if missing_field != "personId" else "unknown"
    excp = InvalidCERNIdentity(missing_field, person_id)

    list(serialize_cern_identities([cern_identity]))
    mock_logger.warning.assert_any_call(f"{str(excp)} Skipping this identity...")


def test_serialize(app, cern_identities):
    serialized_identities = list(serialize_cern_identities(cern_identities))[0:2]
    assert len(serialized_identities) == 2

    for i in range(2):
        assert serialized_identities[i]["email"] == f"john.doe{i}@cern.ch"
        assert serialized_identities[i]["username"] == f"jdoe{i}"
        assert serialized_identities[i]["user_profile"] == {
            "affiliations": "CERN",
            "department": "IT",
            "group": "CA",
            "section": "IR",
            "family_name": f"Doe {i}",
            "full_name": f"John Doe {i}",
            "given_name": "John",
            "mailbox": f"M31120{i}",
            "orcid": f"0000-0002-2227-122{i}",
            "person_id": f"1234{i}",
        }
        assert serialized_identities[i]["preferences"] == {"locale": "en"}
        assert serialized_identities[i]["user_identity_id"] == f"1234{i}"
        assert serialized_identities[i]["remote_account_extra_data"] == {
            "identity_id": f"1234{i}",
            "uidNumber": 22222 + i,
            "username": f"jdoe{i}",
        }


def test_serialize_custom_mapper(app, cern_identities):
    app.config["CERN_SYNC_AUTHZ_USERPROFILE_MAPPER"] = lambda x: {"name": "Test User"}
    app.config["CERN_SYNC_AUTHZ_USER_EXTRADATA_MAPPER"] = lambda x: {"extra": "data"}

    serialized_identities = list(serialize_cern_identities(cern_identities))[0:2]
    assert len(serialized_identities) == 2

    for i in range(2):
        assert serialized_identities[i]["email"] == f"john.doe{i}@cern.ch"
        assert serialized_identities[i]["username"] == f"jdoe{i}"
        assert serialized_identities[i]["user_profile"] == {"name": "Test User"}
        assert serialized_identities[i]["preferences"] == {"locale": "en"}
        assert serialized_identities[i]["user_identity_id"] == f"1234{i}"
        assert serialized_identities[i]["remote_account_extra_data"] == {
            "extra": "data"
        }
