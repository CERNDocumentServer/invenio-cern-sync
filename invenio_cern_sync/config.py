# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Integrates CERN databases with Invenio."""

from .users.profile import remoteaccount_extradata_mapper, userprofile_mapper

CERN_SYNC_LDAP_URL = None
"""Set the CERN LDAP URL."""

CERN_SYNC_USERPROFILE_MAPPER = userprofile_mapper
"""Map the ldap response to Invenio user profile schema.

The user profile schema is defined via ACCOUNTS_USER_PROFILE_SCHEMA.
"""

CERN_SYNC_USER_EXTRADATA_MAPPER = remoteaccount_extradata_mapper
"""Map the ldap response to the Invenio RemoteAccount `extra_data` db col."""
