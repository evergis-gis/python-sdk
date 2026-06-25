"""Delete features from the seed table layer by id and by condition.

Operates on ``evg_logs`` (table, populated with 4 rows by the
``features`` theme):

    .venv/bin/python -m evergis_tutorial_setup themes features

Demonstrates two endpoints in one run:

* ``delete_features_by_ids([2, 3])`` - drop specific rows.
* ``delete_features_by_condition("WHERE is_anomaly = true OR value < 0")``
  - drop everything matching the EQL ``WHERE`` clause (note the
    leading ``WHERE`` - that's the EverGIS convention for filter
    strings on every endpoint that accepts one).

Re-run to reset the seed:
    python -m evergis_tutorial_setup themes features --force
"""

from evergis_tools import Client
from evergis_tools.features import (
    count_features,
    delete_features_by_condition,
    delete_features_by_ids,
    query_layer_to_df,
)


SOURCE_LAYER_SHORT = "evg_logs"

DELETE_IDS = [2, 3]
DELETE_CONDITION = "WHERE is_anomaly = true OR value < 0"


def _show(client, layer, label):
    df = query_layer_to_df(
        client, layer,
        attributes=["gid", "station_code", "metric", "value", "is_anomaly"],
        sort=["gid"],
    )
    n = count_features(client, layer)
    print(f"{label}  (count={n}):")
    print(df.to_string(index=False))


with Client() as client:
    username = client.account.get_user_info().username
    target_layer = f"{username}.{SOURCE_LAYER_SHORT}"

    _show(client, target_layer, "BEFORE")

    print(f"\ndelete_features_by_ids({DELETE_IDS})")
    delete_features_by_ids(client, target_layer, DELETE_IDS)

    print(f"delete_features_by_condition({DELETE_CONDITION!r})")
    delete_features_by_condition(client, target_layer, DELETE_CONDITION)

    print()
    _show(client, target_layer, "AFTER")
