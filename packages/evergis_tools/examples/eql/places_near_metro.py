"""Spatial JOIN with ``ST_DWithin`` (radius in meters).

Asks: for each metro station, how many restaurants sit within a 200m
walking circle? ``ST_DWithin(a::geography, b::geography, R)`` accepts
the radius in meters; without the geography cast ``R`` would be in
degrees of arc and the result would skew with latitude.

Result: top 10 stations by surrounding restaurant density.
"""

import os
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_dataframe


QUERY = """
SELECT m.name AS station,
       count(DISTINCT p.gid) AS nearby_restaurants
FROM {SAMPLE_DATA_OWNER}.evg_overture_metro_stations AS m
JOIN {SAMPLE_DATA_OWNER}.evg_overture_places AS p
  ON ST_DWithin(m.geom::geography, p.geom::geography, 200)
WHERE p.category = 'restaurant'
GROUP BY m.name
ORDER BY nearby_restaurants DESC
LIMIT 10
"""


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    df = eql_query_to_dataframe(QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username), client)
    print(f"top {len(df)} metro stations by restaurants within 200m:")
    print(df.to_string(index=False))
