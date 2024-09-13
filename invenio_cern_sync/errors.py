# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync ldap exceptions."""


class InvalidLdapUser(Exception):
    """Invalid user exception."""

    def __init__(self, key, employee_id):
        """Constructor."""
        msg = f"Missing {key} field or invalid value for employeeID {employee_id}."
        super().__init__(msg)


class InvalidCERNIdentity(Exception):
    """Invalid user exception."""

    def __init__(self, key, personId):
        """Constructor."""
        msg = f"Missing {key} field or invalid value for personId {personId}."
        super().__init__(msg)


class RequestError(Exception):
    """Failed CERN Auth request."""

    def __init__(self, url, error_details):
        """Initialise error."""
        msg = f"Request error on {url}.\n Error details: {error_details}"
        super().__init__(msg)
