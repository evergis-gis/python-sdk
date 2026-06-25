---
title: Layers - Update
module: evergis_tools.layers.update
---

# Layer Update

Import: `from evergis_tools.layers import update_layer_configuration, update_layer_eql, update_layer_style, update_layer_attributes, add_layer_attribute, delete_layer_attribute, update_layer_attribute, update_layer_card, update_layer_edit_config, declare_eql_parameter`

All update functions follow the same pattern: read current config → modify → patch. They only affect the specified fields, preserving everything else.

---

## update_layer_configuration

Replace entire layer configuration at once.

```python
from evergis_tools.layers import get_layer_configuration, update_layer_configuration

config = get_layer_configuration(client, "john_doe.my_layer")
config.alias = "New Name"
config.description = "Updated layer"
update_layer_configuration(client, "john_doe.my_layer", config)
```

**Params:** `client`, `layer_name`, `configuration: QueryLayerServiceConfigurationDc`, `log=True`

**Returns:** `Any` - API response with updated layer info.

**Notes:**
- Overrides `config.name` to match `layer_name` (prevents mismatch)
- Removes None values before sending to API

---

## update_layer_eql

Update EQL query, parameters, and/or condition selectively.

```python
from evergis_tools.layers import update_layer_eql

# Update query + parameters
update_layer_eql(client, "john_doe.my_layer",
    eql_query="SELECT * FROM john_doe.table WHERE status = @status",
    eql_parameters={"@status": "active"},
)

# Update only parameters (query unchanged)
update_layer_eql(client, "john_doe.my_layer",
    eql_parameters={"@status": "inactive"},
)

# Add filter condition
update_layer_eql(client, "john_doe.my_layer",
    condition="price > 0",
)

# Clear parameters
update_layer_eql(client, "john_doe.my_layer", eql_parameters={})
```

**Params:** `client`, `layer_name`, `eql_query=None`, `eql_parameters=None`, `condition=None`, `log=True`

**Returns:** `Any` - API response with updated layer info.

> **Requirement:** At least one of `eql_query`, `eql_parameters`, `condition` must be provided - raises `ValueError` otherwise.

EQL parameters auto-converted: `{"@status": "active"}` → `QueryLayerServiceEqlParameterConfigurationDc(type=String, default="active")`.

---

## declare_eql_parameter

Build an EQL parameter declaration with explicit type and default for `update_layer_eql`.

```python
from evergis_tools.layers import declare_eql_parameter, update_layer_eql

update_layer_eql(client, "john_doe.my_layer",
    eql_query=eql_with_isset_expansions,
    eql_parameters={
        "@category":  declare_eql_parameter("String"),
        "@min_conf":  declare_eql_parameter("Double", default=0.5),
        "@name_like": declare_eql_parameter("String"),
    },
)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `type_name` | required | AttributeType name: `"String"`, `"Double"`, `"Int64"`, `"Boolean"`, `"DateTime"` |
| `default` | `None` | Default value; for `type_name == "String"` a `None` becomes `""` (the String "not set" sentinel) |
| `alias` | `""` | UI alias |
| `description` | `""` | UI description |
| `is_array` | `False` | `True` for list-typed parameters (used with `IN (SELECT unnest(@arr))` patterns) |

`default`, `alias`, `description`, and `is_array` are keyword-only.

**Returns:** `QueryLayerServiceEqlParameterConfigurationDc`

> **Note:** Without a triggering default, `default` is `""` for `String` and `None` for everything else - the value the server treats as "not set", so a matching `${isset:@x, {...}}` expansion does not inject a filter when the client omits the parameter. With a default, the server uses it whenever the client omits the parameter.

---

## update_layer_style

Update Mapbox GL style specification.

```python
from evergis_tools.layers import update_layer_style

# Simple circle style
style = {
    "items": [{
        "type": "circle",
        "paint": {
            "circle-color": "#ff0000",
            "circle-radius": 5,
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 1.5,
        },
    }]
}
update_layer_style(client, "john_doe.my_layer", style)
```

**Conditional coloring:**
```python
style = {
    "items": [{
        "type": "circle",
        "paint": {
            "circle-color": [
                "match", ["get", "type"],
                "office", "#4CAF50",
                "retail", "#FF9800",
                "#9E9E9E",  # default
            ],
            "circle-radius": 6,
        },
    }]
}
update_layer_style(client, "john_doe.my_layer", style)
```

**Params:** `client`, `layer_name`, `client_style: Dict`, `log=True`

**Returns:** `Any` - API response with updated layer info.

---

## update_layer_attributes

Update attribute metadata: aliases, editability, display, [[Patterns - StringFormat|stringFormat]].

```python
from evergis_tools.layers import get_layer_configuration, update_layer_attributes
from evergis_api.schemas import AttributeFormatConfigurationDc

config = get_layer_configuration(client, "john_doe.my_layer")
attrs = config.attributesConfiguration

for attr in attrs.attributes:
    if attr.attributeName == "status":
        attr.alias = "Status"
        attr.isEditable = False
    if attr.attributeName == "price":
        attr.stringFormat = AttributeFormatConfigurationDc(
            format="#,#", splitDigitGroup=True,
            rounding=0, unitsLabel=" руб.", culture="ru-RU",
        )

