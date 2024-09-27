..
    Copyright (C) 2024 CERN.

    Invenio-CERN-sync is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

# Invenio-CERN-sync

Integrates CERN databases and SSO login with Invenio.

## SSO login

This module provides configurable integration with the CERN SSO login.

To integrate the CERN SSO, add this to your application configuration:

```python
from invenio_cern_sync.sso import cern_remote_app_name, cern_keycloak
OAUTHCLIENT_REMOTE_APPS = {
    cern_remote_app_name: cern_keycloak.remote_app,
}

CERN_APP_CREDENTIALS = {
    "consumer_key": "CHANGE ME",
    "consumer_secret": "CHANGE ME",
}

from invenio_cern_sync.sso.api import confirm_registration_form
OAUTHCLIENT_SIGNUP_FORM = confirm_registration_form

OAUTHCLIENT_CERN_REALM_URL = cern_keycloak.realm_url
OAUTHCLIENT_CERN_USER_INFO_URL = cern_keycloak.user_info_url
OAUTHCLIENT_CERN_VERIFY_EXP = True
OAUTHCLIENT_CERN_VERIFY_AUD = False
OAUTHCLIENT_CERN_USER_INFO_FROM_ENDPOINT = True
```

Define, use the env var to inject the right configuration
for your env (local, prod, etc.):

- INVENIO_CERN_SYNC_KEYCLOAK_BASE_URL
- INVENIO_SITE_UI_URL


## Sync users and groups

You can sync users and groups from the CERN AuthZ service or LDAP
with the local Invenio db.

First, decide what fields you would like to get from the CERN database.
By default, only the field in `invenio_cern_sync.users.profile.CERNUserProfileSchema`
are kept when syncing.

If you need to customize that, you will need to:

1. Provide your own schema class, and assign it the config var `ACCOUNTS_USER_PROFILE_SCHEMA`
2. Change the mappers, to serialize the fetched users from the CERN format to your
   local format. If you are using AuthZ, assign your custom serializer func
   to `CERN_SYNC_AUTHZ_USERPROFILE_MAPPER`.
   If you are using LDAP, assign it to `CERN_SYNC_LDAP_USERPROFILE_MAPPER`.
3. You can also customize what extra data can be stored in the RemoteAccount.extra_data fields
   via the config `CERN_SYNC_AUTHZ_USER_EXTRADATA_MAPPER` or `CERN_SYNC_LDAP_USER_EXTRADATA_MAPPER`.

If are only using the CERN SSO as unique login method, you will probably also configure:

```python
ACCOUNTS_DEFAULT_USER_VISIBILITY = True
ACCOUNTS_DEFAULT_EMAIL_VISIBILITY = True
```

### AuthZ

In your app, define the following configuration:

```python
CERN_SYNC_KEYCLOAK_BASE_URL = "<url>"
CERN_SYNC_AUTHZ_BASE_URL = "<url>"
```

The above `CERN_APP_CREDENTIALS` configuration must be already configured.
You will also need to make sure that those credentials are allowed to fetch
the entire CERN database of user and groups.

Then, create a new celery task and sync users:

```python
from invenio_cern_sync.users.sync import sync

def sync_users_task():
    user_ids = sync(method="AuthZ")
    # you can optionally pass extra kwargs for the AuthZ client APIs.

    # make sure that you re-index users if needed. For example, in InvenioRDM:
    # from invenio_users_resources.services.users.tasks import reindex_users
    # reindex_users.delay(user_ids)
```

To fetch groups:

```python
from invenio_cern_sync.groups.sync import sync

def sync_groups_task():
    roles_ids = sync()
```

### LDAP

You can use LDAP instead. Install this module with the ldap extra dependency:

```shell
pip install invenio-cern-sync[ldap]
```

Define the LDAP url:

```python
CERN_SYNC_LDAP_URL = <url>
```

Then, create a new celery task and sync users:

```python
from invenio_cern_sync.users.sync import sync

def sync_users_task():
    user_ids = sync(method="LDAP")
    # you can optionally pass extra kwargs for the LDAP client APIs.
```
