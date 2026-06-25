"""Read features filtered by an EQL ``WHERE`` condition.

Demonstrates three knobs of ``query_layer_to_gdf``:

* ``conditions`` - one or more ``WHERE`` clauses (combined with AND).
* ``attributes`` - return only a subset of columns.
* ``sort``       - server-side ordering (prefix ``-`` for DESC).

Source: ``{SAMPLE_DATA_OWNER}.evg_overture_places`` (Moscow POIs from Overture). The
filter pins one specific category and keeps the top by confidence -
useful illustration of how to narrow a heavy layer to a workable
in-memory slice.
"""

import matplotlib.pyplot as plt

import os
from evergis_tools import Client
from evergis_tools.features import query_layer_to_gdf


SOURCE_LAYER_SHORT = "evg_overture_places"

# ``conditions`` are concatenated by the server without an inserted
# separator - either keep them in a single string or include the
# leading space + AND in each subsequent element.
CONDITIONS = ["WHERE category = 'restaurant' AND confidence >= 0.8"]
# Geometry column on Overture layers is ``geom`` (not ``geometry``);
# include it explicitly so the wrapper packs it into the request.
ATTRIBUTES = ["gid", "name", "category", "confidence", "address", "geom"]
SORT = ["-confidence"]
LIMIT = 200


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    source_layer = f"{SAMPLE_DATA_OWNER}.{SOURCE_LAYER_SHORT}"

    gdf = query_layer_to_gdf(
        client, layer_name=source_layer,
        conditions=CONDITIONS,
        attributes=ATTRIBUTES,
        sort=SORT,
        limit=LIMIT,
    )
    print(f"layer:    {source_layer}")
    print(f"filter:   {CONDITIONS}")
    print(f"sort:     {SORT}")
    print(f"rows:     {len(gdf)} (limit {LIMIT})")
    print(gdf.drop(columns="geometry").head(10).to_string(index=False))

    ax = gdf.plot(figsize=(9, 9), markersize=20, color="#33a02c")
    ax.set_title(f"{source_layer}\n{CONDITIONS}")
    ax.set_axis_off()
    plt.show()
