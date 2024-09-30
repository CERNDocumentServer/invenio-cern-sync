# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync SSO api."""

from flask import current_app, g
from invenio_db import db
from invenio_oauthclient import current_oauthclient, oauth_link_external_id
from invenio_oauthclient.contrib.keycloak.handlers import get_user_info
from invenio_userprofiles.forms import confirm_register_form_preferences_factory
from werkzeug.local import LocalProxy

######################################################################################
# User profile custom form

_security = LocalProxy(lambda: current_app.extensions["security"])


def confirm_registration_form(*args, **kwargs):
    """Custom confirm form."""
    Form = confirm_register_form_preferences_factory(_security.confirm_register_form)

    class _Form(Form):
        password = None
        recaptcha = None
        submit = None  # defined in the template

    return _Form(*args, **kwargs)


######################################################################################
# User handler


def cern_setup_handler(remote, token, resp):
    """Perform additional setup after the user has been logged in."""
    token_user_info, _ = get_user_info(remote, resp)

    with db.session.begin_nested():
        username = token_user_info["sub"]
        # cern_person_id is not set for non-CERN users (EduGain)
        external_id = token_user_info.get("cern_person_id", username)
        extra_data = {
            "keycloak_id": username,
            "person_id": external_id,
        }
        token.remote_account.extra_data = extra_data

        user = token.remote_account.user
        user_identity = {"id": external_id, "method": remote.name}

        # link User with UserIdentity
        oauth_link_external_id(user, user_identity)


def cern_info_handler(remote, resp):
    """Info handler."""
    token_user_info, user_info = get_user_info(remote, resp)

    # Add the user_info to the request, so it can be used in the groups handler
    # to avoid yet another request to the user info endpoint
    g._cern_groups = user_info.get("groups", [])

    handlers = current_oauthclient.signup_handlers[remote.name]
    return handlers["info_serializer"](resp, token_user_info, user_info)


def cern_info_serializer(remote, resp, token_user_info, user_info):
    """Info serializer."""
    user_info = user_info or {}

    username = token_user_info["sub"]
    email = token_user_info["email"]
    # cern_person_id might be missing for non-CERN users (EduGain)
    external_id = token_user_info.get("cern_person_id", username)
    preferred_language = user_info.get("cern_preferred_language", "en").lower()
    return {
        "user": {
            "active": True,
            "email": email,
            "profile": {
                "affiliations": user_info.get("home_institute", ""),
                "full_name": user_info["name"],
                "username": username,
            },
            "prefs": {
                "visibility": "public",
                "email_visibility": "public",
                "locale": preferred_language,
            },
        },
        "external_id": external_id,
        "external_method": remote.name,
    }


######################################################################################
# Groups handler


def cern_groups_handler(remote, resp):
    """Retrieves groups from remote account.

    Groups are in the user info response.
    """
    groups = g.pop("_cern_groups", [])
    handlers = current_oauthclient.signup_handlers[remote.name]
    # `remote` param automatically injected via `make_handler` helper
    return handlers["groups_serializer"](groups)


def cern_groups_serializer(remote, groups, **kwargs):
    """Serialize the groups response object."""
    serialized_groups = []
    # E-groups do have unique names and this name cannot be updated,
    # therefore the name can act as an ID for Invenio
    for group_name in groups:
        serialized_groups.append({"id": group_name, "name": group_name})

    return serialized_groups
