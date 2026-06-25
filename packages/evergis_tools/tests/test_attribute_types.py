# -*- coding: utf-8 -*-
"""Tests for evergis_tools.attribute_types: Attachment / AttachmentsAttribute /
CalculatedAttribute / builders / serializers / SubType registry."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from evergis_api.schemas import (
    AttributeConfigurationType,
    AttributeType,
    StringSubType,
)

from evergis_tools.attribute_types import (
    Attachment,
    AttachmentsAttribute,
    CalculatedAttribute,
    SUB_TYPE_BUILDERS,
    attachment_from_file,
    attachment_from_resource,
    attachment_from_url,
    attachments_from_json,
    attachments_to_json,
    register_sub_type,
)


# =====================================================================
# Attachment (Pydantic model)
# =====================================================================


class TestAttachment:
    """Attachment model: fields, validators, model_config."""

    def test_valid_external(self):
        att = Attachment(
            date="2025-01-01T00:00:00Z",
            link="https://example.com/file.pdf",
            name="file.pdf",
            mimeType="application/pdf",
            isExternal=True,
        )
        assert att.link == "https://example.com/file.pdf"
        assert att.isExternal is True

    def test_valid_internal(self):
        att = Attachment(
            date="2025-01-01T00:00:00Z",
            link="42b7c984ddf94730a36aa4e16d2a04b3",
            name="pic.png",
            mimeType="image/png",
            isExternal=False,
        )
        assert att.isExternal is False

    def test_external_requires_url(self):
        # isExternal=True with non-URL link must raise.
        with pytest.raises(ValidationError, match="link is not an http"):
            Attachment(
                date="2025-01-01T00:00:00Z",
                link="not-a-url",
                name="x",
                mimeType="x",
                isExternal=True,
            )

    def test_internal_rejects_url(self):
        with pytest.raises(ValidationError, match="looks like a URL"):
            Attachment(
                date="2025-01-01T00:00:00Z",
                link="https://example.com/x",
                name="x",
                mimeType="x",
                isExternal=False,
            )

    def test_extra_forbid(self):
        with pytest.raises(ValidationError):
            Attachment(
                date="2025-01-01T00:00:00Z",
                link="abc",
                name="x",
                mimeType="x",
                isExternal=False,
                unknown_field="boom",
            )

    def test_round_trip_json(self):
        att = Attachment(
            date="2025-01-01T00:00:00Z",
            link="abc123",
            name="x",
            mimeType="text/plain",
            isExternal=False,
        )
        dumped = att.model_dump(mode="json")
        roundtrip = Attachment(**dumped)
        assert roundtrip == att


# =====================================================================
# AttachmentsAttribute
# =====================================================================


class TestAttachmentsAttribute:
    """Schema entry for Attachments columns."""

    def test_defaults(self):
        a = AttachmentsAttribute(attributeName="docs")
        # Literal-locked + use_enum_values=True yields the string enum value.
        assert a.attribute_configuration_type == AttributeConfigurationType.STRING.value
        assert a.type == AttributeType.JSON.value
        assert a.sub_type == StringSubType.ATTACHMENTS.value

    def test_column_name_auto_filled(self):
        a = AttachmentsAttribute(attributeName="docs")
        assert a.columnName == "docs"

    def test_column_name_explicit(self):
        a = AttachmentsAttribute(attributeName="docs", columnName="attachments_col")
        assert a.columnName == "attachments_col"

    def test_alias(self):
        a = AttachmentsAttribute(attributeName="docs", alias="Documents")
        assert a.alias == "Documents"

    def test_from_field_uses_description_as_alias(self):
        info = MagicMock()
        info.description = "Documents"
        a = AttachmentsAttribute.from_field("docs", info)
        assert a.attributeName == "docs"
        assert a.columnName == "docs"
        assert a.alias == "Documents"

    def test_from_field_no_description(self):
        info = MagicMock(spec=[])  # spec=[] - no description attribute
        a = AttachmentsAttribute.from_field("docs", info)
        assert a.alias is None

    def test_finalize_marks_fields_set(self):
        a = AttachmentsAttribute(attributeName="docs")
        # _finalize must mark literal-locked / defaulted fields so they are
        # included in patch payloads with exclude_unset=True.
        assert {
            "type",
            "sub_type",
            "attribute_configuration_type",
            "is_nullable",
            "columnName",
        }.issubset(a.__pydantic_fields_set__)


# =====================================================================
# Builders
# =====================================================================


class TestAttachmentFromUrl:
    """attachment_from_url()."""

    def test_simple_url(self):
        att = attachment_from_url("https://example.com/spec.pdf")
        assert att.link == "https://example.com/spec.pdf"
        assert att.isExternal is True
        assert att.name == "spec.pdf"
        assert att.mimeType == "application/pdf"

    def test_url_with_encoded_name(self):
        att = attachment_from_url("https://example.com/foo%20bar.png")
        assert att.name == "foo bar.png"
        assert att.mimeType == "image/png"

    def test_url_explicit_name_and_mime(self):
        att = attachment_from_url(
            "https://example.com/x", name="report", mime_type="application/json"
        )
        assert att.name == "report"
        assert att.mimeType == "application/json"

    def test_unknown_extension_fallback_mime(self):
        att = attachment_from_url("https://example.com/data.unknownext")
        assert att.mimeType == "application/octet-stream"

    def test_explicit_date(self):
        dt = datetime(2020, 5, 17, 12, 0, 0, tzinfo=timezone.utc)
        att = attachment_from_url("https://example.com/x.pdf", date=dt)
        # ISO format with +00:00
        assert "2020-05-17T12:00:00" in att.date


class TestAttachmentFromResource:
    """attachment_from_resource()."""

    def test_basic(self):
        client = MagicMock()
        resource = MagicMock()
        resource.resourceId = "abc123"
        resource.name = "doc.pdf"
        with patch(
            "evergis_tools.attribute_types.attachments."
            "Attachment._check_link",  # bypass URL validation if needed
            side_effect=lambda self=None: self if self else None,
        ):
            pass  # we keep real validator; resource.resourceId is fine
        with patch(
            "evergis_tools.catalog.resources.resolve_resource",
            return_value=resource,
        ):
            att = attachment_from_resource(client, "em:Files/doc.pdf")
        assert att.link == "abc123"
        assert att.name == "doc.pdf"
        assert att.mimeType == "application/pdf"
        assert att.isExternal is False

    def test_name_fallback_to_resource_id(self):
        client = MagicMock()
        resource = MagicMock(spec=["resourceId"])
        resource.resourceId = "abc123"
        with patch(
            "evergis_tools.catalog.resources.resolve_resource",
            return_value=resource,
        ):
            att = attachment_from_resource(client, "em:something")
        assert att.name == "abc123"

    def test_explicit_name(self):
        client = MagicMock()
        resource = MagicMock()
        resource.resourceId = "abc123"
        resource.name = "stored.bin"
        with patch(
            "evergis_tools.catalog.resources.resolve_resource",
            return_value=resource,
        ):
            att = attachment_from_resource(client, "any", name="display.pdf")
        assert att.name == "display.pdf"
        assert att.mimeType == "application/pdf"


class TestAttachmentFromFile:
    """attachment_from_file(): uploads, then builds an Attachment."""

    def test_uploads_and_builds(self):
        client = MagicMock()
        uploaded = MagicMock()
        uploaded.resourceId = "uploaded123"
        with patch(
            "evergis_tools.catalog.files.upload_file", return_value=uploaded
        ) as up:
            att = attachment_from_file(
                client,
                "/tmp/report.pdf",
                parent_path="em:Files",
            )
        up.assert_called_once()
        call_kwargs = up.call_args.kwargs
        assert call_kwargs["client"] is client
        assert call_kwargs["file_path"] == "/tmp/report.pdf"
        assert call_kwargs["parent_path"] == "em:Files"
        assert call_kwargs["rewrite"] is True
        assert att.link == "uploaded123"
        assert att.name == "report.pdf"
        assert att.mimeType == "application/pdf"
        assert att.isExternal is False

    def test_rewrite_false(self):
        client = MagicMock()
        uploaded = MagicMock()
        uploaded.resourceId = "x"
        with patch(
            "evergis_tools.catalog.files.upload_file", return_value=uploaded
        ) as up:
            attachment_from_file(
                client, "/tmp/a.pdf", parent_path="em:Files", rewrite=False
            )
        assert up.call_args.kwargs["rewrite"] is False

    def test_explicit_name_and_mime(self):
        client = MagicMock()
        uploaded = MagicMock()
        uploaded.resourceId = "x"
        with patch(
            "evergis_tools.catalog.files.upload_file", return_value=uploaded
        ):
            att = attachment_from_file(
                client,
                "/tmp/a.pdf",
                parent_path="em:Files",
                name="custom",
                mime_type="text/plain",
            )
        assert att.name == "custom"
        assert att.mimeType == "text/plain"


# =====================================================================
# Serializers
# =====================================================================


class TestAttachmentsToJson:
    """attachments_to_json()."""

    def test_single_item(self):
        att = Attachment(
            date="2025-01-01T00:00:00Z",
            link="abc",
            name="x",
            mimeType="text/plain",
            isExternal=False,
        )
        s = attachments_to_json([att])
        parsed = json.loads(s)
        assert isinstance(parsed, list) and len(parsed) == 1
        assert parsed[0]["link"] == "abc"

    def test_empty_list(self):
        assert attachments_to_json([]) == "[]"

    def test_preserves_unicode(self):
        att = Attachment(
            date="2025-01-01T00:00:00Z",
            link="abc",
            name="документ.pdf",
            mimeType="application/pdf",
            isExternal=False,
        )
        s = attachments_to_json([att])
        # ensure_ascii=False - Cyrillic letters appear raw.
        assert "документ.pdf" in s


class TestAttachmentsFromJson:
    """attachments_from_json()."""

    def test_none_returns_empty(self):
        assert attachments_from_json(None) == []

    def test_empty_string_returns_empty(self):
        assert attachments_from_json("") == []

    def test_nan_returns_empty(self):
        assert attachments_from_json(float("nan")) == []

    def test_empty_array_json(self):
        assert attachments_from_json("[]") == []

    def test_parses_list_string(self):
        payload = [
            {
                "date": "2025-01-01T00:00:00Z",
                "link": "abc",
                "name": "x",
                "mimeType": "text/plain",
                "isExternal": False,
            }
        ]
        result = attachments_from_json(json.dumps(payload))
        assert len(result) == 1
        assert isinstance(result[0], Attachment)
        assert result[0].link == "abc"

    def test_already_parsed_list(self):
        payload = [
            {
                "date": "2025-01-01T00:00:00Z",
                "link": "abc",
                "name": "x",
                "mimeType": "text/plain",
                "isExternal": False,
            }
        ]
        result = attachments_from_json(payload)
        assert len(result) == 1
        assert isinstance(result[0], Attachment)

    def test_non_list_raises(self):
        with pytest.raises(TypeError, match="JSON array"):
            attachments_from_json({"not": "a list"})

    def test_invalid_item_raises(self):
        with pytest.raises(ValidationError):
            attachments_from_json([{"date": "x", "link": "x"}])  # missing fields


# =====================================================================
# CalculatedAttribute
# =====================================================================


class TestCalculatedAttribute:
    """Schema entry for calculated columns."""

    def test_basic(self):
        a = CalculatedAttribute(
            attributeName="density",
            type="Double",
            expression="population / NULLIF(area_km2, 0)",
        )
        assert a.attributeName == "density"
        assert a.expression == "population / NULLIF(area_km2, 0)"
        assert (
            a.attribute_configuration_type
            == AttributeConfigurationType.CALCULATED.value
        )

    def test_column_name_auto_filled(self):
        a = CalculatedAttribute(
            attributeName="density", type="Double", expression="x"
        )
        assert a.columnName == "density"

    def test_column_name_explicit(self):
        a = CalculatedAttribute(
            attributeName="density",
            type="Double",
            expression="x",
            columnName="dens_col",
        )
        assert a.columnName == "dens_col"

    def test_extra_forbid(self):
        with pytest.raises(ValidationError):
            CalculatedAttribute(
                attributeName="x",
                type="Double",
                expression="y",
                unknown="z",
            )

    def test_finalize_marks_fields_set(self):
        a = CalculatedAttribute(
            attributeName="x", type="Double", expression="y"
        )
        assert {"attribute_configuration_type", "columnName"}.issubset(
            a.__pydantic_fields_set__
        )

    def test_with_alias_and_aggregation(self):
        a = CalculatedAttribute(
            attributeName="total",
            type="Double",
            expression="SUM(weight)",
            alias="Total weight",
            aggregation="Sum",
        )
        assert a.alias == "Total weight"
        # aggregation accepts string or enum value; we just check it's set.
        assert a.aggregation is not None


# =====================================================================
# SubType registry
# =====================================================================


class TestSubTypeRegistry:
    """SUB_TYPE_BUILDERS + register_sub_type."""

    def test_attachments_registered(self):
        assert "Attachments" in SUB_TYPE_BUILDERS
        builder = SUB_TYPE_BUILDERS["Attachments"]
        # builder == AttachmentsAttribute.from_field - must be callable.
        assert callable(builder)

    def test_register_requires_from_field(self):
        with pytest.raises(TypeError, match="from_field"):

            @register_sub_type("__test_no_from_field__")
            class BadClass:
                pass

    def test_register_attaches_builder(self):
        @register_sub_type("__test_ok__")
        class OkClass:
            @classmethod
            def from_field(cls, field_name, field_info):
                return cls()

        try:
            assert "__test_ok__" in SUB_TYPE_BUILDERS
            # Bound methods compare by __func__, not by identity (descriptor
            # protocol creates a fresh bound method on each attribute access).
            assert (
                SUB_TYPE_BUILDERS["__test_ok__"].__func__
                is OkClass.from_field.__func__
            )
        finally:
            # cleanup the test registry entry
            SUB_TYPE_BUILDERS.pop("__test_ok__", None)
