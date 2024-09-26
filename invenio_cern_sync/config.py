# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Integrates CERN databases with Invenio."""

from .authz.mapper import remoteaccount_extradata_mapper as authz_extradata_mapper
from .authz.mapper import userprofile_mapper as authz_userprofile_mapper
from .ldap.mapper import remoteaccount_extradata_mapper as ldap_extradata_mapper
from .ldap.mapper import userprofile_mapper as ldap_userprofile_mapper

###################################################################################
# CERN AuthZ
# Required config when using the AuthZ method to sync users, or when syncing groups

CERN_SYNC_KEYCLOAK_BASE_URL = "https://keycloak-qa.cern.ch/"
"""Base URL of the CERN SSO Keycloak endpoint."""

CERN_SYNC_AUTHZ_BASE_URL = "https://authorization-service-api-qa.web.cern.ch/"
"""Base URL of the Authorization Service API endpoint."""

CERN_SYNC_AUTHZ_USERPROFILE_MAPPER = authz_userprofile_mapper
"""Map the AuthZ response to Invenio user profile schema.

The user profile schema is defined via ACCOUNTS_USER_PROFILE_SCHEMA.
"""

CERN_SYNC_AUTHZ_USER_EXTRADATA_MAPPER = authz_extradata_mapper
"""Map the AuthZ response to the Invenio RemoteAccount `extra_data` db col."""


###################################################################################
# CERN LDAP
# Required config when using the LDAP method to sync users

CERN_SYNC_LDAP_URL = None
"""Set the CERN LDAP full URL."""

CERN_SYNC_LDAP_USERPROFILE_MAPPER = ldap_userprofile_mapper
"""Map the LDAP response to Invenio user profile schema.

The user profile schema is defined via ACCOUNTS_USER_PROFILE_SCHEMA.
"""

CERN_SYNC_LDAP_USER_EXTRADATA_MAPPER = ldap_extradata_mapper
"""Map the LDAP response to the Invenio RemoteAccount `extra_data` db col."""
