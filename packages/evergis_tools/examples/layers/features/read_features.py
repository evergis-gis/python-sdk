"""Read attributes-only from a layer into a pandas DataFrame.

``query_layer_to_df`` returns just the attributes - no geometry column,
no GeoDataFrame wrapping. Useful when the consumer only needs the
table side (statistics, reports, joins to other data).

This example reads ``{SAMPLE_DATA_OWNER}.evg_overture_districts`` (146 Moscow districts,
published by an external sample-data pipeline under
``EverGIS Resources/Sample data & maps/overture/``).
"""

import os
from evergis_tools import Client
from evergis_tools.features import query_layer_to_df


SOURCE_LAYER_SHORT = "evg_overture_districts"


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    source_layer = f"{SAMPLE_DATA_OWNER}.{SOURCE_LAYER_SHORT}"

    df = query_layer_to_df(
        client, source_layer,
        attributes=["gid", "name", "name_short", "region", "area_km2"],
        sort=["-area_km2"],
        limit=10,
    )
    print(f"layer:   {source_layer}")
    print(f"rows:    {len(df)} (top 10 by area)")
    print(df.to_string(index=False))
