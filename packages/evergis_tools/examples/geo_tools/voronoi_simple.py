"""Build Voronoi cells around restaurant POIs inside the Central okrug.

Loads restaurants from ``evg_overture_places`` and the Tsentralny
administrative division polygon from ``evg_overture_districts`` to
use as a clipping boundary. Builds Voronoi cells via
``create_voronoi_with_attributes``, then plots cells + restaurants on
top of the division outline.
"""

import matplotlib.pyplot as plt

import os
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_geodataframe
from evergis_tools.geo_tools import create_voronoi_with_attributes


DIVISION_QUERY = """
SELECT name, geom FROM {SAMPLE_DATA_OWNER}.evg_overture_districts
WHERE name = 'Центральный'
"""

POINTS_QUERY = """
WITH d AS (
    SELECT geom FROM {SAMPLE_DATA_OWNER}.evg_overture_districts WHERE name = 'Центральный'
)
SELECT p.name AS name, p.category AS category, p.geom AS geometry
FROM {SAMPLE_DATA_OWNER}.evg_overture_places AS p
JOIN d ON ST_Within(p.geom, d.geom)
WHERE p.category = 'restaurant'
"""


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    division = eql_query_to_geodataframe(DIVISION_QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username), client)
    points = eql_query_to_geodataframe(POINTS_QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username), client)
    print(f"division: {division.iloc[0]['name']}  restaurants: {len(points)}")

    boundary = division.geometry.iloc[0]
    cells = create_voronoi_with_attributes(
        points,
        attribute_columns=["name", "category"],
        boundary=boundary,
    )
    print(f"voronoi cells: {len(cells)}")

    fig, ax = plt.subplots(figsize=(10, 10))
    division.boundary.plot(ax=ax, color="black", linewidth=1)
    cells.plot(ax=ax, alpha=0.4, edgecolor="white", cmap="tab20")
    points.plot(ax=ax, color="black", markersize=10, zorder=5)
    ax.set_title("Restaurants in Tsentralny - Voronoi service areas")
    ax.set_axis_off()
    plt.show()
