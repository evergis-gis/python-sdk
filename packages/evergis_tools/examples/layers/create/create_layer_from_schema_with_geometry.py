"""Create an empty layer from a Pydantic schema (with Point geometry).

Defines a ``WeatherStation`` Pydantic model and turns it into an empty
EverGIS layer with Point geometry. The schema fields become the
layer's attributes; the layer is left empty - populating it is the
next step (see ``add_gdf_features_to_layer`` /
``add_df_features_to_layer`` in ``examples/layers/features/``).

The schema covers every Python type the wrapper auto-maps to an
EverGIS AttributeType:

    Python type           ->  AttributeType
    ---------------------     --------------
    str                   ->  STRING
    int                   ->  INT64
    float                 ->  DOUBLE
    bool                  ->  BOOLEAN
    datetime / date       ->  DATETIME
    dict / list           ->  JSON
    list  + sub_type      ->  JSON + subType=Attachments
                              (file-list column rendered by the EverGIS UI)

For a non-spatial (table-only) variant see
``create_layer_from_schema_attributes_only.py``.
"""

import os
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from evergis_tools import Client
from evergis_tools.catalog import add_layer_to_map, delete_resource
from evergis_tools.layers import create_layer_from_schema


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")

LAYER_SHORT = "schema_weather_stations"
LAYER_ALIAS = "weather stations"
GEOMETRY_TYPE = "Point"
SRID = 4326


class WeatherStation(BaseModel):
    """Weather station record covering every supported attribute type."""

    code: str = Field(..., description="Station short code")                      # STRING
    elevation_m: Optional[float] = Field(None, description="Elevation in metres")  # DOUBLE
    floors_visible: Optional[int] = Field(None, description="Visible floor count from the mast")  # INT64
    is_active: Optional[bool] = Field(None, description="Whether currently in service")  # BOOLEAN
    installed_at: Optional[datetime] = Field(None, description="Installation timestamp")  # DATETIME
    sensor_meta: Optional[Dict[str, Any]] = Field(None, description="Free-form sensor metadata")  # JSON
    photos: Optional[list] = Field(                                                # JSON + subType=Attachments
        default=None,
        description="Inspection photos",
        json_schema_extra={"sub_type": "Attachments"},
    )


with Client() as client:
    username = client.account.get_user_info().username
    target_layer = f"{username}.{RESOURCE_PREFIX}_{LAYER_SHORT}"
    target_parent = f"{username}/{PROJECT_PATH}/layers/results"

    delete_resource(client, target_layer, missing_ok=True)

    create_layer_from_schema(
        client=client,
        schema=WeatherStation,
        layer_name=target_layer,
        layer_alias=LAYER_ALIAS,
        parent_path=target_parent,
        geometry_field="geometry",
        geometry_type=GEOMETRY_TYPE,
        srid=SRID,
        overwrite=True, log=False,
    )
    add_layer_to_map(
        client, f"{username}.{RESOURCE_PREFIX}_map_layers", target_layer,
    )
    print(f"layer saved (empty): {target_parent}/{target_layer}")
