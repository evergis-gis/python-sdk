# -*- coding: utf-8 -*-
"""Typed attribute helpers for special StringSubType / AttributeType combinations.

Each submodule covers one server-side ``StringSubType`` (currently only
``Attachments``; ``Image`` and ``PkkCode`` can follow the same shape) and
exposes:

- a Pydantic model for one value;
- helper constructors;
- JSON serializers for the attribute column;
- a ``make_*_attribute()`` builder for the schema entry.
"""

from ._registry import SUB_TYPE_BUILDERS, register_sub_type
from .attachments import (
    Attachment,
    AttachmentsAttribute,
    attachment_from_file,
    attachment_from_resource,
    attachment_from_url,
    attachments_from_json,
    attachments_to_json,
)
from .calculated import CalculatedAttribute

__all__ = [
    "Attachment",
    "AttachmentsAttribute",
    "CalculatedAttribute",
    "SUB_TYPE_BUILDERS",
    "attachment_from_file",
    "attachment_from_resource",
    "attachment_from_url",
    "attachments_from_json",
    "attachments_to_json",
    "register_sub_type",
]
