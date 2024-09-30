# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync Authz - user profile mapper."""


def userprofile_mapper(cern_identity):
    """Map the CERN Identity fields to the Invenio user profile schema.

    The returned dict structure must match the user profile schema defined via
    the config ACCOUNTS_USER_PROFILE_SCHEMA."""
    return dict(
        affiliations=cern_identity["instituteName"] or "",
        department=cern_identity["cernDepartment"] or "",
        family_name=cern_identity["lastName"],
        full_name=cern_identity["displayName"],
        given_name=cern_identity["firstName"],
        group=cern_identity["cernGroup"] or "",
        mailbox=cern_identity["postOfficeBox"] or "",
        orcid=cern_identity["orcid"] or "",
        person_id=cern_identity["personId"],
        section=cern_identity["cernSection"] or "",
    )


def remoteaccount_extradata_mapper(cern_identity):
    """Map the CERN Identity to the Invenio remote account extra data.

    :param cern_identity: the identity dict
    :return: a serialized dict, containing all the keys that will appear in the
        RemoteAccount.extra_data column. Any unwanted key should be removed.
    """
    return dict(
        person_id=cern_identity["personId"],
        uidNumber=cern_identity["uid"],
        username=cern_identity["upn"].lower(),
    )
