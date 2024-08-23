# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync users serializer API."""

from .errors import InvalidLdapUser


def first_or_raise(d, key, employee_id):
    """Return the decoded first value of the given key or raise."""
    try:
        return d[key][0].decode("utf8")
    except (KeyError, IndexError, AttributeError):
        raise InvalidLdapUser(key, employee_id)


def first_or_default(d, key, default=""):
    """Return the decoded first value of the given key or return default."""
    try:
        return d[key][0].decode("utf8")
    except (KeyError, IndexError, AttributeError):
        return default
