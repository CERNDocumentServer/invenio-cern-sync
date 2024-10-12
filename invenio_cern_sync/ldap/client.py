# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync LDAP Client."""

try:
    import ldap
except ImportError:
    ldap = None
from flask import current_app

BASE = "OU=Users,OU=Organic Units,DC=cern,DC=ch"

PRIMARY_ACCOUNTS_FILTER = "(&(cernAccountType=Primary)(cernActiveStatus=Active))"

RESPONSE_FIELDS = [
    "cernAccountType",
    "cernActiveStatus",
    "cernGroup",
    "cernInstituteName",
    "cernSection",
    "cn",  # username
    "department",
    "displayName",  # last + first name
    "division",
    "employeeID",  # person id (unique - never changes, only in case of mistakes)
    "givenName",  # first name
    "mail",
    "postOfficeBox",
    "preferredLanguage",
    "sn",  # last name
    "uidNumber",  # uid (unique - can change if user leaves CERN for > 6 months, then comes back)
]


class LdapClient:
    """Ldap client class for user importation/synchronization.

    Response example:
        [
            {
                'cernAccountType': [b'Primary'],
                'cernActiveStatus': [b'Active'],
                'cernGroup': [b'CA'],
                'cernInstituteAbbreviation': [b'CERN'],
                'cernInstituteName': [b'CERN'],
                'cernSection': [b'IR'],
                'cn': [b'joefoe'],
                'department': [b'IT/CA'],
                'displayName': [b'Joe Foe'],
                'division': [b'IT'],
                'givenName': [b'Joe'],
                'mail': [b'joe.foe@cern.ch'],
                'employeeID': [b'101010'],
                'postOfficeBox': [b'M31120'],
                'preferredLanguage': [b'EN'],
                'sn': [b'Foe'],
                'uidNumber': [b'100000'],
            },
            ...
        ]
    """

    def __init__(self, ldap_url=None, base=BASE):
        """Initialize ldap connection."""
        ldap_url = ldap_url or current_app.config["CERN_SYNC_LDAP_URL"]
        self._ldap = ldap.initialize(ldap_url)
        self._base = base

    def _search_paginated(self, filter, fields, page_control):
        """Execute search to get primary accounts."""
        return self._ldap.search_ext(
            self._base,
            ldap.SCOPE_ONELEVEL,
            filter,
            fields,
            serverctrls=[page_control],
        )

    def get_primary_accounts(
        self, filter=PRIMARY_ACCOUNTS_FILTER, fields=RESPONSE_FIELDS
    ):
        """Retrieve all primary accounts from ldap."""
        page_control = ldap.controls.SimplePagedResultsControl(
            True, size=1000, cookie=""
        )
        result = []
        while True:
            response = self._search_paginated(filter, fields, page_control)
            rtype, rdata, rmsgid, serverctrls = self._ldap.result3(response)
            result.extend([x[1] for x in rdata])

            ldap_page_control = ldap.controls.SimplePagedResultsControl
            ldap_page_control_type = ldap_page_control.controlType
            controls = [
                control
                for control in serverctrls
                if control.controlType == ldap_page_control_type
            ]
            if not controls:
                current_app.logger.exception("The server ignores RFC 2696 control")
                break
            if not controls[0].cookie:
                break
            page_control.cookie = controls[0].cookie

        return result
