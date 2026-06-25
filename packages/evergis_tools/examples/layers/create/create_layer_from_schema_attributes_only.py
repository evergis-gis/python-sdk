"""Create an attribute-only (no geometry) layer from a Pydantic schema.

Defines a ``MeasurementLog`` Pydantic model with no spatial fields and
creates a table-only EverGIS layer. Useful for tabular data -
observations, surveys, ratings - that links to spatial layers via key
fields rather than carrying geometry of its own.

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

For a layer with geometry see
``create_layer_from_schema_with_geometry.py``.
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

LAYER_SHORT = "schema_measurement_logs"
LAYER_ALIAS = "measurement logs (table)"
SRID = 4326


class MeasurementLog(BaseModel):
    """Single measurement reading covering every supported attribute type."""

    station_code: str = Field(..., description="Station short code")             # STRING
    metric: str = Field(..., description="Metric name (temp_c / wind_ms / ...)")  # STRING
    value: float = Field(..., description="Numeric value of the measurement")    # DOUBLE
    sample_count: int = Field(..., description="Number of raw samples averaged")  # INT64
    is_anomaly: Optional[bool] = Field(None, description="Anomaly flag")          # BOOLEAN
    recorded_at: datetime = Field(..., description="Timestamp of the measurement")  # DATETIME
    raw_payload: Optional[Dict[str, Any]] = Field(None, description="Original sensor payload")  # JSON
    attachments: Optional[list] = Field(                                          # JSON + subType=Attachments
        default=None,
        description="Raw log files / photos for this reading",
        json_schema_extra={"sub_type": "Attachments"},
    )


with Client() as client:
    username = client.account.get_user_info().username
    target_layer = f"{username}.{RESOURCE_PREFIX}_{LAYER_SHORT}"
    target_parent = f"{username}/{PROJECT_PATH}/layers/results"

    delete_resource(client, target_layer, missing_ok=True)

    create_layer_from_schema(
        client=client,
        schema=MeasurementLog,
        layer_name=target_layer,
        layer_alias=LAYER_ALIAS,
        parent_path=target_parent,
        srid=SRID,
        overwrite=True, log=False,
    )
    add_layer_to_map(
        client, f"{username}.{RESOURCE_PREFIX}_map_layers", target_layer,
    )
    print(f"layer saved (empty, table-only): {target_parent}/{target_layer}")
