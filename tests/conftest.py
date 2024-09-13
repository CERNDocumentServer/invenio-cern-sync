# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration."""

import pytest
from invenio_app.factory import create_app as _create_app


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
    return app_config


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Application factory fixture."""
    return _create_app
