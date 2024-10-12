# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync logging."""

import json
import uuid

from flask import current_app


def _log(log_func, name, extra=dict(), log_uuid=None):
    """Format log."""
    uuid_ = log_uuid or str(uuid.uuid4())
    structured_msg = dict(name=name, uuid=uuid_, **extra)
    msg = json.dumps(structured_msg, sort_keys=True)
    log_func(msg)


def log_debug(name, extra=dict(), log_uuid=None):
    """Log debug."""
    _log(current_app.logger.debug, name, extra=extra, log_uuid=log_uuid)


def log_info(name, extra=dict(), log_uuid=None):
    """Log info."""
    _log(current_app.logger.info, name, extra=extra, log_uuid=log_uuid)


def log_warning(name, extra=dict(), log_uuid=None):
    """Log warning."""
    _log(current_app.logger.warning, name, extra=extra, log_uuid=log_uuid)


def log_error(name, extra=dict(), log_uuid=None):
    """Log error."""
    _log(current_app.logger.error, name, extra=extra, log_uuid=log_uuid)
