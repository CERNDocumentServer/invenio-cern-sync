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
# Required config

CERN_SYNC_KEYCLOAK_CLIENT_ID = ""
"""Set the unique id/name of the CERN SSO app, also called `consumer_key`.

This corresponds to the RemoteAccount `client_id` column.
"""

CERN_SYNC_REMOTE_APP_NAME = None
"""Set the configured remote (oauth) app name for the CERN login.

This corresponds to the UserIdentity `method` column.
"""

###################################################################################
# Required config when using the AuthZ method to sync users, or when syncing groups

CERN_SYNC_KEYCLOAK_BASE_URL = ""
"""."""

CERN_SYNC_KEYCLOAK_CLIENT_SECRET = ""
"""."""

CERN_SYNC_AUTHZ_BASE_URL = ""
"""."""

CERN_SYNC_AUTHZ_USERPROFILE_MAPPER = authz_userprofile_mapper
"""Map the AuthZ response to Invenio user profile schema.

The user profile schema is defined via ACCOUNTS_USER_PROFILE_SCHEMA.
"""

CERN_SYNC_AUTHZ_USER_EXTRADATA_MAPPER = authz_extradata_mapper
"""Map the AuthZ response to the Invenio RemoteAccount `extra_data` db col."""


###################################################################################
# Required config when using the LDAP method to sync users

CERN_SYNC_LDAP_URL = None
"""Set the CERN LDAP full URL."""

CERN_SYNC_LDAP_USERPROFILE_MAPPER = ldap_userprofile_mapper
"""Map the LDAP response to Invenio user profile schema.

The user profile schema is defined via ACCOUNTS_USER_PROFILE_SCHEMA.
"""

CERN_SYNC_LDAP_USER_EXTRADATA_MAPPER = ldap_extradata_mapper
"""Map the LDAP response to the Invenio RemoteAccount `extra_data` db col."""
