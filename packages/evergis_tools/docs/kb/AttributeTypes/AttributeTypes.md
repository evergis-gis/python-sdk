---
title: Attribute Types
---

# Attribute Types

Typed helpers for the special `StringSubType` / `AttributeConfigurationType` combinations that EverGIS treats differently from plain scalar attributes - file lists, EQL-driven computed columns, and similar specialised classes. Each helper is a pre-configured `AttributeConfigurationDc` subclass ready to hand to [[Layers/Update|add_layer_attribute]] or to include in `AttributesConfigurationDc.attributes` at layer-create time. Helpers that self-register via `@register_sub_type(...)` (currently `AttachmentsAttribute`) are also reachable from a Pydantic field declaration via [[Layers/Update|create_layer_from_schema]]; `CalculatedAttribute` does not register and is used only by direct instantiation.

Import: `from evergis_tools.attribute_types import ...`

## Sections

- [[AttributeTypes/Attachments|Attachments]] - file-list column (`StringSubType.Attachments`), with builders for external URLs, catalog resources, and local uploads
- [[AttributeTypes/Calculated|Calculated]] - server-side computed column (`AttributeConfigurationType.Calculated`) driven by an EQL `expression`

## Registry

`SUB_TYPE_BUILDERS: Dict[str, SubTypeBuilder]` maps a `StringSubType` name to a callable that builds the corresponding `AttributeConfigurationDc` from a Pydantic `(field_name, field_info)` pair. `create_layer_from_schema` walks the schema, and for every field with `Field(json_schema_extra={"sub_type": "..."})` looks the builder up here and calls it - so adding a new sub-type is a single new file under `attribute_types/`, no edits to `layers/create.py`.

`register_sub_type(name)` is the class decorator that wires a typed-attribute class into the registry. The class must expose a `from_field(field_name, field_info)` classmethod - the decorator raises `TypeError` at import time otherwise.

```python
from evergis_api.schemas import StringAttributeConfigurationDc
from evergis_tools.attribute_types import register_sub_type

@register_sub_type("Image")
class ImageAttribute(StringAttributeConfigurationDc):
    @classmethod
    def from_field(cls, field_name, field_info):
        return cls(
            attributeName=field_name,
            alias=field_info.description,
            # ... locked type/subType triplet, defaults, etc.
        )
```

After import, `create_layer_from_schema` will dispatch any `sub_type="Image"` field to `ImageAttribute.from_field` automatically.

## See Also

- [[Attributes]] - generic attribute CRUD (`add_layer_attribute`, `remove_layer_attribute`, type conversion)
- [[Layers/Update|Layers Update]] - where these typed classes are consumed (`add_layer_attribute`, `create_layer_from_schema`)
- [[Home]]
