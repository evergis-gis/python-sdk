---
title: Attachments
module: evergis_tools.attribute_types.attachments
---

# Attachments

Typed support for the server-side `StringSubType.Attachments` column - a `Json`-typed attribute that the EverGIS UI renders as a file-list widget. This module fixes the on-wire JSON shape, gives builders for the three flavours of file reference (URL / catalog resource / local upload), and ships a `StringAttributeConfigurationDc` subclass for the schema entry. Import: `from evergis_tools.attribute_types import ...`

## Attachment

Pydantic model for one file reference inside an attachments column. Field order matches the wire format the UI plugin expects.

```python
from evergis_tools.attribute_types import Attachment

item = Attachment(
    date="2025-02-01T11:10:00.240878Z",
    link="42b7c984ddf94730a36aa4e16d2a04b3",
    name="spec.pdf",
    mimeType="application/pdf",
    isExternal=False,
)
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `date` | `str` | ISO-8601 UTC timestamp |
| `link` | `str` | Catalog `resourceId` (32-hex) when `isExternal=False`, otherwise an `http(s)://` URL |
| `name` | `str` | Display name shown in the UI |
| `mimeType` | `str` | MIME type used by the renderer to pick a preview |
| `isExternal` | `bool` | `True` -> external URL; `False` -> catalog file |

> **Note:** A `model_validator` cross-checks `isExternal` against `link`: a URL with `isExternal=False`, or a non-URL with `isExternal=True`, raises `ValueError` at construction time. Use the builders below to avoid mismatches.

## AttachmentsAttribute

`StringAttributeConfigurationDc` subclass that pre-fills the locked `(attributeConfigurationType=String, type=Json, subType=Attachments)` triplet. The instance is still a regular attribute-config, so it can be appended directly to `AttributesConfigurationDc.attributes` or handed to `add_layer_attribute`.

```python
from evergis_tools.attribute_types import AttachmentsAttribute
from evergis_tools.layers import add_layer_attribute

add_layer_attribute(
    client, "john_doe.evg_stations",
    AttachmentsAttribute(attributeName="docs", alias="Documents"),
)
```

**Key params:** `attributeName` (required), `alias`, plus any other `StringAttributeConfigurationDc` flag. `columnName` defaults to `attributeName` if omitted.

**Declarative use via `create_layer_from_schema`:**

```python
from pydantic import BaseModel, Field

class StationSchema(BaseModel):
    docs: list = Field(
        description="Documents",
        json_schema_extra={"sub_type": "Attachments"},
    )
```

`create_layer_from_schema` looks the `sub_type` up in `SUB_TYPE_BUILDERS` (filled by `@register_sub_type("Attachments")` on this class) and calls `AttachmentsAttribute.from_field(name, field_info)`, taking the EverGIS `alias` from Pydantic's `description`.

## Builders

