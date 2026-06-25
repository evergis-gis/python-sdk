---
title: Catalog - Files
module: evergis_tools.catalog.files
---

# Files

Import: `from evergis_tools.catalog import (upload_file, upload_files_by_extension, upload_directory, create_file, update_file, download_file, extract_zip)`

---

## upload_file
Upload single file from disk to catalog or TaskResource.

```python
from evergis_tools.catalog import upload_file

resource = upload_file(client, "/path/to/data.csv", parent_path="john_doe/Projects/Uploads")
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `file_path` | required | Local file path (str or Path) |
| `parent_path` | `None` | Catalog path or TaskResource mixed path |
| `parent_id` | `None` | Direct resource ID (alternative to parent_path) |
| `owner` | `None` | Defaults to current user |
| `rewrite` | `True` | Overwrite existing file |
| `description` | `None` | Auto-generated as `"Uploaded file: <name>"` if None |

**Returns:** `CatalogResourceDc`

> **Warning:** `parent_path` and `parent_id` are mutually exclusive - exactly one must be provided (raises `ValueError` otherwise). Raises `FileNotFoundError` if `file_path` is not a file.

> **Note:** Auto-detects TaskResource paths (containing `.task/`). Regular catalog paths are created via `get_or_create_folder_by_path` if missing.

---

## upload_files_by_extension
Upload multiple files from a directory filtered by extension.

```python
from evergis_tools.catalog import upload_files_by_extension

resources = upload_files_by_extension(
    client, "/path/to/dir", "john_doe/Uploads",
    extensions=[".csv", ".xlsx"],
    recursive=True,
)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `directory_path` | required | Local directory path |
| `parent_path` | required | Catalog path for uploads |
| `extensions` | `None` | Single `".csv"` or list `[".csv", ".xlsx"]`; `None` or `["*"]` for all files |
| `owner` | `None` | Defaults to current user |
| `rewrite` | `True` | Overwrite existing |
| `recursive` | `False` | Search subdirectories |

**Returns:** `List[CatalogResourceDc]`

> **Warning:** Raises `FileNotFoundError` if `directory_path` is not a directory. Raises `RuntimeError` if every file upload fails (when files were found but `results` is empty). Partial success returns the list of successful results.

> **Note:** Per-file failures are logged via the `logging` module (`logger.error`) and skipped; successes are logged via `logger.info`. Extensions are normalized (a leading `.` is added if missing, then lowercased).

---

## upload_directory
Upload an entire directory recursively, preserving the folder hierarchy.

```python
from evergis_tools.catalog import upload_directory

resources = upload_directory(client, "/path/to/project", "john_doe/Projects/Upload")
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `directory_path` | required | Local directory path |
| `parent_path` | required | Catalog path (regular or TaskResource) |
| `owner` | `None` | Defaults to current user |
| `rewrite` | `True` | Overwrite existing |
| `ignore_patterns` | `None` | gitignore-style patterns (default list applied if None) |
| `sync` | `False` | Delete remote files/folders not present locally |

**Returns:** `List[CatalogResourceDc]`

> **Warning:** `sync=True` is destructive - it deletes remote files and folders that are not present in the local directory. Raises `FileNotFoundError` if `directory_path` is not a directory. Raises `RuntimeError` if every file upload fails (files found but none uploaded).

> **Note:** Progress is printed to stdout (`✓` / `✗` per file); failures are also logged via `logger.error`. Default ignore patterns: `__pycache__`, `*.pyc`, `*.pyo`, `*.pyd`, `.DS_Store`, `._.DS_Store`, `Thumbs.db`, `*.tmp`, `*.swp`, `*~`.

---

## create_file
Create a new catalog file from in-memory content (built at runtime).

```python
from evergis_tools.catalog import create_file

resource = create_file(
    client, "report.txt", "line 1\nline 2",
    parent_path="john_doe/Projects/Reports",
)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `name` | required | File name |
| `content` | required | `str` (UTF-8 encoded) or raw `bytes` |
| `parent_path` | `None` | Catalog path; missing folders are created |
| `parent_id` | `None` | Resource ID (alternative to parent_path) |
| `description` | `None` | Optional file description |

**Returns:** `CatalogResourceDc`

> **Warning:** Pass exactly one of `parent_path` / `parent_id` (raises `ValueError` if both set or both missing). Calls the server with `rewrite=False`, so it raises `ResourceExists` (importable from `evergis_tools`) if a file with this name already exists at the destination - use `update_file` to overwrite. See [[Errors]].

> **Note:** For files already on disk use `upload_file`.

---

## update_file
Overwrite an existing catalog file's content in place.

```python
from evergis_tools.catalog import update_file

resource = update_file(client, "john_doe/Projects/Reports/report.txt", "new body")
```

**Key params:** `client`, `identifier` (catalog path, resource ID, or system name), `content` (`str` UTF-8 or `bytes`).

**Returns:** `CatalogResourceDc`

> **Warning:** Raises `ValueError` if the file cannot be resolved.

> **Note:** The resulting resource keeps the same `resourceId` and `parentId`; only `size` and contents change. The wrapper resolves `parentId + name` first and calls the server with `rewrite=True` (passing only `resourceId` would create a new file instead). Only content changes - to edit `description` / `tags` / `icon` use `update_resource_metadata` ([[Catalog/Resources|Resources]]).

---

## download_file
Download a catalog file's content to local disk.

```python
from evergis_tools.catalog import download_file

path = download_file(client, "john_doe/Projects/Data/data.zip", "./downloads/", overwrite=True)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `identifier` | required | Catalog path, resource ID, or system name |
| `target_path` | required | Destination on disk (str or Path) |
| `overwrite` | `False` | Replace destination if it already exists |

**Returns:** `Path` - absolute path of the saved file

> **Note:** If `target_path` is an existing directory or ends with `/` or `\`, the file is saved inside it under the resource's own name; otherwise `target_path` is the full destination path. Missing parent directories are created automatically.

> **Warning:** Raises `ValueError` if the resource cannot be resolved, and `FileExistsError` if `target_path` exists and `overwrite` is `False`.

---

## extract_zip
Extract a zip archive that already lives in the catalog.

```python
from evergis_tools.catalog import extract_zip

ok = extract_zip(
    client, "john_doe/Projects/Data/archive.zip",
    target_parent="john_doe/Projects/Data/unpacked",
    conflict_strategy="Overwrite",
    delete_zip_after=True,
)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `archive` | required | Zip resource - catalog path, resource ID, or system name |
| `target_parent` | `None` | Destination (catalog path with missing folders created, or resource ID); `None` means the archive's own parent |
| `conflict_strategy` | `"Skip"` | One of `"Skip"`, `"Overwrite"`, `"GenerateUnique"`, `"ThrowError"` (or `ConflictResolutionStrategy`) |
| `delete_zip_after` | `False` | Remove the source archive after extraction |
| `extract_nested` | `False` | Also extract zip archives found inside |

**Returns:** `bool` - `True` on success

---

## See Also
- [[Catalog/Folders|Folders]] - Create target folders
- [[Catalog/Resources|Resources]] - Resolve resources, update metadata
- [[Catalog/TaskResources|Task Resources]] - Upload to TaskResource
- [[Catalog/Catalog|Catalog]] - Overview
