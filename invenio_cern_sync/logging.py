# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync logging."""

import json

from flask import current_app


def _log(log_func, log_uuid, action, extra=dict()):
    """Format log."""
    structured_msg = dict(name="sync_users", uuid=log_uuid, action=action, **extra)
    msg = json.dumps(structured_msg, sort_keys=True)
    log_func(msg)


def log_info(log_uuid, action, extra=dict()):
    """Log info."""
    _log(current_app.logger.info, log_uuid, action, extra)


def log_warning(log_uuid, action, extra=dict()):
    """Log warning."""
    _log(current_app.logger.warning, log_uuid, action, extra)


def log_error(log_uuid, action, extra=dict()):
    """Log error."""
    _log(current_app.logger.error, log_uuid, action, extra)
