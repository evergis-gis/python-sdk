# -*- coding: utf-8 -*-
"""Theme: ``tasks`` - server-side import / export tasks.

Tasks are headless - they run on EverGIS workers and produce files
or layers. No own seed layers; examples create their results under
``tasks/results/``.

* ``source_files`` is a symlink to the shared source-files folder under
  ``SAMPLE_DATA_OWNER`` (edu) so users land on the fixtures import
  examples read from in one click.
* Map extent is global (Atlantic-centred, zoom 2) because import
  examples pull from many parts of the world (Chicago crimes, German
  lands, Italian regions, global earthquakes, Natural Earth countries).
"""

from ..._config import ExternalSymlink, MapConfig, MapLayerRef, ThemeConfig


# Shared source-files folder under SAMPLE_DATA_OWNER (edu); the symlink
# is marked external so the runner resolves it under edu, not the caller.
SAMPLE_SOURCE_FILES_PATH = (
    "EverGIS Sample Data Catalog/Source files - raw archives"
)


THEME = ThemeConfig(
    name="tasks",
    alias="tasks tutorial",
    depends_on=["shared"],
    folders=("scripts", "results"),
    symlinks=[ExternalSymlink(
        name="source_files", target_path=SAMPLE_SOURCE_FILES_PATH, external=True,
    )],
    map=MapConfig(
        position=(10, 30),
        resolution=2,
        layers=[
            MapLayerRef(short="overture_places",    visible=True),
            MapLayerRef(short="overture_districts", visible=True),
        ],
    ),
)
