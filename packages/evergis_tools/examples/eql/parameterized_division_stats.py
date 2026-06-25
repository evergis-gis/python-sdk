"""Division-level statistics filtered by building class via EQL parameters.

For every Moscow division, computes:

* the number and total footprint area (m²) of buildings of a given
  ``class`` (default ``'apartments'`` = multi-unit residential);
* the number of POIs and the count of distinct POI categories inside
  the division.

The building class is passed as an EQL parameter (``@building_class``)
- the safe way to plug user input into a query, prevents EQL injection
that string-concatenation would expose.

Try other values to explore the data:

* ``'apartments'``    - multi-unit residential (1004 buildings, default)
* ``'house'``         - detached houses
* ``'dormitory'``     - dorms
* ``'office'``        - office buildings (431)
* ``'retail'``        - retail
* ``'hospital'``      - hospitals
* ``'university'``    - universities
* ``'school'``        - schools
* ``'industrial'``    - industrial buildings
"""

import os
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_dataframe


BUILDING_CLASS = "apartments"


QUERY = """
WITH bld AS (
    SELECT id, geom
    FROM {SAMPLE_DATA_OWNER}.evg_overture_buildings
    WHERE class = @building_class
),
bld_stats AS (
    SELECT d.name AS division,
           COUNT(b.id) AS buildings,
           SUM(ST_Area(b.geom::geography)) AS area_m2
    FROM {SAMPLE_DATA_OWNER}.evg_overture_districts AS d
    JOIN bld AS b ON ST_Within(b.geom, d.geom)
    GROUP BY d.name
),
poi_stats AS (
    SELECT d.name AS division,
           COUNT(p.id) AS places,
           COUNT(DISTINCT p.category) AS categories
    FROM {SAMPLE_DATA_OWNER}.evg_overture_districts AS d
    JOIN {SAMPLE_DATA_OWNER}.evg_overture_places AS p ON ST_Within(p.geom, d.geom)
    GROUP BY d.name
)
SELECT b.division AS division,
       b.buildings AS buildings,
       b.area_m2 AS area_m2,
       p.places AS places,
       p.categories AS categories
FROM bld_stats AS b
JOIN poi_stats AS p ON b.division = p.division
ORDER BY b.area_m2 DESC
LIMIT 10
"""


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    df = eql_query_to_dataframe(
        QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username),
        client,
        parameters={"building_class": BUILDING_CLASS},
    )

    print(f"building_class = {BUILDING_CLASS!r}  rows: {len(df)}")
    df["area_m2"] = df["area_m2"].round(0)
    print(df.to_string(index=False))
