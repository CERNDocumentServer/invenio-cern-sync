# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-CERN-sync is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Invenio-CERN-sync users profile API."""

from marshmallow import Schema, fields


class CERNUserProfileSchema(Schema):
    """The CERN default user profile schema."""

    affiliations = fields.String()
    department = fields.String()
    family_name = fields.String()
    full_name = fields.String()
    given_name = fields.String()
    group = fields.String()
    mailbox = fields.String()
    orcid = fields.String()
    person_id = fields.String()
    section = fields.String()
