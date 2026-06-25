"""Window function ``RANK() OVER (ORDER BY count(DISTINCT …))``.

A street ranks high if many POIs sit within walking distance of it.
The aggregate ``count(DISTINCT p.gid)`` is computed per ``s.name`` group
and reused inside the ``OVER`` clause - the server allows aggregates as
window-function arguments directly.

Two spatial filters:

* ``streets ⨝ districts ON ST_Intersects`` keeps only streets crossing
  the Presnensky district;
* ``streets ⨝ places ON ST_DWithin(..., 0.0005)`` selects POIs within
  ~55m of the street (at Moscow latitude). The radius is given in
  degrees (the native SRID 4326 unit) on purpose - ``ST_DWithin`` on
  raw geometry can use the existing spatial index, while the
  geography-cast version (``ST_DWithin(::geography, ::geography, 50)``)
  forces a slower per-row recompute and times out on this dataset.
"""

import os
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_dataframe


QUERY = """
SELECT s.name AS street,
       count(DISTINCT p.gid) AS poi,
       RANK() OVER (ORDER BY count(DISTINCT p.gid) DESC) AS rk
FROM {SAMPLE_DATA_OWNER}.evg_overture_streets AS s
JOIN {SAMPLE_DATA_OWNER}.evg_overture_districts AS d ON ST_Intersects(s.geom, d.geom)
JOIN {SAMPLE_DATA_OWNER}.evg_overture_places AS p ON ST_DWithin(s.geom, p.geom, 0.0005)
WHERE s.name IS NOT NULL
  AND d.name = 'Пресненский район'
GROUP BY s.name
ORDER BY rk
LIMIT 10
"""


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    df = eql_query_to_dataframe(QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username), client)
    print(f"top {len(df)} streets in the Presnensky district by POI density (~55m):")
    print(df.to_string(index=False))
