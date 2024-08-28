..
    Copyright (C) 2024 CERN.

    Invenio-CERN-sync is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

# Invenio-CERN-sync

Integrates CERN databases and login with Invenio.

## Users sync

This module connects to LDAP to fetch users, updates already existing users
and inserts missing ones.




To get the extra user fields stored in the user profile, set the following:

from invenio_cern_sync.users.profile import CERNUserProfileSchema
ACCOUNTS_USER_PROFILE_SCHEMA = CERNUserProfileSchema()

You can also provide your own schema.


Define
- ACCOUNTS_DEFAULT_USER_VISIBILITY
- ACCOUNTS_DEFAULT_EMAIL_VISIBILITY
