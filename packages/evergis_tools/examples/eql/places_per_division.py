"""Statistics on places per Moscow division.

For every division returns the number of places (POIs) inside it and
the count of distinct categories. Demonstrates ``WITH`` (CTE) plus a
spatial ``JOIN`` on ``ST_Within``.

Reads from the seed layers ``evg_overture_districts`` and
``evg_overture_places``.
"""

import os
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_dataframe


QUERY = """
WITH d AS (
    SELECT geom, name FROM {SAMPLE_DATA_OWNER}.evg_overture_districts
)
SELECT d.name AS division,
       COUNT(p.id) AS places,
       COUNT(DISTINCT p.category) AS categories
FROM {SAMPLE_DATA_OWNER}.evg_overture_places AS p
JOIN d ON ST_Within(p.geom, d.geom)
GROUP BY d.name
ORDER BY places DESC
LIMIT 10
"""


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    df = eql_query_to_dataframe(QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username), client)

    print(f"rows: {len(df)}")
    print(df.to_string(index=False))
