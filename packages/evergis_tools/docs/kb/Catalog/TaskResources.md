---
title: Catalog - Task Resources
module: evergis_tools.catalog.task_resources
---

# Task Resources

TaskResource - special catalog item for storing task files (scripts, configs, data). Import: `from evergis_tools.catalog import ...`

---

## create_task_resource
Create new TaskResource in catalog.

```python
from evergis_tools.catalog import create_task_resource

task_id = create_task_resource(client, "my_task", parent_path="john_doe/Projects/Tasks")
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `name` | required | Task name (`.task` extension added automatically) |
| `parent_id` | `None` | Parent folder resource ID |
| `parent_path` | `None` | Catalog path (alternative, mutually exclusive) |
| `description` | `None` | Task description |
| `tags` | `None` | Tags |
| `sub_type` | `PYTHONTASK` | TaskResourceSubType enum |

**Returns:** `str` - TaskResource UUID (not CatalogResourceDc).

---

## is_task_resource_path
Detect if a path is in TaskResource format (contains `.task/`).

```python
from evergis_tools.catalog import is_task_resource_path

is_task_resource_path("john_doe/Projects/test.task/src/utils")              # True
is_task_resource_path("6c02301ae0b94cf8a6f595b20890b1b7/src")        # True (UUID/path)
is_task_resource_path("john_doe/Projects/Folder")                           # False
```

**Returns:** `bool`

---

## parse_task_resource_path
Parse mixed catalog/TaskResource path into components.

```python
from evergis_tools.catalog import parse_task_resource_path

catalog_path, task_name, internal_path = parse_task_resource_path(
    "john_doe/Projects/Folder/test.task/src/utils"
)
# ("john_doe/Projects/Folder", "test.task", "src/utils")
```

**Returns:** `tuple[str, str, str]` - (catalog_path, task_name, internal_path)

---

## resolve_task_resource_by_path
Resolve TaskResource UUID from catalog path and task name.

```python
from evergis_tools.catalog import resolve_task_resource_by_path

task_id = resolve_task_resource_by_path(client, "john_doe/Projects/Tasks", "my_task")
```

**Key params:** `client`, `catalog_path: str`, `task_name: str`

**Returns:** `str` - TaskResource UUID.

> **Note:** Case-sensitive exact name match. Adds `.task` extension if missing.

---

## create_folder_in_task_resource
Create internal folder inside TaskResource.

```python
from evergis_tools.catalog import create_folder_in_task_resource

parent_id = create_folder_in_task_resource(client, task_id, "src/utils")
```

**Key params:** `client`, `task_resource_id: str`, `folder_path: str`, `description=None`, `tags=None`

**Returns:** `str` - parentId in format `"taskId/path"`.

> **Warning:** Always creates - fails with HTTP 409 if folder already exists. Use `get_or_create_folder_in_task_resource` instead.

---

## get_or_create_folder_in_task_resource
Get existing or create internal folder inside TaskResource. Recommended over `create_folder_in_task_resource`.

```python
from evergis_tools.catalog import get_or_create_folder_in_task_resource

parent_id = get_or_create_folder_in_task_resource(client, task_id, "src/utils")
```

**Key params:** `client`, `task_resource_id: str`, `folder_path: str`, `description=None`, `tags=None`

**Returns:** `str` - parentId in format `"taskId/path"`.

---

## upload_file_to_task_resource
Upload file to TaskResource internal path. Creates internal folders if needed.

```python
from evergis_tools.catalog import upload_file_to_task_resource

resource = upload_file_to_task_resource(
    client, "/path/to/script.py",
    task_resource_id=task_id,
    internal_path="src/",
)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `file_path` | required | Local file path |
| `task_resource_id` | required | TaskResource UUID |
| `internal_path` | `""` | Internal folder path (empty = root) |
| `owner` | `None` | Defaults to current user |
| `rewrite` | `True` | Overwrite existing |
| `description` | `None` | Auto-generated if None |

**Returns:** `CatalogResourceDc`

---

## See Also
- [[Catalog/Files|Files]] - Upload files to regular catalog
- [[Catalog/Folders|Folders]] - Regular folder operations
- [[Tasks]] - Task execution system
- [[Catalog/Catalog|Catalog]] - Overview
