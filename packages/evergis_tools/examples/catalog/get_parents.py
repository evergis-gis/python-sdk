"""Get the chain of ancestor folders for a catalog resource.

``get_parents`` returns ``ResourceParentDc(name, path, resourceId)``
from the root down to the immediate parent (the resource itself is not
included). Useful for breadcrumb UI or for printing the full catalog
path of a resource you only have a system name / id for.

Source for this example: ``natural_earth_110m.gpkg`` from the shared
sample-data catalog owned by ``SAMPLE_DATA_OWNER`` (default ``edu``),
read-only here.
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import get_parents


SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")


with Client() as client:
    resource_path = (
        f"{SAMPLE_DATA_OWNER}/EverGIS Sample Data Catalog/Source files - raw archives"
        "/Source files - GeoPackage gpkg/natural_earth_110m.gpkg"
    )

    parents = get_parents(client, resource_path)

    print(f"breadcrumb for {resource_path}:")
    for p in parents:
        print(f"  /  {p.name}")
