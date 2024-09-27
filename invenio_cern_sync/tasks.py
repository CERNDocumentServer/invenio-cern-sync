# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync tasks."""

from flask import current_app
from celery import shared_task
from invenio_db import db

from .users.sync import sync as users_sync
from .groups.sync import sync as groups_sync


@shared_task
def sync_users(*args, **kwargs):
    """Task to sync users with CERN database."""
    if current_app.config.get("DEBUG", True):
        current_app.logger.warning(
            "Users sync disabled, the DEBUG env var is True."
        )
        return

    try:
        users_sync(*args, **kwargs)
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(e)


@shared_task
def sync_groups(*args, **kwargs):
    """Task to sync groups with CERN database."""
    if current_app.config.get("DEBUG", True):
        current_app.logger.warning(
            "Groups sync disabled, the DEBUG env var is True."
        )
        return

    try:
        groups_sync(*args, **kwargs)
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(e)
