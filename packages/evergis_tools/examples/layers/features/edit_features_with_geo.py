"""Edit attribute values AND geometry of the seed Point layer by row id.

Reads + edits ``evg_stations`` (Point, populated with 4 rows
by the ``features`` theme):

    .venv/bin/python -m evergis_tutorial_setup themes features

Touches every supported attribute type AND geometry in the update -
STRING, INT64, DOUBLE, BOOLEAN, DATETIME, JSON, JSON+Attachments,
Point.

Re-run to reset the seed:
    python -m evergis_tutorial_setup themes features --force
"""

from datetime import datetime

import geopandas as gpd
from shapely.geometry import Point

from evergis_tools import Attachment, Client
from evergis_tools.eql import eql_query_to_geodataframe
from evergis_tools.features import edit_layer_by_gdf


SOURCE_LAYER_SHORT = "evg_stations"
SRID = 4326


def _attach(name: str, link: str, *, mime: str, external: bool, date: str) -> dict:
    return Attachment(
        date=date, link=link, name=name, mimeType=mime, isExternal=external,
    ).model_dump(mode="json")


def _show(client, layer, label):
    gdf = eql_query_to_geodataframe(
        f"SELECT gid, code, elevation_m, floors_visible, is_active,"
        f" installed_at, sensor_meta, photos, geometry"
        f" FROM {layer} ORDER BY gid",
        client,
    )
    gdf["lon"] = gdf.geometry.x.round(4)
    gdf["lat"] = gdf.geometry.y.round(4)
    print(f"{label}:")
    print(gdf.drop(columns="geometry").to_string(index=False))


with Client() as client:
    username = client.account.get_user_info().username
    target_layer = f"{username}.{SOURCE_LAYER_SHORT}"

    _show(client, target_layer, "BEFORE")

    edits = gpd.GeoDataFrame(
        [
            {"gid": 1, "code": "MSK-01a",                                # STRING
             "elevation_m": 158.0,                                        # DOUBLE
             "floors_visible": 6,                                         # INT64
             "is_active": False,                                          # BOOLEAN
             "installed_at": datetime(2018, 4, 12, 8, 30, 0),             # DATETIME
             "sensor_meta": {"vendor": "Davis", "model": "VP2+"},         # JSON
             "photos": [                                                  # JSON+Attachments
                 _attach("install.jpg",
                         "https://example.com/MSK-01-install.jpg",
                         mime="image/jpeg", external=True,
                         date="2018-04-12T08:00:00.000000Z"),
                 _attach("upgrade-2026.jpg",
                         "https://example.com/MSK-01-upgrade.jpg",
                         mime="image/jpeg", external=True,
                         date="2026-05-09T10:00:00.000000Z"),
             ],
             "geometry": Point(37.6300, 55.7600)},                        # Point
            {"gid": 3, "is_active": True,
             "geometry": Point(37.6330, 55.8270)},
        ],
        crs=f"EPSG:{SRID}",
    )
    edit_layer_by_gdf(
        client=client, gdf=edits, layer_name=target_layer,
        target_sr=SRID, geometry_type="Point",
        id_column="gid", log=False,
    )

    print()
    _show(client, target_layer, "AFTER")
