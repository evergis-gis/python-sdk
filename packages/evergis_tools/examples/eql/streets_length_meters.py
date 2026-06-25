"""Length of streets in meters via ``ST_Length(geom::geography)``.

Casting the geography type re-projects the calculation from degrees
(EPSG:4326) to meters, so a single ``ST_Length`` returns a real-world
distance instead of an angular one. Same trick works for ``ST_Distance``
and ``ST_Area``.

Restricted to one Moscow district (Tverskoy) via a JOIN on
``evg_overture_districts``. Note: ``ST_Length(s.geom::geography)`` is
computed on the full street geometry; if the street only clips the
district edge it still counts in full. Use
``ST_Length(ST_Intersection(s.geom, d.geom)::geography)`` for the exact
slice if needed.
"""

import os
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_dataframe


QUERY = """
SELECT s.name,
       ROUND((ST_Length(s.geom::geography))::numeric, 0) AS meters
FROM {SAMPLE_DATA_OWNER}.evg_overture_streets AS s
JOIN {SAMPLE_DATA_OWNER}.evg_overture_districts AS d ON ST_Intersects(s.geom, d.geom)
WHERE s.name IS NOT NULL
  AND d.name = 'Тверской район'
ORDER BY meters DESC
LIMIT 10
"""


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    df = eql_query_to_dataframe(QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username), client)
    print(f"top {len(df)} longest streets crossing the Tverskoy district (meters):")
    print(df.to_string(index=False))
