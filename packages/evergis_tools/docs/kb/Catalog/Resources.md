---
title: Catalog - Resources
module: evergis_tools.catalog.resources
---

# Resources

Import: `from evergis_tools.catalog import resolve_resource, get_resources, iter_resources, iter_tags, rename_resource, update_resource_metadata, get_parents, create_link, resolve_parent_id, resolve_target_layer_parent`

---

## resolve_resource
Universal resource resolver - auto-detects identifier type.

```python
from evergis_tools.catalog import resolve_resource

resource = resolve_resource(client, "john_doe/Projects/Data/Layer")           # catalog path (slash)
resource = resolve_resource(client, "john_doe:Projects/Data/Layer")           # legacy colon form
resource = resolve_resource(client, "efb02c4d89144f9792a94af22831f45d") # resource ID (32 hex)
layer = resolve_resource(client, "john_doe.my_layer", resource_type="Layer")  # system name
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `identifier` | required | Catalog path, 32-hex resource ID, or system name |
| `resource_type` | `None` | Disambiguates a system-name lookup; `"Layer"` / `"Table"` / `"Map"` etc. or a `CatalogResourceType` |

**Returns:** `CatalogResourceDc` - full resource metadata (resourceId, systemName, type, parentId, etc.)

> **Note:** Detection: identifier containing `:` or `/` (and not a 32-hex id) is a catalog path; a 32-hex string is a resource ID; everything else is a system name. The path format is `owner/Folder/Name` (slash separator). The legacy `owner:Folder/Name` colon form is still accepted and normalized to the slash form before the request (only the first `:` is replaced). Reserved characters in the path (`&`, `#`, `?`, ...) are percent-encoded; `/` is kept as the separator.

> **Note:** Since the v3 catalog update a single `GET /resources/{resourceId}` resolves both a 32-hex id and a catalog path - the dedicated by-path and by-system-name endpoints are gone. Path and resource-id lookups resolve one resource directly. A system-name lookup uses `post_get_all(systemNames=[...])`, which returns BOTH a physical Layer and its backing Table when they share a `systemName`; pass `resource_type=` to pick one. Without `resource_type`, the first item is returned and the order is server-defined.

> **Warning:** Raises `ResourceNotFound` (importable from `evergis_tools`) when the resource does not exist - a 404, or an empty result set for a system-name lookup. Raises `ValueError` only for invalid input (empty / non-string identifier), a system name with no item of the requested `resource_type`, or a resolved item without a resourceId. Any other server failure (5xx / 403) propagates as `ApiClientError` - it is never masked as "not found". `ResourceNotFound` is an `ApiClientError` subclass, so `is_not_found(exc)` recognizes it.

---

## get_resources
Get filtered list of catalog resources with flexible filtering.

```python
from evergis_tools.catalog import get_resources, ResourceTypeFilter

resources = get_resources(
    client,
    resource_types=[ResourceTypeFilter.LAYER],
    filter_text="realty*",
    owner_filter="My",
    limit=50,
)
for r in resources.items:
    print(f"{r.systemName}: {r.type}")
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `filter_text` | `None` | Wildcard search (`*` supported) |
| `owner_filter` | `None` | `"My"`, `"Shared"`, `"Public"` or AccessMode enum |
| `resource_types` | `None` | List of ResourceTypeFilter |
| `catalog_resource_types` | `None` | List of CatalogResourceType |
| `geometry_types` | `None` | List of GeometryType |
| `parent` | `None` | Parent resource ID or catalog path |
| `subtypes` | `None` | List of ResourceSubTypeFilter |
| `system_names` | `None` | List of system names |
| `acl_filter` | `None` | Dict of role→permission |
| `limit` | `100` | Page size |
| `offset` | `None` | Pagination offset |
| `order_by` | `None` | Sort fields |
| `tags_filter` | `None` | TagsFilterDc or dict |

**Returns:** `PagedResourcesListDc` - paged result with `.items` list.

> **Note:** Accepts both enum values and strings for all filter params.

---

## iter_resources
Stream every resource matching the filters, paging through the API automatically.

```python
from evergis_tools.catalog import iter_resources

for r in iter_resources(client, owner_filter="My", resource_types=["Layer"]):
    print(f"{r.systemName}: {r.type}")
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `filter_text` | `None` | Wildcard search (`*` supported) |
| `owner_filter` | `"My"` | `"My"`, `"Shared"`, `"Public"` or AccessMode enum (server rejects null) |
| `resource_types` | `None` | List of ResourceTypeFilter |
| `catalog_resource_types` | `None` | List of CatalogResourceType |
| `geometry_types` | `None` | List of GeometryType |
| `parent` | `None` | Parent resource ID or catalog path |
| `subtypes` | `None` | List of ResourceSubTypeFilter |
| `system_names` | `None` | List of system names |
| `acl_filter` | `None` | Dict of role to permission |
| `order_by` | `None` | Sort fields |
| `tags_filter` | `None` | TagsFilterDc or dict |
| `page_size` | `1000` | Items per request |

