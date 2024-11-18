# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync groups sync API."""

import time
import uuid

from invenio_oauthclient.handlers.utils import create_or_update_roles

from ..authz.client import AuthZService, KeycloakService
from ..logging import log_info


def _truncate_string(input_string, max_length=255):
    """Truncate string."""
    if len(input_string) > max_length:
        return input_string[: max_length - 3] + "..."
    return input_string


def _serialize_groups(groups):
    """Serialize groups."""
    for group in groups:
        description = group.get("description", "")
        truncated_description = _truncate_string(description)
        yield {
            "id": group["groupIdentifier"],
            "name": group["displayName"],
            "description": truncated_description,
        }


def sync(**kwargs):
    """Sync CERN groups with local db."""
    log_uuid = str(uuid.uuid4())
    log_name = "groups-sync"
    log_info(
        log_name,
        dict(action="fetching-cern-groups", status="started"),
        log_uuid=log_uuid,
    )
    start_time = time.time()

    overridden_params = kwargs.get("keycloak_service", dict())
    keycloak_service = KeycloakService(**overridden_params)

    overridden_params = kwargs.get("authz_service", dict())
    authz_client = AuthZService(keycloak_service, **overridden_params)

    overridden_params = kwargs.get("groups", dict())
    groups = authz_client.get_groups(**overridden_params)

    log_info(
        log_name,
        dict(action="fetching-cern-groups", status="completed"),
        log_uuid=log_uuid,
    )
    log_info(
        log_name,
        dict(action="creating-updating-groups", status="started"),
        log_uuid=log_uuid,
    )
    roles_ids = create_or_update_roles(_serialize_groups(groups))
    log_info(
        log_name,
        dict(
            action="creating-updating-groups", status="completed", count=len(roles_ids)
        ),
        log_uuid=log_uuid,
    )

    total_time = time.time() - start_time
    log_info(log_name, dict(status="completed", time=total_time), log_uuid=log_uuid)

    return list(roles_ids)
