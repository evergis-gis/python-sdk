"""Add rows to an existing table layer.

Appends 3 measurement-log records to the seed table layer
``evg_logs`` provisioned by the ``features`` theme. Each
added row carries ``station_code='ADD-N'`` so the example is safe to
re-run: it deletes its own previous additions before appending.

Run the seed once:

    .venv/bin/python -m evergis_tutorial_setup themes features

Re-run this script to grow / refresh the added rows. To restore the
seed to its initial state:

    python -m evergis_tutorial_setup themes features --force
"""

from datetime import datetime

import pandas as pd

from evergis_tools import Client
from evergis_tools.features import (
    add_df_features_to_layer,
    delete_features_by_condition,
)


TARGET_LAYER_SHORT = "evg_logs"

# Marker that lets the example clean up its own additions on re-run.
ADD_MARKER = "ADD-"


ROWS = [
    {"station_code": "ADD-1", "metric": "temp_c",       "value": -1.2,
     "sample_count": 12, "is_anomaly": False,
     "recorded_at": datetime(2026, 5, 10, 12, 0, 0),
     "raw_payload": {"sensor": "DHT22", "battery_v": 3.31}},
    {"station_code": "ADD-2", "metric": "wind_ms",      "value":  8.5,
     "sample_count": 30, "is_anomaly": True,
     "recorded_at": datetime(2026, 5, 10, 12, 5, 0),
     "raw_payload": {"sensor": "Davis-6410", "gust_ms": 12.0}},
    {"station_code": "ADD-3", "metric": "humidity_pct", "value": 65.0,
     "sample_count": 12, "is_anomaly": False,
     "recorded_at": datetime(2026, 5, 10, 12, 0, 0),
     "raw_payload": None},
]


with Client() as client:
    username = client.account.get_user_info().username
    target_layer = f"{username}.{TARGET_LAYER_SHORT}"

    # Wipe rows from previous runs of this example so the result is stable.
    delete_features_by_condition(
        client, target_layer,
        f"WHERE station_code LIKE '{ADD_MARKER}%'",
    )

    df = pd.DataFrame(ROWS)
    add_df_features_to_layer(
        client=client, df=df, layer_name=target_layer, log=False,
    )
    print(f"appended {len(df)} rows to {target_layer}")
