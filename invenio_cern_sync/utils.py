# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync utils."""


def first_or_raise(d, key):
    """Return the decoded first value of the given key or raise."""
    return d[key][0].decode("utf8")


def first_or_default(d, key, default=""):
    """Return the decoded first value of the given key or return default."""
    try:
        return d[key][0].decode("utf8")
    except (KeyError, IndexError, AttributeError):
        return default


def is_different(new_dict, existing_dict):
    """Return True new_dict has new keys or updated values."""
    for key, value in new_dict.items():
        if key not in existing_dict or existing_dict[key] != value:
            return True
