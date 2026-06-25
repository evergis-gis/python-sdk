"""Buildings ranked by the diversity of POI categories within 150 m.

For each of the 100 tallest buildings counts how many distinct place
categories sit in a 150-metre radius of its footprint. Demonstrates
``ST_DWithin`` with ``::geography`` so the distance argument is in
metres (otherwise EQL would interpret it as degrees on EPSG:4326).

The candidate set is pre-filtered with a CTE to the 100 tallest
buildings - the join across ~5k buildings × ~7k places without that
limit is too heavy.

Reads from the seed layers ``evg_overture_buildings`` and
``evg_overture_places``.
"""

import os
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_dataframe


QUERY = """
WITH b AS (
    SELECT id, name, height, geom
    FROM {SAMPLE_DATA_OWNER}.evg_overture_buildings
    WHERE height IS NOT NULL
    ORDER BY height DESC
    LIMIT 100
)
SELECT b.name AS building,
       b.height AS height,
       COUNT(DISTINCT p.category) AS categories_around
FROM b
JOIN {SAMPLE_DATA_OWNER}.evg_overture_places AS p
  ON ST_DWithin(b.geom::geography, p.geom::geography, 150)
GROUP BY b.id, b.name, b.height
ORDER BY categories_around DESC
LIMIT 10
"""


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    df = eql_query_to_dataframe(QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username), client)

    print(f"rows: {len(df)}")
    print(df.to_string(index=False))
