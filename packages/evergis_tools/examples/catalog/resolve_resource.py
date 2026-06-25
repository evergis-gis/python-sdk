"""Resolve a resource by path or by resource ID.

``resolve_resource`` accepts three identifier shapes:

* catalog path (``<username>/Folder/Name``; the legacy ``<username>:Folder/Name`` form
  is still accepted) -> ``get_resource``
* 32-char hex resource ID -> ``get_resource``
* anything else -> system-name lookup (requires a server-side
  ``systemName`` such as ``<username>.<short>`` on Layer / Table).

The example demonstrates the first two forms on
``natural_earth_110m.gpkg`` from the shared sample-data catalog owned
by ``SAMPLE_DATA_OWNER`` (default ``edu``).
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import resolve_resource


SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")


with Client() as client:
    catalog_path = (
        f"{SAMPLE_DATA_OWNER}/EverGIS Sample Data Catalog/Source files - raw archives"
        "/Source files - GeoPackage gpkg/natural_earth_110m.gpkg"
    )

    by_path = resolve_resource(client, catalog_path)
    print(f"by path: id={by_path.resourceId[:8]}  type={by_path.type}")

    by_id = resolve_resource(client, by_path.resourceId)
    print(f"by id:   path={by_id.path}")
