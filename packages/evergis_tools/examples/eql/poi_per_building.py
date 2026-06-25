"""Polygon-contains-point JOIN via ``ST_Contains``.

For each named building in the Basmanny district count the POIs that fall
strictly inside its footprint. Two nested joins:

* ``buildings ⨝ districts ON ST_Within``  - keep only buildings whose
  footprint lies completely inside the chosen district;
* ``buildings ⨝ places ON ST_Contains``   - count points inside each
  building polygon.

A building stays in the output even when it has zero POIs would be
handled by ``LEFT JOIN`` instead - kept simple here because we only
care about the top of the list.
"""

import os
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_dataframe


QUERY = """
SELECT b.gid, b.name AS building,
       count(DISTINCT p.gid) AS poi
FROM {SAMPLE_DATA_OWNER}.evg_overture_buildings AS b
JOIN {SAMPLE_DATA_OWNER}.evg_overture_districts AS d ON ST_Within(b.geom, d.geom)
JOIN {SAMPLE_DATA_OWNER}.evg_overture_places AS p ON ST_Contains(b.geom, p.geom)
WHERE b.name IS NOT NULL
  AND d.name = 'Басманный район'
GROUP BY b.gid, b.name
ORDER BY poi DESC
LIMIT 10
"""


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    df = eql_query_to_dataframe(QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username), client)
    print(f"top {len(df)} buildings in the Basmanny district by POI count:")
    print(df.to_string(index=False))
