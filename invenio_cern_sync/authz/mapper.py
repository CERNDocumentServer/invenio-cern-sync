# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync Authz - user profile mapper."""


def userprofile_mapper(cern_identity):
    """Map the CERN Identity fields to the Invenio user profile schema.

    :param cern_identity: the identity dict
    :param profile_schema: the Invenio user profile schema to map to
    :return: a serialized dict, containing all the keys that will appear in the
        User.profile JSON column. Any unwanted key should be removed.
    """
    return dict(
        cern_department=cern_identity["cernDepartment"],
        cern_group=cern_identity["cernGroup"],
        cern_section=cern_identity["cernSection"],
        family_name=cern_identity["lastName"],
        full_name=cern_identity["displayName"],
        given_name=cern_identity["firstName"],
        institute_abbreviation=cern_identity["instituteAbbreviation"],
        institute=cern_identity["instituteName"],
        mailbox=cern_identity.get("postOfficeBox", ""),
        person_id=cern_identity["personId"],
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
