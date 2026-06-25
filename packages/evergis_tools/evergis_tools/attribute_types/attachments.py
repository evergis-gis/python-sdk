# -*- coding: utf-8 -*-
"""Attachments attribute support.

EverGIS stores file attachments inside a JSON column flagged on the schema
side with ``StringSubType.Attachments``. The server treats the value as
opaque JSON; the structure is determined by the UI plugin that renders the
file list. This module fixes that structure as a Pydantic model and gives
helpers for both the schema entry and the JSON value.

Wire format (one entry):

.. code-block:: json

    {
      "date": "2025-02-01T11:10:00.240878Z",
      "link": "42b7c984ddf94730a36aa4e16d2a04b3",
      "name": "pic.png",
      "mimeType": "image/png",
      "isExternal": false
    }

Two flavours of ``link``:

- ``isExternal=False`` - ``link`` is a 32-hex catalog ``resourceId``;
- ``isExternal=True``  - ``link`` is an ``http(s)://...`` URL.

Typical use:

.. code-block:: python

    from evergis_tools.attribute_types import (
        Attachment, AttachmentsAttribute,
        attachment_from_url, attachment_from_file,
        attachments_to_json,
    )
    from evergis_tools.layers import add_layer_attribute

    # 1. add the column to the layer schema (server auto-creates the
    #    backing physical column from the PATCH /layers call)
    add_layer_attribute(
        client, layer_name,
        AttachmentsAttribute(attributeName="docs", alias="Documents"),
    )

    # 2. build a value from a URL and an uploaded file
    items = [
        attachment_from_url("https://example.com/spec.pdf"),
        attachment_from_file(client, "report.pdf",
                             parent_path="john_doe:Projects/Files"),
    ]
    gdf.loc[idx, "docs"] = attachments_to_json(items)
"""

from __future__ import annotations

import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, List, Literal, Optional, Union
from urllib.parse import unquote, urlparse

from pydantic import BaseModel, ConfigDict, Field, model_validator

from evergis_api import Client
from evergis_api.schemas import (
    AttributeConfigurationType,
    AttributeType,
    StringAttributeConfigurationDc,
    StringSubType,
)

from ._registry import register_sub_type


_DEFAULT_MIME = "application/octet-stream"


class Attachment(BaseModel):
    """Single file reference inside an Attachments-typed attribute.

    Field order matches the wire format.
    """

    date: str
    link: str
    name: str
    mimeType: str
    isExternal: bool

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @model_validator(mode="after")
    def _check_link(self) -> "Attachment":
        if self.isExternal:
            if not (self.link.startswith("http://") or self.link.startswith("https://")):
                raise ValueError(
                    f"isExternal=True but link is not an http(s) URL: {self.link!r}"
                )
        else:
            # Catalog resourceId is a 32-char hex (no dashes); be lenient and
            # only reject obviously wrong values like URLs.
            if "://" in self.link:
                raise ValueError(
                    f"isExternal=False but link looks like a URL: {self.link!r}"
                )
        return self


