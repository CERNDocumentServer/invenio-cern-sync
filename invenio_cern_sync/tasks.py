# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync tasks."""

from celery import current_app, shared_task

from invenio_db import db

from .users.sync import sync


@shared_task
def sync_users():
    """Task to sync users with LDAP."""
    if current_app.config.get("DEBUG", True):
        current_app.logger.warning(
            "Users sync with CERN LDAP disabled, the DEBUG env var is True."
        )
        return

    try:
        sync()
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(e)
