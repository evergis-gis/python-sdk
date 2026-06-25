# -*- coding: utf-8 -*-
"""``john_doe.evg_stations`` - Point seed: weather stations covering every
supported attribute type (String/Double/Int32/Boolean/DateTime/Json/Attachments;
the PK ``gid`` is Int64).

Used by the read / edit / delete feature examples. Fixture rows live
in ``stations_data.py``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

import geopandas as gpd
from pydantic import BaseModel, Field

from evergis_tools.features import add_gdf_features_to_layer

from ..._config import LayerSchema
from .stations_data import ROWS


SRID = 4326


class WeatherStation(BaseModel):
    code: str = Field(..., description="Station short code")
    elevation_m: Optional[float] = Field(None, description="Elevation in metres")
    # Int32 (the default for plain ``int``); a NULL row is allowed. Only
    # the PK gid stays Int64, which the server makes autoincrement/NOT NULL.
    floors_visible: Optional[int] = Field(None, description="Visible floors from the mast")
    is_active: Optional[bool] = Field(None, description="Currently in service")
    installed_at: Optional[datetime] = Field(None, description="Installation timestamp")
    sensor_meta: Optional[Dict[str, Any]] = Field(None, description="Free-form sensor metadata")
    photos: Optional[list] = Field(
        default=None,
        description="Inspection photos",
        json_schema_extra={"sub_type": "Attachments"},
    )


# Boolean-driven styling via ``case`` - frontend does not currently
# pin boolean literals through ``match``, so this is the canonical form.
STYLE = {
    "items": [
        {"type": "circle", "paint": {
            "circle-color": [
                "case", ["get", "is_active"], "#33a02c", "#999999",
            ],
            "circle-radius": 6,
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 1.5,
        }},
    ]
}


def populate(client, layer_name: str) -> None:
    add_gdf_features_to_layer(
        client=client,
        gdf=gpd.GeoDataFrame(ROWS, crs=f"EPSG:{SRID}"),
        layer_name=layer_name,
        target_sr=SRID, geometry_type="Point", log=False,
    )


LAYER = LayerSchema(
    alias="weather stations (seed)",
    schema=WeatherStation,
    geometry_type="Point",
    geometry_field="geometry",
    srid=SRID,
    client_style=STYLE,
    populate=populate,
)
