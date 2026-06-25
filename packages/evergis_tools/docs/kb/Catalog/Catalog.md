---
title: Catalog
module: evergis_tools.catalog
---

# Catalog

Resource management: resources, folders, files, maps, permissions, task resources.

Import: `from evergis_tools.catalog import ...`

## Sections
- [[Catalog/Resources|Resources]] - resolve_resource, get_resources, resolve_parent_id
- [[Catalog/Folders|Folders]] - create/find/get_or_create folders and paths
- [[Catalog/Files|Files]] - upload files and directories
- [[Catalog/Maps|Maps]] - create_map, update_map
- [[Catalog/DataSources|Data Sources]] - create/update/test/delete data sources (Postgres, S3)
- [[Catalog/Permissions|Permissions]] - get/set/add/remove permissions
- [[Catalog/TaskResources|Task Resources]] - TaskResource CRUD

## Enums

| Enum | Values | Description |
|------|--------|-------------|
| `AccessMode` | My, Shared, Public | Owner filter |
| `ResourceTypeFilter` | Map, Layer, Table, File, DataSource, etc. | Resource type filter |
| `CatalogResourceType` | Directory, Map, Layer, Table, File, etc. | Catalog resource type |
| `GeometryType` | Point, LineString, Polygon, MultiPolygon, etc. | OGC geometry type |
| `ResourceSubTypeFilter` | RemoteTileService, ProxyService, QueryLayerService, etc. | Resource subtype |
| `PermissionLevel` | none, read, write, configure, read,write, etc. | Permission levels |

## See Also
- [[Layers/Layers|Layers]] - Layer CRUD (uses catalog for parent folders)
- [[Tasks]] - Task execution (uses task resources)
