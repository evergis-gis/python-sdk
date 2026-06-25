# -*- coding: utf-8 -*-
"""Fixture rows for ``stations.py`` seed layer.

Four points covering every supported attribute type: string, float,
int, bool, datetime, json dict, and an Attachments list (with one row
having a real link, the rest None to demo the empty case).
"""

from __future__ import annotations

from datetime import datetime
from shapely.geometry import Point

from evergis_tools import Attachment


def _attach(name: str, link: str, *, mime: str, external: bool, date: str) -> dict:
    return Attachment(
        date=date, link=link, name=name, mimeType=mime, isExternal=external,
    ).model_dump(mode="json")


ROWS = [
    {"code": "MSK-01", "elevation_m": 156.3, "floors_visible": 5,
     "is_active": True,  "installed_at": datetime(2018, 4, 12, 8, 0, 0),
     "sensor_meta": {"vendor": "Davis"},
     "photos": [_attach("install.jpg", "https://example.com/MSK-01-install.jpg",
                        mime="image/jpeg", external=True,
                        date="2018-04-12T08:00:00.000000Z")],
     "geometry": Point(37.6208, 55.7539)},
    {"code": "MSK-02", "elevation_m": 142.0, "floors_visible": 8,
     "is_active": True,  "installed_at": datetime(2020, 9, 1, 12, 30, 0),
     "sensor_meta": {"vendor": "Vaisala"}, "photos": None,
     "geometry": Point(37.6017, 55.7314)},
    {"code": "MSK-03", "elevation_m": 178.5, "floors_visible": 3,
     "is_active": False, "installed_at": datetime(2015, 6, 20, 0, 0, 0),
     "sensor_meta": {"vendor": "DIY"}, "photos": None,
     "geometry": Point(37.6325, 55.8266)},
    {"code": "MSK-04", "elevation_m": None,  "floors_visible": None,
     "is_active": True,  "installed_at": None, "sensor_meta": None, "photos": None,
     "geometry": Point(37.6207, 55.7414)},
]
