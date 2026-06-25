"""k-NN query: nearest metro station for each restaurant.

Uses ``CROSS JOIN LATERAL`` (a small per-row subquery): for every
restaurant row, run a tiny SELECT over metro stations sorted by the
KNN-distance operator ``<->`` and keep only the closest one. The
distance value is recomputed in meters via ``ST_Distance(::geography)``
because ``<->`` returns degrees (the SRID's native unit).

Restricted to the Tverskoy district so the output shows several stations
within walking range; without the district filter you'd get many
restaurants clustered around the same station and a less varied
illustration of the technique.
"""

import os
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_dataframe


QUERY = """
SELECT p.gid, p.name AS place,
       near.station,
       ROUND(near.dist::numeric, 0) AS dist_m
FROM {SAMPLE_DATA_OWNER}.evg_overture_places AS p
JOIN {SAMPLE_DATA_OWNER}.evg_overture_districts AS d ON ST_Within(p.geom, d.geom)
CROSS JOIN LATERAL (
    SELECT m.name AS station,
           ST_Distance(p.geom::geography, m.geom::geography) AS dist
    FROM {SAMPLE_DATA_OWNER}.evg_overture_metro_stations AS m
    ORDER BY p.geom <-> m.geom
    LIMIT 1
) AS near
WHERE p.category = 'restaurant'
  AND d.name = 'Тверской район'
ORDER BY near.dist
LIMIT 10
"""


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    df = eql_query_to_dataframe(QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username), client)
    print(f"closest metro for {len(df)} restaurants in the Tverskoy district:")
    print(df.to_string(index=False))
