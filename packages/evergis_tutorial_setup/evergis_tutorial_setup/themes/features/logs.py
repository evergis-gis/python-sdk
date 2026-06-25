# -*- coding: utf-8 -*-
"""``john_doe.evg_logs`` - table seed: measurement readings covering every
supported attribute type. Companion to ``stations`` (no geometry).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
from pydantic import BaseModel, Field

from evergis_tools.features import add_df_features_to_layer

from ..._config import LayerSchema
from .logs_data import ROWS


SRID = 4326


class MeasurementLog(BaseModel):
    station_code: str = Field(..., description="Station short code")
    metric: str = Field(..., description="Metric name")
    value: float = Field(..., description="Numeric value")
    sample_count: int = Field(..., description="Raw samples averaged")
    is_anomaly: Optional[bool] = Field(None, description="Anomaly flag")
    recorded_at: datetime = Field(..., description="Measurement timestamp")
    raw_payload: Optional[Dict[str, Any]] = Field(None, description="Sensor payload")
    attachments: Optional[list] = Field(
        default=None,
        description="Raw log files / photos",
        json_schema_extra={"sub_type": "Attachments"},
    )


def populate(client, layer_name: str) -> None:
    add_df_features_to_layer(
        client=client, df=pd.DataFrame(ROWS),
        layer_name=layer_name, log=False,
    )


LAYER = LayerSchema(
    alias="measurement logs (seed)",
    schema=MeasurementLog,
    geometry_type=None,        # table-only
    geometry_field=None,
    srid=SRID,
    populate=populate,
)
