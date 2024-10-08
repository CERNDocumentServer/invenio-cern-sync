# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Integrates CERN databases with Invenio."""

from . import config


class InvenioCERNSync(object):
    """Invenio-CERN-Sync extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions["invenio-cern-sync"] = self

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("CERN_SYNC_"):
                app.config.setdefault(k, getattr(config, k))
