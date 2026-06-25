---
title: Catalog - Folders
module: evergis_tools.catalog.folders
---

# Folders

Import: `from evergis_tools.catalog import create_folder, create_nested_folders, find_folder_by_name, get_or_create_folder, get_or_create_nested_folders, get_or_create_folder_by_path`

---

## get_or_create_folder_by_path
Get or create folder from catalog path. Most convenient function - resolves full path, creates missing segments.

```python
from evergis_tools.catalog import get_or_create_folder_by_path

folder = get_or_create_folder_by_path(client, "john_doe/Projects/Data/2024")
print(folder.resourceId)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `path` | required | Catalog path like `"john_doe/Projects/Data/2024"` |
| `description` | `None` | Description for created folders |
| `tags` | `None` | Tags for created folders |

**Returns:** `CatalogResourceDc` - with `.path` field set.

> **Note:** Resolves right-to-left - finds deepest existing parent, creates missing segments as DIRECTORY.

> **Note:** Accepts both path forms: the `owner:folder/sub` colon form and the `owner/folder/sub` slash form. A path with neither `:` nor `/` raises `ValueError`.

---

## create_nested_folders
Create nested folder structure under a parent.

```python
from evergis_tools.catalog import create_nested_folders

folders = create_nested_folders(client, "data/cities/2024", parent_id="...")
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `folder_path` | required | `/`-separated path like `"data/cities/2024"` |
| `parent_id` | required | Parent folder resource ID |
| `description` | `None` | Applied to **final folder only** |
| `tags` | `None` | Applied to **final folder only** |
| `owner` | `None` | Defaults to current user |

**Returns:** `List[CatalogResourceDc]` - all created folders.

---

## get_or_create_nested_folders
Like `create_nested_folders` but skips existing folders.

```python
from evergis_tools.catalog import get_or_create_nested_folders

folder = get_or_create_nested_folders(client, "data/cities/2024", parent_id="...")
```

**Params:** Same as `create_nested_folders`.

**Returns:** `CatalogResourceDc` - **final folder only** (not a list).

---

## create_folder
Create a single folder.

```python
from evergis_tools.catalog import create_folder

folder = create_folder(client, "my_folder", parent_id="...")
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `name` | required | Folder name |
| `parent_id` | `None` | Parent folder resource ID |
| `description` | `None` | Folder description |
| `tags` | `None` | List of tags |
| `owner` | `None` | Defaults to current user |

**Returns:** `CatalogResourceDc`

> **Note:** Raises `ResourceExists` (importable from `evergis_tools`) if a folder with this name already exists under the same parent. See [[Errors]]. `get_or_create_folder_by_path` is the idempotent alternative.

---

## get_or_create_folder
Get existing or create new folder by name under parent.

```python
from evergis_tools.catalog import get_or_create_folder

folder = get_or_create_folder(client, "my_folder", parent_id="...")
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `name` | required | Folder name |
| `parent_id` | required | Parent folder resource ID |
| `description` | `None` | Folder description (only on create) |
| `tags` | `None` | Tags (only on create) |
| `owner` | `None` | Defaults to current user |

**Returns:** `CatalogResourceDc`

---

## find_folder_by_name
Find container by name under optional parent.

```python
from evergis_tools.catalog import find_folder_by_name

folder = find_folder_by_name(client, "my_folder", parent_id="...")
```

**Key params:** `client`, `folder_name`, `parent_id=None`

**Returns:** `Optional[CatalogResourceDc]` - None if not found.

> **Note:** Searches any container type (DIRECTORY, MAP, LAYER, TASKPROTOTYPE).

---

## See Also
- [[Catalog/Resources|Resources]] - Resolve resource identifiers
- [[Catalog/Files|Files]] - Upload files to folders
- [[Catalog/Catalog|Catalog]] - Overview
