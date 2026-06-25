"""Create a virtual layer with an explicit Pydantic schema and a custom EQL query.

When the result of a JOIN doesn't map cleanly to a single source
layer, ``create_layer_from_schema(..., query=...)`` lets you declare
exactly which fields the layer should expose AND provide the EQL that
produces them. The layer is virtual (``create_table=False``) - rows
live in the source tables and are computed on read.

The schema fields must match the SELECT projection (names + types).
"""

import os
from typing import Optional

from pydantic import BaseModel, Field

from evergis_tools import Client
from evergis_tools.catalog import add_layer_to_map, delete_resource
from evergis_tools.layers import create_layer_from_schema


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")

LAYER_SHORT = "schema_division_pois_summary"
LAYER_ALIAS = "POI counts per division"
GEOMETRY_TYPE = "MultiPolygon"
SRID = 4326


class DivisionPOISummary(BaseModel):
    """Aggregated POI stats per division (one row per division)."""

    gid: int = Field(..., description="Division identifier")
    division: str = Field(..., description="Division name")
    poi_total: Optional[int] = Field(None, description="Total POIs inside the division")
    poi_categories: Optional[int] = Field(None, description="Distinct POI categories inside")


QUERY = """
WITH poi AS (
    SELECT gid, category, geom FROM {SAMPLE_DATA_OWNER}.evg_overture_places
)
SELECT
    d.gid,
    d.name AS division,
    COUNT(p.gid)::int AS poi_total,
    COUNT(DISTINCT p.category)::int AS poi_categories,
    d.geom
FROM {SAMPLE_DATA_OWNER}.evg_overture_districts AS d
LEFT JOIN poi AS p ON ST_Within(p.geom, d.geom)
GROUP BY d.gid, d.name, d.geom
"""


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    target_layer = f"{username}.{RESOURCE_PREFIX}_{LAYER_SHORT}"
    target_parent = f"{username}/{PROJECT_PATH}/layers/results"

    delete_resource(client, target_layer, missing_ok=True)

    create_layer_from_schema(
        client=client,
        schema=DivisionPOISummary,
        layer_name=target_layer,
        layer_alias=LAYER_ALIAS,
        parent_path=target_parent,
        geometry_field="geometry",
        geometry_type=GEOMETRY_TYPE,
        srid=SRID,
        create_table=False,
        query=QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username),
        overwrite=True, log=False,
    )
    add_layer_to_map(
        client, f"{username}.{RESOURCE_PREFIX}_map_layers", target_layer,
    )
    print(f"layer saved (virtual): {target_parent}/{target_layer}")
