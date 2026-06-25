"""Count features in a layer (with and without a condition).

``count_features`` is a thin wrapper over the
``get_filtered_features_count`` endpoint - much cheaper than reading
every row when all you need is a count. Pass ``condition`` as the EQL
``WHERE`` clause body for a filtered count; omit it for the layer's
total row count.

Reads the seed demo layer ``<username>.evg_overture_places``.
"""

import os
from evergis_tools import Client
from evergis_tools.features import count_features


SOURCE_LAYER_SHORT = "evg_overture_places"

CATEGORIES = ["restaurant", "hospital", "train_station", "cafe", "school"]


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    source_layer = f"{SAMPLE_DATA_OWNER}.{SOURCE_LAYER_SHORT}"

    total = count_features(client, source_layer)
    print(f"layer:           {source_layer}")
    print(f"total features:  {total}")
    print()
    print("by category:")
    for cat in CATEGORIES:
        n = count_features(
            client, source_layer,
            condition=f"WHERE category = '{cat}'",
        )
        print(f"  {cat:15s} {n}")
