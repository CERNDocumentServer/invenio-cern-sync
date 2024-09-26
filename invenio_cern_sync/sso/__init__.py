# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync SSO module."""

###################################################################################
# CERN SSO
# Pre-configured settings for CERN SSO

import os
from urllib.parse import quote

from invenio_oauthclient.contrib.keycloak import KeycloakSettingsHelper

from .api import (
    cern_groups_handler,
    cern_groups_serializer,
    cern_info_handler,
    cern_info_serializer,
    cern_setup_handler,
)

_base_url = os.environ.get(
    "INVENIO_CERN_SYNC_KEYCLOAK_BASE_URL", "https://keycloak-qa.cern.ch/"
)
_site_ui_url = os.environ.get("INVENIO_SITE_UI_URL", "https://127.0.0.1")

cern_remote_app_name = "cern"  # corresponds to the UserIdentity `method` column

cern_keycloak = KeycloakSettingsHelper(
    title="CERN",
    description="CERN SSO authentication",
    base_url=_base_url,
    realm="cern",
    app_key="CERN_APP_CREDENTIALS",  # config key for the app credentials
    logout_url="{}auth/realms/cern/protocol/openid-connect/logout?redirect_uri={}".format(
        _base_url, quote(_site_ui_url)
    ),
)

handlers = cern_keycloak.get_handlers()
handlers["signup_handler"] = {
    **handlers["signup_handler"],
    "info": cern_info_handler,
    "info_serializer": cern_info_serializer,
    "groups_serializer": cern_groups_serializer,
    "groups": cern_groups_handler,
    "setup": cern_setup_handler,
}
rest_handlers = cern_keycloak.get_rest_handlers()
rest_handlers["signup_handler"] = {
    **rest_handlers["signup_handler"],
    "info": cern_info_handler,
    "info_serializer": cern_info_serializer,
    "groups_serializer": cern_groups_serializer,
    "groups": cern_groups_handler,
    "setup": cern_setup_handler,
}