def _format_date(dt: Optional[datetime]) -> str:
    """Return an ISO-8601 UTC string. Defaults to ``datetime.now(UTC)``."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _guess_mime(name: str, fallback: str = _DEFAULT_MIME) -> str:
    mime, _ = mimetypes.guess_type(name)
    return mime or fallback


def attachment_from_url(
    url: str,
    *,
    name: Optional[str] = None,
    mime_type: Optional[str] = None,
    date: Optional[datetime] = None,
) -> Attachment:
    """Build an :class:`Attachment` pointing at an external URL.

    ``name`` defaults to the URL-decoded last path segment of ``url``;
    ``mime_type`` is guessed from the resulting filename via :mod:`mimetypes`
    and falls back to ``application/octet-stream``.
    """
    if name is None:
        path_part = unquote(urlparse(url).path or "")
        name = Path(path_part).name or url
    if mime_type is None:
        mime_type = _guess_mime(name)
    return Attachment(
        date=_format_date(date),
        link=url,
        name=name,
        mimeType=mime_type,
        isExternal=True,
    )


def attachment_from_resource(
    client: Client,
    identifier: str,
    *,
    name: Optional[str] = None,
    mime_type: Optional[str] = None,
    date: Optional[datetime] = None,
) -> Attachment:
    """Build an :class:`Attachment` pointing at an existing catalog resource.

    Args:
        client: EverGIS API client.
        identifier: catalog path / resource ID / system name; resolved via
            :func:`evergis_tools.catalog.resources.resolve_resource`.
        name: display name; defaults to the resource's ``name`` attribute.
        mime_type: explicit MIME type; otherwise guessed from ``name``.
    """
    # Local import to avoid a circular dependency at module load time.
    from ..catalog.resources import resolve_resource

    resource = resolve_resource(client, identifier)
    name = name or getattr(resource, "name", None) or resource.resourceId
    if mime_type is None:
        mime_type = _guess_mime(name)
    return Attachment(
        date=_format_date(date),
        link=resource.resourceId,
        name=name,
        mimeType=mime_type,
        isExternal=False,
    )


def attachment_from_file(
    client: Client,
    file_path: Union[str, Path],
    *,
    parent_id: Optional[str] = None,
    parent_path: Optional[str] = None,
    name: Optional[str] = None,
    mime_type: Optional[str] = None,
    rewrite: bool = True,
    date: Optional[datetime] = None,
) -> Attachment:
    """Upload a local file into the catalog and return an Attachment for it.

    Either ``parent_id`` or ``parent_path`` must be supplied - they are
    forwarded to :func:`evergis_tools.catalog.files.upload_file`.

    ``name`` and ``mime_type`` default to the uploaded file's basename and
    a guess from its extension respectively.
    """
    from ..catalog.files import upload_file

    uploaded = upload_file(
        client=client,
        file_path=file_path,
        parent_id=parent_id,
        parent_path=parent_path,
        rewrite=rewrite,
    )
    fp = Path(file_path)
    display_name = name or fp.name
    if mime_type is None:
        mime_type = _guess_mime(display_name)
    return Attachment(
        date=_format_date(date),
        link=uploaded.resourceId,
        name=display_name,
        mimeType=mime_type,
        isExternal=False,
    )


def attachments_to_json(items: Iterable[Attachment]) -> str:
    """Serialize a sequence of attachments to the JSON string stored in a feature."""
    payload = [item.model_dump(mode="json") for item in items]
    return json.dumps(payload, ensure_ascii=False)


def attachments_from_json(value: Any) -> List[Attachment]:
    """Parse an Attachments attribute value back into a list of :class:`Attachment`.

    Accepts a JSON string, an already-parsed list / tuple, or a null-ish value
    (``None``, ``""``, ``"[]"``, pandas ``NaN``) which produce an empty list.
    """
    import math

    if value is None or value == "":
        return []
    if isinstance(value, float) and math.isnan(value):
        return []
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, (list, tuple)):
        raise TypeError(
            f"Expected a JSON array, got {type(value).__name__}: {value!r}"
        )
    return [Attachment.model_validate(item) for item in value]


@register_sub_type("Attachments")
class AttachmentsAttribute(StringAttributeConfigurationDc):
    """Schema entry for an attachments column.

    Pre-fills the ``(attributeConfigurationType=String, type=Json,
    subType=Attachments)`` triplet so the caller only supplies
    ``attributeName``, ``alias`` and the usual flags. The instance still
    *is* a :class:`StringAttributeConfigurationDc`, so it can be appended
    directly to ``AttributesConfigurationDc.attributes``.

    The server stores the value as ``type=Json``; the ``subType=Attachments``
    flag is what tells the EverGIS UI to render it as the file-list widget.
    Use :func:`attachments_to_json` to produce values that match.

    Example:
        >>> cfg.attributesConfiguration.attributes.append(
        ...     AttachmentsAttribute(attributeName="docs", alias="Documents")
        ... )

    Declarative use via Pydantic schema (recognised by
    :func:`create_layer_from_schema`)::

        class MySchema(BaseModel):
            docs: list = Field(
                description="Documents",
                json_schema_extra={"sub_type": "Attachments"},
            )
    """

    attribute_configuration_type: Literal[AttributeConfigurationType.STRING] = Field(
        default=AttributeConfigurationType.STRING, alias="attributeConfigurationType"
    )
    type: Literal[AttributeType.JSON] = Field(default=AttributeType.JSON)
    sub_type: Literal[StringSubType.ATTACHMENTS] = Field(
        default=StringSubType.ATTACHMENTS, alias="subType"
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        use_enum_values=True,
    )

    @classmethod
    def from_field(cls, field_name: str, field_info: Any) -> "AttachmentsAttribute":
        """Build an instance from a Pydantic ``FieldInfo``.

        Used by :func:`create_layer_from_schema` when it sees a field with
        ``Field(json_schema_extra={"sub_type": "Attachments"})``. The EverGIS
        ``alias`` is taken from Pydantic's ``description`` (this matches the
        convention used by every other attribute in
        ``create_layer_from_schema``).
        """
        return cls(
            attributeName=field_name,
            columnName=field_name,
            alias=getattr(field_info, "description", None) or None,
        )

    @model_validator(mode="after")
    def _finalize(self) -> "AttachmentsAttribute":
        # Default columnName to attributeName. EverGIS routes the value to
        # the physical column by ``columnName``; without it the server
        # cannot resolve the target and returns 500 on insert/update.
        if self.columnName is None:
            self.columnName = self.attributeName

        # The generated EverGIS client serializes payloads with
        # ``model_dump(exclude_unset=True)`` and the parent ``attributes``
        # field is an un-discriminated Union, so without these explicit
        # marks our locked literals would silently drop out of the patch.
        self.__pydantic_fields_set__.update(
            {
                "type",
                "sub_type",
                "attribute_configuration_type",
                "is_nullable",
                "columnName",
            }
        )
        return self


__all__ = [
    "Attachment",
    "AttachmentsAttribute",
    "attachment_from_file",
    "attachment_from_resource",
    "attachment_from_url",
    "attachments_from_json",
    "attachments_to_json",
]