All three builders return an `Attachment`; combine them in a list and feed it to [`attachments_to_json`](#serializers) before writing to a feature.

### attachment_from_url
Build an `Attachment` pointing at an external URL. `name` defaults to the URL-decoded last path segment, `mime_type` is guessed from that name and falls back to `application/octet-stream`.

```python
from evergis_tools.attribute_types import attachment_from_url

item = attachment_from_url("https://example.com/spec.pdf")
# Attachment(name="spec.pdf", mimeType="application/pdf", isExternal=True, ...)
```

### attachment_from_resource
Build an `Attachment` pointing at an existing catalog file. `identifier` is resolved via `evergis_tools.catalog.resources.resolve_resource`, so a path, resource ID, or system name all work.

```python
from evergis_tools.attribute_types import attachment_from_resource

item = attachment_from_resource(
    client, "john_doe/EverGIS Resources/python/features/results/spec.pdf",
)
```

`name` defaults to the resource's `name`; `mime_type` is guessed from that name.

### attachment_from_file
Upload a local file via `evergis_tools.catalog.files.upload_file` and return an `Attachment` pointing at the new catalog entry. Either `parent_id` or `parent_path` must be supplied (enforced by `upload_file`).

```python
from evergis_tools.attribute_types import attachment_from_file

item = attachment_from_file(
    client, "report.pdf",
    parent_path="john_doe/EverGIS Resources/python/features/results",
)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | Authenticated `evergis_api.Client` |
| `file_path` | required | Local path to upload |
| `parent_id` / `parent_path` | one required | Target folder in the catalog |
| `name` | basename of `file_path` | Display name on the wire |
| `mime_type` | guessed from `name` | Explicit override |
| `rewrite` | `True` | Replace an existing file with the same name |
| `date` | now (UTC) | Override the recorded timestamp |

## Serializers

### attachments_to_json
Serialize a sequence of `Attachment` into the JSON string stored in a feature attribute.

```python
from evergis_tools.attribute_types import attachments_to_json

gdf.loc[idx, "docs"] = attachments_to_json([item1, item2])
```

**Returns:** `str` - JSON array, `ensure_ascii=False` (Cyrillic file names stay readable).

### attachments_from_json
Parse an attachments value back into `list[Attachment]`. Accepts a JSON string, an already-parsed list/tuple, or a null-ish value (`None`, `""`, pandas `NaN`) which produce `[]`. A non-empty JSON string is parsed via `json.loads` and each item is validated through `Attachment.model_validate`.

```python
from evergis_tools.attribute_types import attachments_from_json

for item in attachments_from_json(feature["docs"]):
    print(item.name, item.link, item.isExternal)
```

**Raises:** `TypeError` if the input is neither a JSON string nor a list/tuple; `pydantic.ValidationError` per-item if any entry violates the `Attachment` shape (e.g. URL/`isExternal` mismatch).

## Key Behaviors

- **Wire format is opaque to the server.** EverGIS stores the value as `type=Json` and never inspects it; the `subType=Attachments` flag only tells the UI which widget to render. Anything the UI does not recognise is silently ignored, so always go through `attachments_to_json` rather than hand-rolling the payload.
- **`attachment_from_file` uploads first, then returns.** The builder calls `upload_file(rewrite=rewrite)` (default `rewrite=True`) synchronously and uses the returned `CatalogResourceDc.resourceId` as `link`. Any exception raised by `upload_file` propagates out (e.g. `FileNotFoundError` if the local path is missing, `ValueError` if neither `parent_id` nor `parent_path` is given) and no `Attachment` is produced.
- **Order is preserved.** `attachments_to_json` iterates the input as-is; the UI renders the list in that order, so callers control display ordering by ordering the input list.
- **Locked literals survive `model_dump(exclude_unset=True)`.** `AttachmentsAttribute._finalize` adds the Python field names `type`, `sub_type`, `attribute_configuration_type`, `is_nullable`, and `columnName` to `__pydantic_fields_set__`. Without this the generated client (which serializes with `exclude_unset=True` into an un-discriminated `Union`) would drop the locked triplet (`attributeConfigurationType=String`, `type=Json`, `subType=Attachments`) and the server would create a plain string column.
- **`columnName` defaults to `attributeName`.** EverGIS routes the value to the physical column by `columnName`; leaving it unset crashes inserts with a 500. The finaliser fills it in if the caller omits it.
- **Registry hook.** `@register_sub_type("Attachments")` adds `AttachmentsAttribute.from_field` to `SUB_TYPE_BUILDERS`, which is how `create_layer_from_schema` discovers the typed builder without importing it directly. See `_registry.py` for the contract a new sub-type class must satisfy.

## See Also
- [[Attributes]] - generic attribute CRUD (`add_layer_attribute`, `remove_layer_attribute`)
- [[AttributeTypes/Calculated|Calculated]] - sibling typed-attribute helper
- [[AttributeTypes/AttributeTypes|Attribute Types]] - hub page and registry overview
- [[Catalog/Files|Files]] - `upload_file` used by `attachment_from_file`