update_layer_attributes(client, "john_doe.my_layer", attrs)
```

**Params:** `client`, `layer_name`, `attributes_configuration: AttributesConfigurationDc`, `log=True`

**Returns:** `Any` - API response with updated layer info.

**What you can modify per attribute:**
- `alias` - human-readable name
- `isEditable` - allow/deny editing
- `isDisplayed` - show/hide in queries
- `stringFormat` - display formatting (see [[Patterns - StringFormat]])
- `description` - attribute description

---

## add_layer_attribute

Append a single attribute to a layer's schema (server creates the backing physical column).

```python
from evergis_api.schemas import AttributeConfigurationDc
from evergis_tools.layers import add_layer_attribute

add_layer_attribute(
    client, "john_doe.my_layer",
    AttributeConfigurationDc(
        attributeName="note", columnName="note",
        type="String", alias="Inspector note",
    ),
)
```

**Params:** `client`, `layer_name`, `attribute: AttributeConfigurationDc`, `log=True`

**Returns:** `Any` - response from the underlying `PATCH /layers` call.

> **Raises:** `ValueError` if the layer already has an attribute with the same `attributeName`.

> **Note:** Reads the current `attributesConfiguration`, appends `attribute`, and calls `update_layer_attributes` to persist. Works with subtype-aware subclasses such as [[AttributeTypes/Attachments|AttachmentsAttribute]] - subclass-only fields like `subType` are preserved.

---

## delete_layer_attribute

Remove a single attribute from a layer's schema (server drops the backing physical column).

```python
from evergis_tools.layers import delete_layer_attribute

delete_layer_attribute(client, "john_doe.my_layer", "note")
```

**Params:** `client`, `layer_name`, `attribute_name: str`, `log=True`

**Returns:** `Any` - response from the underlying `PATCH /layers` call.

> **Raises:** `ValueError` if no attribute with that name exists, or if `attribute_name` equals the layer's `idAttribute` (it backs the primary key and feature ids).

---

## update_layer_attribute

Replace a single attribute in a layer's schema by name, swapping it whole.

```python
from evergis_api.schemas import AttributeFormatConfigurationDc
from evergis_tools.layers import get_layer_configuration, update_layer_attribute

cfg = get_layer_configuration(client, "john_doe.my_layer", log=False)
attr = next(a for a in cfg.attributesConfiguration.attributes
            if a.attributeName == "density")
attr.alias = "Population density"
attr.stringFormat = AttributeFormatConfigurationDc(format="#,#.00")
update_layer_attribute(client, "john_doe.my_layer", attr)
```

Promote a plain attribute to a typed one (e.g. [[AttributeTypes/Calculated|CalculatedAttribute]]):

```python
from evergis_tools.attribute_types import CalculatedAttribute
from evergis_tools.layers import update_layer_attribute

update_layer_attribute(client, "john_doe.my_layer",
    CalculatedAttribute(
        attributeName="density", columnName="density",
        type="Double",
        expression="population / NULLIF(area_km2, 0)",
        alias="Population density",
    ),
)
```

**Params:** `client`, `layer_name`, `attribute: AttributeConfigurationDc`, `log=True`

**Returns:** `Any` - response from the underlying `PATCH /layers` call.

> **Raises:** `ValueError` if no attribute with `attribute.attributeName` exists - use `add_layer_attribute` to create it instead.

> **Warning:** The new `attribute` is dropped in verbatim - fields you do not set fall back to class defaults (often `None`), not to the previous values. Read the current attribute first for a partial change (see the first example above).

---

## update_layer_card

Update popup card displayed on feature click.

```python
from evergis_tools.layers import update_layer_card

card = {
    "header": {
        "templateName": "Icon",
        "children": [
            {"id": "title", "type": "attributeValue", "attributeName": "name"},
            {"id": "description", "type": "attributeValue", "attributeName": "address"},
        ],
    },
    "children": [{
        "id": "pages", "templateName": "Pages",
        "children": [{
            "id": "page1", "templateName": "ContainersGroup",
            "children": [{
                "id": "info", "templateName": "TwoColumn",
                "options": {"attributes": ["status", "price", "area"]},
                "children": [
                    {"id": "alias", "type": "attributeAlias"},
                    {"id": "value", "type": "attributeValue"},
                ],
            }],
        }],
    }],
    "dataSources": [],
}
update_layer_card(client, "john_doe.my_layer", card)
```

**Params:** `client`, `layer_name`, `card_configuration: Dict`, `log=True`

**Returns:** `Any` - API response with updated layer info.

**Common templates:** `Icon` (header), `Pages`, `ContainersGroup`, `TwoColumn`, `Edit`

---

## update_layer_edit_config

Update feature edit form with controls (dropdowns, text inputs, etc.).

```python
from evergis_tools.layers import update_layer_edit_config

edit_config = {
    "children": [{
        "id": "pages", "templateName": "Pages",
        "children": [{
            "id": "page1", "templateName": "ContainersGroup",
            "children": [{
                "id": "status_edit", "templateName": "Edit",
                "children": [
                    {"id": "alias", "type": "attributeAlias", "attributeName": "status"},
                    {
                        "id": "value", "type": "control", "attributeName": "status",
                        "options": {
                            "control": {"type": "dropdown", "targetAttributeName": "status"},
                            "relatedDataSource": "Statuses Lookup",
                        },
                    },
                ],
            }],
        }],
    }],
}
update_layer_edit_config(client, "john_doe.my_layer", edit_config)
```

**Params:** `client`, `layer_name`, `edit_configuration: Dict`, `log=True`

**Returns:** `Any` - API response with updated layer info.

---

## See Also
- [[Layers/Read]] - Read configuration before updating
- [[Layers/Create]] - Create layers
- [[EQL]] - EQL query language and parameters
- [[Patterns - StringFormat]] - Attribute formatting
- [[Patterns - Overwrite]]
