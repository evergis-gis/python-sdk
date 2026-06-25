"""Edit attribute values of the seed table layer by row id.

Reads + edits ``evg_logs`` (table, populated with 4 rows by
the ``features`` theme):

    .venv/bin/python -m evergis_tutorial_setup themes features

The example prints BEFORE / AFTER snapshots so the diff is visible.
Touches every supported attribute type in the update payload -
STRING, INT64, DOUBLE, BOOLEAN, DATETIME, JSON, JSON+Attachments.

Re-run to reset the seed:
    python -m evergis_tutorial_setup themes features --force
"""

from datetime import datetime

import pandas as pd

from evergis_tools import Attachment, Client
from evergis_tools.eql import eql_query_to_dataframe
from evergis_tools.features import edit_layer_by_df


SOURCE_LAYER_SHORT = "evg_logs"

SELECT_COLS = (
    "gid, station_code, metric, value, sample_count, is_anomaly,"
    " recorded_at, raw_payload, attachments"
)


def _attach(name: str, link: str, *, mime: str, external: bool, date: str) -> dict:
    return Attachment(
        date=date, link=link, name=name, mimeType=mime, isExternal=external,
    ).model_dump(mode="json")


with Client() as client:
    username = client.account.get_user_info().username
    target_layer = f"{username}.{SOURCE_LAYER_SHORT}"

    print("BEFORE:")
    print(eql_query_to_dataframe(
        f"SELECT {SELECT_COLS} FROM {target_layer} ORDER BY gid", client,
    ).to_string(index=False))

    edits = pd.DataFrame([
        {"gid": 1,
         "metric": "temp_c_corrected",                                   # STRING
         "value": -3.5,                                                  # DOUBLE
         "sample_count": 25,                                             # INT64
         "is_anomaly": True,                                             # BOOLEAN
         "recorded_at": datetime(2026, 1, 15, 9, 0, 5),                  # DATETIME
         "raw_payload": {"sensor": "DHT22", "calibrated": True},         # JSON
         "attachments": [                                                # JSON+Attachments
             _attach("re-calibration.pdf",
                     "https://example.com/re-calibration.pdf",
                     mime="application/pdf", external=True,
                     date="2026-01-15T09:00:05.000000Z"),
         ]},
        {"gid": 2, "is_anomaly": True,
         "raw_payload": {"sensor": "Davis-6410", "gust_ms": 18.2}},
    ])
    edit_layer_by_df(
        client=client, df=edits, layer_name=target_layer,
        id_column="gid", log=False,
    )

    print("\nAFTER:")
    print(eql_query_to_dataframe(
        f"SELECT {SELECT_COLS} FROM {target_layer} ORDER BY gid", client,
    ).to_string(index=False))
