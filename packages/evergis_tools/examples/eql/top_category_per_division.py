"""For every Moscow division, find the most common POI category.

Demonstrates the classic "top-1 per group" SQL pattern via a window
function: ``ROW_NUMBER() OVER (PARTITION BY division ORDER BY cnt DESC)``
ranks categories within each division, then the outer query keeps only
the top row per division.

Reads from the seed layers ``evg_overture_districts`` and
``evg_overture_places``.
"""

import os
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_dataframe


QUERY = """
WITH division_categories AS (
    SELECT d.name AS division,
           p.category AS category,
           COUNT(*) AS cnt
    FROM {SAMPLE_DATA_OWNER}.evg_overture_districts AS d
    JOIN {SAMPLE_DATA_OWNER}.evg_overture_places AS p ON ST_Within(p.geom, d.geom)
    WHERE p.category IS NOT NULL
    GROUP BY d.name, p.category
),
ranked AS (
    SELECT division, category, cnt,
           ROW_NUMBER() OVER (PARTITION BY division ORDER BY cnt DESC) AS rn
    FROM division_categories
)
SELECT division, category, cnt
FROM ranked
WHERE rn = 1
ORDER BY cnt DESC
LIMIT 10
"""


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    df = eql_query_to_dataframe(QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username), client)

    print(f"rows: {len(df)}")
    print(df.to_string(index=False))
