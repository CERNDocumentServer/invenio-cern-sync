# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Integrates CERN databases with Invenio."""

from .ext import InvenioCERNSync

__version__ = "0.1.1"

__all__ = ("__version__", "InvenioCERNSync")
