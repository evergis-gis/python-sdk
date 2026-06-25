"""Euclidean vs network "nearest metro": Voronoi vs OD-matrix.

A naive "which metro station is closest" question is usually answered
geometrically - a Voronoi diagram drawn on the station points. That
ignores how the road network actually runs: a station 500m away
through a courtyard is closer than one 250m away across a railway.

Pulls 62 metro stations inside the Central administrative okrug and
30 top-rated restaurants in the Tverskoy district, then answers the
question two ways:

* ``create_voronoi_with_attributes`` over the stations + ``sjoin_nearest``
  -> "Euclidean nearest" station for each restaurant.
* ``build_od_matrix_rest`` (62 x 30 car-time matrix) + groupby-argmin
  -> "network nearest" station for each restaurant.

For roughly half of the restaurants the two answers disagree -
Voronoi gives the geometric truth, but railways, rivers and the
Kremlin re-shape the real-world neighbourhood.
"""

import matplotlib.pyplot as plt

import os
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_geodataframe
from evergis_tools.geo_tools import build_od_matrix_rest, create_voronoi_with_attributes


METRO_QUERY = """
SELECT m.gid AS gid, m.name AS station, m.geom AS geometry
FROM {SAMPLE_DATA_OWNER}.evg_overture_metro_stations AS m
JOIN {SAMPLE_DATA_OWNER}.evg_overture_divisions AS d ON ST_Within(m.geom, d.geom)
WHERE d.name = 'Центральный административный округ'
"""

RESTAURANTS_QUERY = """
SELECT p.gid AS gid, p.name AS place, p.geom AS geometry
FROM {SAMPLE_DATA_OWNER}.evg_overture_places AS p
JOIN {SAMPLE_DATA_OWNER}.evg_overture_districts AS d ON ST_Within(p.geom, d.geom)
WHERE d.name = 'Тверской район' AND p.category = 'restaurant'
ORDER BY p.confidence DESC
LIMIT 30
"""

CAO_BOUNDARY_QUERY = """
SELECT geom AS geometry FROM {SAMPLE_DATA_OWNER}.evg_overture_divisions
WHERE name = 'Центральный административный округ'
"""


with Client() as client:
    username = client.account.get_user_info().username

    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    metro = eql_query_to_geodataframe(
        METRO_QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username), client,
    ).reset_index(drop=True)
    restaurants = eql_query_to_geodataframe(
        RESTAURANTS_QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username), client,
    ).reset_index(drop=True)
    boundary_gdf = eql_query_to_geodataframe(
        CAO_BOUNDARY_QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username), client,
    )
    print(f"metro stations in the Central okrug: {len(metro)}")
    print(f"top restaurants in Tverskoy: {len(restaurants)}")

    # 1) Euclidean nearest = which Voronoi cell the restaurant falls
    # into. ``sjoin_nearest`` avoids NaN for points that land on cell
    # boundaries or just outside the clipped polygon.
    cells = create_voronoi_with_attributes(
        metro, attribute_columns=["gid", "station"],
        boundary=boundary_gdf.geometry.iloc[0],
    )
    rest_v = restaurants.sjoin_nearest(
        cells[["gid", "station", "geometry"]], how="left",
    ).rename(columns={
        "gid_right": "euclid_station_gid",
        "station": "euclid_station",
    })

    # 2) Network nearest = argmin over the OD-matrix per restaurant.
    # ``od`` has columns: from (metro row idx), to (restaurant row idx),
    # distance, ... - sort + drop_duplicates picks the closest station
    # per restaurant; an index-join attaches the station name / gid.
    od = build_od_matrix_rest(
        client, metro, restaurants,
        transport_type="car", epsg_code=4326, seconds=True,
    )
    network = (
        od.sort_values("distance").drop_duplicates("to")
          .rename(columns={"from": "metro_idx", "to": "rest_idx",
                           "distance": "network_seconds"})
          .join(
              metro[["gid", "station"]].rename(columns={
                  "gid": "network_station_gid",
                  "station": "network_station",
              }),
              on="metro_idx",
          )
    )

    # 3) Compare per restaurant.
    df = rest_v.reset_index().rename(columns={"index": "rest_idx"}).merge(
        network, on="rest_idx", how="left",
    )
    df["match"] = df["euclid_station_gid"] == df["network_station_gid"]
    n_match, n_total = int(df["match"].sum()), len(df)
    print(f"agreement: {n_match}/{n_total} restaurants ({n_match / n_total:.0%})")
    print()
    print("disagreements:")
    print(df[~df["match"]][["place", "euclid_station",
                            "network_station", "network_seconds"]]
          .to_string(index=False))

    # 4) Plot. Voronoi cells faintly underneath, restaurants coloured
    # green when the two methods agree and red when they don't.
    fig, ax = plt.subplots(figsize=(11, 11))
    boundary_gdf.boundary.plot(ax=ax, color="black", linewidth=1)
    cells.plot(ax=ax, alpha=0.15, edgecolor="white", cmap="tab20")
    metro.plot(ax=ax, color="black", marker="s", markersize=18, zorder=4)
    df[df["match"]].plot(ax=ax, color="#2ca02c", markersize=40, zorder=6,
                         label=f"agree ({n_match})")
    df[~df["match"]].plot(ax=ax, color="#d62728", markersize=60, zorder=7,
                          label=f"disagree ({n_total - n_match})")
    ax.set_title(f"Tverskoy district - Voronoi vs network metro · "
                 f"agreement {n_match}/{n_total}")
    ax.legend(loc="upper right")
    ax.set_axis_off()
    plt.show()
