---
title: Catalog - Maps
module: evergis_tools.catalog.maps
---

# Maps

Import: `from evergis_tools.catalog import create_map, update_map, add_layer_to_map, remove_layer_from_map`

---

## create_map
Create new map (project) in EverGIS.

```python
from evergis_tools.catalog import create_map

map_info = create_map(
    client, "my_map",
    alias="My Map",
    description="Interactive dashboard",
    parent_path="john_doe/Projects",
    tags=["dashboard", "2024"],
)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `name` | required | Map system name like `"username.my_map"` |
| `alias` | `None` | Display name |
| `description` | `None` | Map description |
| `parent_path` | `None` | Catalog path for parent folder |
| `tags` | `None` | List of tags |
| `dashboard_configuration` | `None` | Dashboard config (stored as-is) |
| `edit_configuration` | `None` | Edit config (stored as-is) |

**Returns:** `ExtendedProjectInfoDc`

> **Note:** Raises `ResourceExists` (HTTP 409) if a resource with the same
> system name or alias already exists in the target folder. See [[Errors]].

---

## update_map
Update existing map configuration. None values preserve existing fields.

```python
from evergis_tools.catalog import update_map

update_map(client, "john_doe.my_map", alias="Updated Name", tags=["v2"])
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `name` | required | Map system name |
| `alias` | `None` | New display name (None = keep existing) |
| `description` | `None` | New description |
| `tags` | `None` | New tags |
| `dashboard_configuration` | `None` | New dashboard config |
| `edit_configuration` | `None` | New edit config |

**Returns:** `ExtendedProjectInfoDc`

---

## add_layer_to_map
Append a layer to a page in an existing map. Safe to re-run: if a layer with `layer_name` is already on the target page, nothing is added and the unchanged map info is returned.

```python
from evergis_tools.catalog import add_layer_to_map

add_layer_to_map(
    client, "john_doe.evg_map_features", "john_doe.evg_stations",
    page_id="page1",
    visible=True,
    prepend=True,
)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `map_name` | required | Map system name like `"john_doe.evg_map_features"` |
| `layer_name` | required | Full system name of the layer to append |
| `page_id` | `"page1"` | Page id inside the dashboard's `Pages` container; the value of `id` from the `children` of the `templateName="Pages"` node |
| `visible` | `True` | Initial visibility of the layer on the page (stored as `isVisible`) |
| `selectable` | `True` | Whether features of the layer are selectable |
| `parameters` | `None` | Optional `{"@param": "%filterName"}` mapping for layers wired to a dashboard filter |
| `prepend` | `True` | `True` puts the new layer at the top of the list (rendered above existing layers); `False` appends to the bottom |

**Returns:** `ExtendedProjectInfoDc` - updated map info, or the unchanged one if the layer was already present.

> **Note:** Persists via [[Catalog/Maps#update_map|update_map]], so it requires the map to already exist with a dict `dashboardConfiguration`.

**Raises:**
- `ValueError` if the map has no dashboard configuration to update.
- `ValueError` if `page_id` is not found in the dashboard.

---

## remove_layer_from_map
Remove a layer from a page in an existing map. Safe to re-run: if the layer is not on the page, nothing changes and the unchanged map info is returned.

```python
from evergis_tools.catalog import remove_layer_from_map

remove_layer_from_map(
    client, "john_doe.evg_map_features", "john_doe.evg_stations",
    page_id="page1",
)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `map_name` | required | Map system name |
| `layer_name` | required | Full system name of the layer to remove |
| `page_id` | `"page1"` | Page id inside the dashboard's `Pages` container |

**Returns:** `ExtendedProjectInfoDc` - updated map info, or the unchanged one if the layer (or the page, or the dashboard configuration) was not found.

> **Note:** Returns the unchanged map info without raising when the dashboard configuration is missing or the `page_id` is absent. Persists via [[Catalog/Maps#update_map|update_map]] only when a matching layer is actually removed.

---

## See Also
- [[Catalog/Catalog|Catalog]] - Overview
- [[Errors]] - `ResourceExists` on name/alias collision
