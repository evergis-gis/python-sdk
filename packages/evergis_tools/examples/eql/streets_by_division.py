"""Total street length by road class per Moscow division (in metres).

For each division sums the metric length of street segments that
intersect it, broken down by the Overture ``class`` column. Demonstrates
``ST_Length(geometry::geography)`` to get the result in metres
(``ST_Length`` on raw EPSG:4326 geometry returns degrees).

Reads from the seed layers ``evg_overture_districts`` and
``evg_overture_streets``.
"""

import os
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_dataframe


QUERY = """
SELECT d.name AS division,
       s.class AS road_class,
       SUM(ST_Length(s.geom::geography)) AS total_length_m
FROM {SAMPLE_DATA_OWNER}.evg_overture_streets AS s
JOIN {SAMPLE_DATA_OWNER}.evg_overture_districts AS d
  ON ST_Intersects(s.geom, d.geom)
GROUP BY d.name, s.class
ORDER BY d.name, total_length_m DESC
LIMIT 20
"""


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    df = eql_query_to_dataframe(QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username), client)

    print(f"rows: {len(df)}")
    df["total_length_m"] = df["total_length_m"].round(0)
    print(df.to_string(index=False))
