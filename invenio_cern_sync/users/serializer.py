# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync users serializer API."""

from flask import current_app

from .errors import InvalidLdapUser
from .utils import first_or_default, first_or_raise


def _serialize_ldap_user(ldap_user, userprofile_mapper, extra_data_mapper):
    """Serialize ldap user to Invenio user."""
    employee_id = first_or_raise(
        ldap_user, "employeeID", "unknown"
    )  # this should always exist
    return dict(
        email=first_or_raise(ldap_user, "mail").lower(),
        username=first_or_raise(ldap_user, "cn").lower(),
        active=first_or_default(ldap_user, "cernActiveStatus", "Active").lower()
        == "active",
        user_profile=userprofile_mapper(ldap_user),
        preferences=dict(
            locale=first_or_default(ldap_user, "preferredLanguage", "en").lower()
        ),
        user_identity_id=employee_id,
        remote_account_extra_data=extra_data_mapper(ldap_user),
    )


def serialize_ldap_users(ldap_users):
    """Serialize ldap users to Invenio users."""
    userprofile_mapper = current_app.config["CERN_SYNC_USERPROFILE_MAPPER"]
    extra_data_mapper = current_app.config["CERN_SYNC_USER_EXTRADATA_MAPPER"]

    for ldap_user in ldap_users:
        try:
            yield _serialize_ldap_user(ldap_user, userprofile_mapper, extra_data_mapper)
        except InvalidLdapUser as ex:
            # LOG-ME!
            continue
