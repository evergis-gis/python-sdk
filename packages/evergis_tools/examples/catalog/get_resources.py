"""List a single page of resources with server-side filters.

``get_resources`` returns a ``PagedResourcesListDc`` with ``items`` and
the total count - use it when you need pagination metadata or just one
page. For a generator that streams every page automatically see
``iter_resources`` (and the ``list_container_contents.py`` example).

The example reads a folder of the shared sample-data catalog owned by
``SAMPLE_DATA_OWNER`` (default ``edu``) and lists the files inside.
Because the folder belongs to another account, the listing uses
``owner_filter="Shared"`` (``"My"`` would only see the caller's own
resources).
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import get_resources


SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")


with Client() as client:
    parent = (
        f"{SAMPLE_DATA_OWNER}/EverGIS Sample Data Catalog/Source files - raw archives"
        "/Source files - CSV"
    )

    page = get_resources(
        client,
        parent=parent,
        owner_filter="Shared",
        resource_types=["File"],
        limit=10,
    )
    print(f"totalCount: {page.totalCount}  (showing up to {len(page.items)})")
    for r in page.items:
        size_kb = (r.size or 0) / 1024
        print(f"  {r.name:40s}  {size_kb:>9,.1f} KB")
