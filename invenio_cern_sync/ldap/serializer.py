# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync LDAP users serializer API."""

from flask import current_app

from ..errors import InvalidLdapUser
from ..utils import first_or_default, first_or_raise


def serialize_ldap_user(ldap_user, userprofile_mapper=None, extra_data_mapper=None):
    """Serialize LDAP user to Invenio user."""
    userprofile_mapper = (
        userprofile_mapper or current_app.config["CERN_SYNC_LDAP_USERPROFILE_MAPPER"]
    )
    extra_data_mapper = (
        extra_data_mapper or current_app.config["CERN_SYNC_LDAP_USER_EXTRADATA_MAPPER"]
    )
    try:
        # The assumption here is that we only sync CERN primary accounts.
        # The personId does not exist for external accounts (EduGain, social logins or guest accounts)
        person_id = first_or_raise(ldap_user, "employeeID")
    except KeyError:
        raise InvalidLdapUser("employeeID", "unknown")

    try:
        serialized = dict(
            email=first_or_raise(ldap_user, "mail").lower(),
            username=first_or_raise(ldap_user, "cn").lower(),
            user_profile=userprofile_mapper(ldap_user),
            preferences=dict(
                locale=first_or_default(ldap_user, "preferredLanguage", "en").lower()
            ),
            user_identity_id=person_id,
            remote_account_extra_data=extra_data_mapper(ldap_user),
        )
    except (KeyError, IndexError, AttributeError) as e:
        raise InvalidLdapUser(e.args[0], person_id)

    return serialized


def serialize_ldap_users(ldap_users):
    """Serialize LDAP users to Invenio users."""
    for ldap_user in ldap_users:
        yield serialize_ldap_user(ldap_user)
