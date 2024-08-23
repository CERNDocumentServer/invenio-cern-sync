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
        self._key = key
        self._employee_id = employee_id

    @property
    def description(self):
        """Exception description."""
        return f"Missing {self._key} field or invalid value for employeeID {self._employee_id}."
