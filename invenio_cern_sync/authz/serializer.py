# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync CERN identities serializer API."""

from flask import current_app

from ..errors import InvalidCERNIdentity


def serialize_cern_identity(cern_identity):
    """Serialize CERN identity to Invenio user."""
    userprofile_mapper = current_app.config["CERN_SYNC_AUTHZ_USERPROFILE_MAPPER"]
    extra_data_mapper = current_app.config["CERN_SYNC_AUTHZ_USER_EXTRADATA_MAPPER"]
    try:
        # The assumption here is that we only sync CERN primary accounts.
        # The personId does not exist for external accounts (EduGain, social logins or guest accounts)
        person_id = cern_identity["personId"]
    except KeyError:
        raise InvalidCERNIdentity("personId", "unknown")

    try:
        # cern_identity.get("preferredCernLanguage") or "en"  # value can be None
        language = "en"  # Invenio supports only English for now
        serialized = dict(
            email=cern_identity["primaryAccountEmail"].lower(),
            username=cern_identity["upn"].lower(),
            user_profile=userprofile_mapper(cern_identity),
            preferences=dict(locale=language.lower()),
            user_identity_id=person_id,
            remote_account_extra_data=extra_data_mapper(cern_identity),
        )
    except (KeyError, IndexError, AttributeError) as e:
        raise InvalidCERNIdentity(e.args[0], person_id)

    return serialized


def serialize_cern_identities(cern_identities):
    """Serialize CERN identities to Invenio users."""
    for cern_identity in cern_identities:
        try:
            yield serialize_cern_identity(cern_identity)
        except InvalidCERNIdentity as e:
            current_app.logger.warning(str(e) + " Skipping this identity...")
            continue
