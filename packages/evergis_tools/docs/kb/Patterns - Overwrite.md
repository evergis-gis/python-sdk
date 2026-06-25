---
title: Patterns - Overwrite
---

# Overwrite Modes

Layer creation functions accept `overwrite` parameter:

| Value | Behavior |
|-------|----------|
| `False` (default) | Error if layer exists |
| `True` | Delete layer and recreate |
| `"cascade"` | Delete layer + table + all dependencies |

```python
# Safe - error if exists
gdf_to_layer(client, gdf, "my_layer", overwrite=False)

# Recreate layer only
gdf_to_layer(client, gdf, "my_layer", overwrite=True)

# Full cleanup including table and dependent layers
gdf_to_layer(client, gdf, "my_layer", overwrite="cascade")
```

Type: `OverwriteMode = Union[bool, Literal["cascade"]]`
