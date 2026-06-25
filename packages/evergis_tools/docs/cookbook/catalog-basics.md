---
title: Find and manage resources, folders and files
---

# Find and manage resources, folders and files

This recipe covers the everyday catalog moves: make a folder (with all
its parents in one call), put a file into it, find that file by its
path, check whether it is there, and pull it back down to disk. Every
function here accepts the same kind of identifier - a catalog path, a
resource ID, or a system name - so you rarely have to think about which
one you are holding.

The script is self-contained: it writes a tiny text file to `/tmp`,
uploads that into a new folder under your `Cookbook`, then reads it back.

```python
from pathlib import Path
import tempfile

from evergis_tools import Client
from evergis_tools.catalog import (
    download_file,
    exists,
    get_or_create_folder_by_path,
    resolve_resource,
    upload_file,
)

with Client() as client:
    username = client.account.get_user_info().username

    # A small local file to upload. In real use this is your own file.
    local_file = Path(tempfile.gettempdir()) / "cookbook_notes.txt"
    local_file.write_text("Hello from the EverGIS cookbook.\n", encoding="utf-8")

    # 1. Create a nested folder. Every missing level is created at once,
    #    and running this again just returns the existing folder.
    folder_path = f"{username}/Cookbook/catalog_basics/files"
    folder = get_or_create_folder_by_path(client, folder_path)
    print(f"folder ready: {folder.path}")

    # 2. Upload the file into that folder.
    uploaded = upload_file(client, file_path=local_file, parent_path=folder_path)
    catalog_path = f"{folder_path}/{uploaded.name}"
    print(f"uploaded {uploaded.name}: id={uploaded.resourceId[:8]}  size={uploaded.size}")

    # 3. Find it again by its catalog path. resolve_resource returns the
    #    full metadata record (id, type, size, and more).
    found = resolve_resource(client, catalog_path)
    print(f"resolved: type={found.type}  id={found.resourceId[:8]}")

    # 4. Quick yes/no check - cheaper than resolve when you only need
    #    to know whether something is there.
    print(f"exists by path: {exists(client, catalog_path)}")
    print(f"exists by id:   {exists(client, found.resourceId)}")

    # 5. Download it back. A path ending in "/" is treated as a folder,
    #    so the file keeps its own name inside it.
    out_dir = Path(tempfile.gettempdir()) / "cookbook_download"
    saved = download_file(client, catalog_path, f"{out_dir}/", overwrite=True)
    print(f"downloaded to: {saved}  ({saved.stat().st_size} bytes)")
```

Notes:

- `get_or_create_folder_by_path` walks the path from the deepest
  existing parent and creates only what is missing, so it is safe to run
  more than once - existing folders are left as they are.
- `upload_file` takes `parent_path` (a folder path) and uploads the
  file under its own name. If the folder does not exist yet it is
  created for you, so step 1 is optional here - it is shown to make the
  folder layout explicit. By default an existing file with the same name
  is overwritten (`rewrite=True`).
- `resolve_resource` and `exists` accept a catalog path, a 32-character
  resource ID, or a system name. Use `exists` for a plain True/False;
  use `resolve_resource` when you need the metadata.
- `download_file` writes the bytes to `target_path`. Give it a path
  ending in `/` (or an existing directory) to keep the resource's own
  name, or a full file path to rename on the way down. Pass
  `overwrite=True` to replace a file that is already there.
- Paths use the slash form `username/Folder/Name`. The older
  `username:Folder/Name` form still works too.

## See also

- [[quickstart|Quick start]]
- [[layer-from-geodataframe|Create a layer from a GeoDataFrame]]
