..
    Copyright (C) 2024 CERN.

    Invenio-CERN-sync is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

==============
 Invenio-CERN-sync
==============

Integrates CERN databases with Invenio.

To get the extra user fields stored in the user profile, set the following:

from invenio_cern_sync.users.profile import CERNUserProfileSchema
ACCOUNTS_USER_PROFILE_SCHEMA = CERNUserProfileSchema()

You can also provide your own schema.


Define
- ACCOUNTS_DEFAULT_USER_VISIBILITY
- ACCOUNTS_DEFAULT_EMAIL_VISIBILITY
