---
title: Layers - Read
module: evergis_tools.layers.read
---

# Layer Reading

Import: `from evergis_tools.layers import get_layer_configuration, get_layer_schema, create_identity_mapping_from_layer`

---

## get_layer_configuration

Get complete layer configuration: EQL, parameters, style, card, edit config, attributes.

```python
from evergis_tools.layers import get_layer_configuration

config = get_layer_configuration(client, "john_doe.my_layer")

print(config.eql)                              # EQL query
print(config.eqlParameters)                    # @parameters
print(config.clientStyle)                      # Mapbox GL style
print(config.attributesConfiguration)          # Attributes config
print(config.cardConfiguration)                # Popup card
print(config.editConfiguration)                # Edit form
```

**Returns:** `QueryLayerServiceConfigurationDc`

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `layer_name` | required | Layer name (with or without username prefix) |
| `log` | `True` | Enable logging |

**Notes:**
- Only works with **QueryLayerService** layers - raises `ValueError` for other types
- Layer type detected via `configuration.layerType` field
- Geometry type auto-normalized (API returns lowercase, converted to enum)
- Used as first step in all update workflows

---

## get_layer_schema

Get layer attribute schema (attribute names, types, geometry info).

```python
from evergis_tools.layers import get_layer_schema

schema = get_layer_schema(client, "john_doe.my_layer")

if schema:
    print(f"ID: {schema.idAttribute}")
    print(f"Geometry: {schema.geometryAttribute}")
    for attr in schema.attributes:
        print(f"  {attr.attributeName}: {attr.type}, editable={attr.isEditable}")
```

**Returns:** `Optional[AttributesConfigurationDc]` - `None` if layer has no schema definition.

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `layer_name` | required | Layer name |
| `log` | `True` | Enable logging |

**Notes:**
- Has fallback: tries API client first, then raw JSON parsing on validation error
- Returns `None` (not exception) if `layerDefinition` not found
- Lighter than `get_layer_configuration` - only attributes, not full config

---

## create_identity_mapping_from_layer

Create `{field: field}` identity mapping for all layer attributes. Used for export functions.

```python
from evergis_tools.layers import create_identity_mapping_from_layer

mapping = create_identity_mapping_from_layer(client, "john_doe.cities")
# {'gid': 'gid', 'name': 'name', 'population': 'population', 'geometry': 'geometry'}

# Exclude geometry
mapping = create_identity_mapping_from_layer(client, "john_doe.cities", exclude_geometry=True)
# {'gid': 'gid', 'name': 'name', 'population': 'population'}
```

**Returns:** `Dict[str, str]`

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `layer_name` | required | Layer name |
| `exclude_geometry` | `False` | Exclude geometry field from mapping |
| `log` | `True` | Enable logging |

**Notes:**
- Raises `ValueError` if layer has no attributes
- Geometry field detected from `schema.geometryAttribute` (default `"geometry"`)
- Useful with `tasks.export_tools` functions that require attribute mapping

---

## See Also
- [[Layers/Create]] - Create layers
- [[Layers/Update]] - Modify layer configuration
- [[Patterns - StringFormat]] - Format attributes
