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


def _is_different(dict1, dict2):
    """Return true if they differ."""
    return (
        len(
            [
                key
                for key in dict1.keys() | dict2.keys()
                if dict1.get(key) != dict2.get(key)
            ]
        )
        > 0
    )
