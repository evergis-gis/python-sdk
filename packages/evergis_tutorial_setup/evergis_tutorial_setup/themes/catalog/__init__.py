# -*- coding: utf-8 -*-
"""Theme: ``catalog`` - folder / file / resource operations.

Catalog examples are about the catalog tree itself (rename, move,
upload, delete). No spatial content; the companion map is a landing
page so the reader still has a single click into the theme folder.

The ``folders`` override pre-creates a handful of sandbox subdirs the
examples expect.
"""

from ..._config import MapConfig, ThemeConfig

THEME = ThemeConfig(
    name="catalog",
    alias="catalog tutorial",
    depends_on=[],
    folders=(
        "scripts",
        "rename/folder_a",
        "rename/folder_b",
        "create_file",
        "extract",
        "nested_folders",
        "delete",
        "exists",
        "list",
        "metadata",
        "upload_file",
        "upload_files",
        "upload_directory",
    ),
    map=MapConfig(),   # landing page, no layers
)