**Returns:** `Iterator[CatalogResourceDc]` - yields each resource across all pages.

> **Note:** Same filters as [[#get_resources]]; use `get_resources` when a single page is enough. Paging stops when a page returns fewer than `page_size` items.

---

## iter_tags
Stream every tag the user can see, paging through the API automatically.

```python
from evergis_tools.catalog import iter_tags

tags = list(iter_tags(client, filter="proj"))
```

**Key params:** `client`, `filter=None` (server-side substring filter), `page_size=1000`

**Returns:** `Iterator[str]` - yields each tag across all pages.

---

## rename_resource
Rename and/or move a resource.

```python
from evergis_tools.catalog import rename_resource

renamed = rename_resource(client, "john_doe.my_layer", new_name="My Layer")
moved = rename_resource(client, "john_doe.my_layer", new_parent="john_doe/Projects/Archive", rewrite=True)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `identifier` | required | Resource to rename - catalog path, resource ID, or system name |
| `new_name` | `None` | New display name (in-place rename) |
| `new_parent` | `None` | New parent location - catalog path or resource ID; missing folders are created |
| `rewrite` | `False` | Overwrite an existing resource with the new name at the target; only honored on the move |

**Returns:** `CatalogResourceDc` - updated resource.

> **Warning:** At least one of `new_name` or `new_parent` is required; raises `ValueError` if both are `None`. Raises `ResourceNotFound` if the source or target cannot be resolved.

> **Note:** `new_name` only patches in place via `patch_resource`. Setting `new_parent` moves via `move_resource` (only when the target parent differs from the current one), then patches for the rename if `new_name` was also given. The rename carries existing `description` / `tags` / `icon` forward so the server does not clear them.

---

## update_resource_metadata
Patch a resource's description, tags, and/or icon.

```python
from evergis_tools.catalog import update_resource_metadata

updated = update_resource_metadata(client, "john_doe.my_layer", description="Charging stations", tags=["poi", "energy"])
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `identifier` | required | Resource to update - catalog path, resource ID, or system name |
| `description` | `None` | New description; `None` keeps existing, `""` clears |
| `tags` | `None` | New tag list; `None` keeps existing, `[]` clears |
| `icon` | `None` | New icon URI / id; `None` keeps existing, `""` clears |

**Returns:** `CatalogResourceDc` - updated resource.

> **Note:** Wraps `patch_resource`, which clears any field omitted from the body, so the helper reads the current resource and only overrides the fields you pass. For renaming, use [[#rename_resource]].

---

## get_parents
Return the chain of ancestor folders for a resource.

```python
from evergis_tools.catalog import get_parents

for p in get_parents(client, "john_doe.my_layer"):
    print(p.name, p.path, p.resourceId)
```

**Key params:** `client`, `identifier: str` (catalog path, resource ID, or system name)

**Returns:** `list[ResourceParentDc]` - ancestors from catalog root down to the immediate parent (`name`, `path`, `resourceId`). Empty list if the resource sits at the root; the resource itself is not included.

---

## create_link
Create a symlink (shortcut) to a resource.

```python
from evergis_tools.catalog import create_link

link = create_link(client, "john_doe.realty", parent_path="john_doe/Projects/Links")
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `target` | required | Target resource - catalog path, resource ID, or system name |
| `parent_path` | `None` | Catalog path for the link location (auto-creates missing folders) |
| `name` | `None` | Link display name (defaults to the target resource's systemName) |
| `description` | `None` | Link description |
| `tags` | `None` | List of tags |
| `log` | `True` | Enable logging |

**Returns:** `CatalogResourceDc` - the created link.

> **Warning:** Raises `ResourceNotFound` if `target` cannot be resolved.

---

## resolve_parent_id
Resolve parent folder ID from direct ID or catalog path. Mutually exclusive params.

```python
from evergis_tools.catalog import resolve_parent_id

parent_id = resolve_parent_id(client, parent_path="john_doe/Projects/Data")
# or
parent_id = resolve_parent_id(client, parent_id="efb02c4d...")
```

**Key params:** `client`, `parent_id=None`, `parent_path=None`

**Returns:** `str` - resolved resource ID.

> **Warning:** Exactly one of `parent_id` or `parent_path` must be provided - raises `ValueError` otherwise. Auto-creates missing folders in path.

---

## resolve_target_layer_parent
Get parent folder ID for a layer. If layer exists, returns its current parent. If not, optionally creates folders from path.

```python
from evergis_tools.catalog import resolve_target_layer_parent

parent_id = resolve_target_layer_parent(client, "john_doe.my_layer", target_layer_parent_path="john_doe/Projects/Data")
```

**Key params:** `client`, `target_layer: str`, `target_layer_parent_path=None`

**Returns:** `Optional[str]` - parent folder ID, or None if layer doesn't exist and no path provided.

---

## See Also
- [[Catalog/Folders|Folders]] - Create and manage folders
- [[Catalog/Catalog|Catalog]] - Overview
