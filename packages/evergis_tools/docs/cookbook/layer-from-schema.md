---
title: Create a layer from a schema
smoke: run
---

# Create a layer from a schema

When you know the columns you want but do not have data yet, describe
the columns as a Pydantic model and let `create_layer_from_schema` turn
that model into an empty EverGIS layer. Each model field becomes a layer
attribute; the layer is created empty, ready for you to add features
later.

This recipe creates one layer with Point geometry and one table-only
layer (no geometry), both under `{username}/Cookbook`. The model shows
every Python type the wrapper maps to an EverGIS attribute type.

```python
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from evergis_tools import Client
from evergis_tools.layers import create_layer_from_schema


class WeatherStation(BaseModel):
    """One station record - covers every supported attribute type."""

    code: str = Field(..., description="Station short code")                  # String
    elevation_m: Optional[float] = Field(None, description="Elevation, m")    # Double
    floors: Optional[int] = Field(None, description="Floor count")            # Int64
    is_active: Optional[bool] = Field(None, description="In service now")     # Boolean
    installed_at: Optional[datetime] = Field(None, description="Installed")   # Datetime
    sensor_meta: Optional[Dict[str, Any]] = Field(None, description="Meta")   # Json
    photos: Optional[list] = Field(                                           # Json + Attachments
        default=None,
        description="Inspection photos",
        json_schema_extra={"sub_type": "Attachments"},
    )


class MeasurementLog(BaseModel):
    """A reading with no geometry of its own - links to a layer by code."""

    station_code: str = Field(..., description="Station short code")
    metric: str = Field(..., description="Metric name")
    value: float = Field(..., description="Measured value")
    recorded_at: datetime = Field(..., description="When it was measured")


with Client() as client:
    username = client.account.get_user_info().username
    cookbook = f"{username}/Cookbook"

    # A spatial layer: pass geometry_field + geometry_type so the layer
    # gets a Point geometry column on top of the model fields.
    create_layer_from_schema(
        client=client,
        schema=WeatherStation,
        layer_name="cookbook_weather_stations",
        layer_alias="weather stations",
        parent_path=cookbook,          # folder is created if missing
        geometry_field="geometry",
        geometry_type="Point",
        srid=4326,
        overwrite=True,                # replace it if you run this again
    )
    print(f"Spatial layer saved (empty): {cookbook}/cookbook_weather_stations")

    # A table-only layer: leave geometry_field/geometry_type unset and the
    # layer is created with no geometry column.
    create_layer_from_schema(
        client=client,
        schema=MeasurementLog,
        layer_name="cookbook_measurement_logs",
        layer_alias="measurement logs",
        parent_path=cookbook,
        overwrite=True,
    )
    print(f"Table layer saved (empty): {cookbook}/cookbook_measurement_logs")
```

Notes:

- Type mapping from the Pydantic field to the EverGIS attribute type:

  | Python type        | EverGIS attribute type        |
  | ------------------ | ----------------------------- |
  | `str`              | String                        |
  | `int`              | Int64                         |
  | `float`            | Double                        |
  | `bool`             | Boolean                       |
  | `datetime`, `date` | Datetime                      |
  | `dict`, `list`     | Json                          |
  | `list` + sub_type  | Json with subType=Attachments |

  `Optional[...]` fields map to the inner type (`Optional[int]` becomes
  Int64). The `description` of each field becomes the column alias shown
  in the EverGIS UI.

- The Attachments column (a `list` field tagged with
  `json_schema_extra={"sub_type": "Attachments"}`) is rendered by the UI
  as a file list you can upload files into.

- An `id` column named `gid` (Int64) is added automatically if your
  model does not already have one. Primary-key constraints
  (not-null, unique, autoincrement) are decided by the server now, so
  there is nothing to set for them in your model or the call.

- `overwrite=True` replaces an existing layer of the same name. Use
  `overwrite="cascade"` to also remove resources that depend on it.

## See also

- [[layer-from-geodataframe|Create a layer from a GeoDataFrame]]
- [[quickstart|Quick start]]
</content>
</invoke>
