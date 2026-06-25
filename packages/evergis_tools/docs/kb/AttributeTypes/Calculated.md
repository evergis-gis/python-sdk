---
title: Calculated
module: evergis_tools.attribute_types.calculated
---

# Calculated

Schema entry for a server-side computed column driven by an EQL `expression`. Import: `from evergis_tools.attribute_types import CalculatedAttribute`

## CalculatedAttribute

Subclass of `CalculatedAttributeConfigurationDc` that pre-fills `attributeConfigurationType=Calculated` and defaults `columnName` to `attributeName`, so the caller only supplies `attributeName`, `type`, and `expression` (plus an optional `alias` / `aggregation` / standard flags).

```python
from evergis_tools.attribute_types import CalculatedAttribute
from evergis_tools.layers import add_layer_attribute

add_layer_attribute(
    client, "john_doe.my_layer",
    CalculatedAttribute(
        attributeName="density",
        type="Double",
        expression="population / NULLIF(area_km2, 0)",
        alias="Population density",
    ),
)
```

The instance still *is* a `CalculatedAttributeConfigurationDc`, so it can be appended directly to `AttributesConfigurationDc.attributes`.

**Key params:**

| Param | Default | Description |
|-------|---------|-------------|
| `attributeName` | required | Attribute name in the layer schema |
| `type` | `None` | `AttributeType` of the computed value (`Double`, `Int64`, `String`, ...) |
| `expression` | `None` | EQL expression evaluated per feature |
| `columnName` | `attributeName` | Physical column backing the value; auto-filled by the validator |
| `alias` | `None` | Human-friendly label shown in the UI |
| `aggregation` | `None` | `AggregationFunction` for expressions that aggregate child rows (e.g. `SUM(weight)` over a referenced layer); leave `None` for row-wise expressions |
| `isEditable` / `isDisplayed` | `None` | Standard `AttributeConfigurationDc` flags |
| `description`, `stringFormat`, `icon`, `referenceId`, `layerReferenceId`, `clientData`, `attributeSelectorType` | `None` | Inherited from `AttributeConfigurationDc` |

`attributeConfigurationType` is locked to `AttributeConfigurationType.CALCULATED` - do not override it.

**Returns:** an `AttributeConfigurationDc` subclass instance, ready to pass to [[Layers/Update|add_layer_attribute]] or to include in `AttributesConfigurationDc.attributes` at layer-create time.

> **Warning:** A true *virtual* (compute-on-read) mode is not exposed by the API today. `PATCH /layers/{name}` with a calculated attribute and no `columnName` returns HTTP 400, and `POST /layers` quietly fills `columnName=attributeName` itself - turning the would-be virtual attribute into a persisted column. This helper picks the persisted path on purpose so both endpoints behave the same way. The value is materialised into a physical column and can be queried and indexed like any other attribute.

## Key Behaviors

- **`columnName` auto-fill.** The `model_validator` sets `columnName = attributeName` when the caller leaves it `None`. Both the discriminator (`attributeConfigurationType`) and the defaulted `columnName` are then force-marked in `__pydantic_fields_set__` so they survive `model_dump(exclude_unset=True)` - the generated client uses that mode for PATCH payloads, and the parent `attributes` field is an un-discriminated `Union`, so unmarked defaults would silently drop out.
- **Expression language is EQL.** See [[EQL]] for available functions and operators. `NULLIF`, `ST_Area(geometry)`, arithmetic, and string functions all work the same way as in query layers.
- **Row-wise vs aggregating.** Leave `aggregation=None` for per-feature expressions. Set it (`Sum`, `Avg`, `Count`, ...) only when the expression rolls up rows from a referenced layer; the server uses the `AggregationFunction` to decide how to fold child rows into the parent.
- **Model config.** `extra="forbid"` rejects unknown keyword args at construction time, `validate_assignment=True` re-validates on every attribute write, `use_enum_values=True` serialises enums as their string value, and `populate_by_name=True` accepts both `attributeConfigurationType` (alias) and `attribute_configuration_type` (field name).

## See Also

- [[AttributeTypes/Attachments|Attachments]] - file-upload attribute via the same registry
- [[AttributeTypes/AttributeTypes|Attribute Types]] - hub page for typed attribute helpers
- [[Attributes]] - generic attribute utilities (cleaning, type conversion, validation)
- [[EQL]] - expression language reference
