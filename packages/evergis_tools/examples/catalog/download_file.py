"""Download a catalog file to local disk.

``download_file`` resolves the identifier (path / id / system name),
fetches the bytes via ``catalog.get_file`` and writes them to the local
``target_path``. If the target points to a directory, the resource's
own name is appended.

Source for this example: ``natural_earth_110m.gpkg`` from the shared
sample-data catalog owned by ``SAMPLE_DATA_OWNER`` (default ``edu``).
It is read-only here, so it always exists at the expected path.
"""

import os
import tempfile
from pathlib import Path

from evergis_tools import Client
from evergis_tools.catalog import download_file


SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")


with Client() as client:
    source = (
        f"{SAMPLE_DATA_OWNER}/EverGIS Sample Data Catalog/Source files - raw archives"
        "/Source files - GeoPackage gpkg/natural_earth_110m.gpkg"
    )

    dir_target = Path(tempfile.gettempdir()) / "evergis_download_demo"

    # 1. Save into a directory (trailing slash or existing dir) -
    #    the resource's own name is appended automatically.
    saved = download_file(client, source, f"{dir_target}/", overwrite=True)
    print(f"saved to dir: {saved}  ({saved.stat().st_size} bytes)")

    # 2. Save to an explicit file path.
    saved = download_file(
        client, source, dir_target / "natural_earth_renamed.gpkg",
        overwrite=True,
    )
    print(f"saved as:     {saved}  ({saved.stat().st_size} bytes)")
