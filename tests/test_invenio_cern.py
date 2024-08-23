# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from flask import Flask

from invenio_cern_sync import InvenioCERNSync


def test_version():
    """Test version import."""
    from invenio_cern_sync import __version__

    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    ext = InvenioCERNSync(app)
    assert "invenio-cern-sync" in app.extensions

    app = Flask("testapp")
    ext = InvenioCERNSync()
    assert "invenio-cern-sync" not in app.extensions
    ext.init_app(app)
    assert "invenio-cern-sync" in app.extensions
