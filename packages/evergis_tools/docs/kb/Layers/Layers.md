---
title: Layers
module: evergis_tools.layers
---

# Layers

CRUD operations for EverGIS layers. Import: `from evergis_tools.layers import ...`

## Sections
- [[Layers/Create]] - `gdf_to_layer`, `create_layer_from_schema`, `create_query_layer`
- [[Layers/Read]] - `get_layer_configuration`, `get_layer_schema`, `create_identity_mapping_from_layer`
- [[Layers/Update]] - `update_layer_configuration`, `update_layer_eql`, `update_layer_style`, `update_layer_attributes`, `update_layer_card`, `update_layer_edit_config`

## Typical Workflow

```python
from evergis_tools.layers import *

# 1. Create
result = gdf_to_layer(client, gdf, "my_layer", geometry_type="Point", overwrite=True)

# 2. Read config
config = get_layer_configuration(client, "my_layer")

# 3. Update style
update_layer_style(client, "my_layer", {"items": [{"type": "circle", "paint": {...}}]})

# 4. Update attributes (aliases, formatting)
attrs = config.attributesConfiguration
for attr in attrs.attributes:
    if attr.attributeName == "price":
        attr.alias = "Price"
        attr.stringFormat = AttributeFormatConfigurationDc(format="#,#", unitsLabel=" руб.")
update_layer_attributes(client, "my_layer", attrs)
```

## Key Behaviors

- **Name normalization** - Cyrillic auto-transliterated, lowercased, snake_case. `"Мои Данные"` → `"username.moi_dannye"`
- **Auto-folder creation** - `parent_path` creates missing folders automatically
- **gid attribute** - mandatory `gid` added if missing; PK constraints and autoincrement are applied server-side
- **QueryLayerService only** - `get_layer_configuration` works only with QueryLayerService layers

## Types

### OverwriteMode
`Union[bool, Literal["cascade"]]` - see [[Patterns - Overwrite]]

## See Also
- [[Features]] - Add features to layers
- [[EQL]] - EQL query language (used in `create_query_layer`, `update_layer_eql`)
- [[Patterns - Overwrite]]
- [[Patterns - StringFormat]]
- [[Patterns - Chunking]]
