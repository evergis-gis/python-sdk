# -*- coding: utf-8 -*-
"""Fixture rows for ``logs.py`` seed layer."""

from __future__ import annotations

from datetime import datetime

from evergis_tools import Attachment


def _attach(name: str, link: str, *, mime: str, external: bool, date: str) -> dict:
    return Attachment(
        date=date, link=link, name=name, mimeType=mime, isExternal=external,
    ).model_dump(mode="json")


ROWS = [
    {"station_code": "MSK-01", "metric": "temp_c", "value": -3.7,
     "sample_count": 24, "is_anomaly": False,
     "recorded_at": datetime(2026, 1, 15, 9, 0, 0),
     "raw_payload": {"sensor": "DHT22"},
     "attachments": [_attach("calibration.pdf",
                             "https://example.com/calibration.pdf",
                             mime="application/pdf", external=True,
                             date="2026-01-15T09:00:00.000000Z")]},
    {"station_code": "MSK-02", "metric": "wind_ms", "value": 12.4,
     "sample_count": 60, "is_anomaly": False,
     "recorded_at": datetime(2026, 1, 15, 9, 5, 0),
     "raw_payload": {"sensor": "Davis-6410"}, "attachments": None},
    {"station_code": "MSK-01", "metric": "humidity_pct", "value": 78.0,
     "sample_count": 24, "is_anomaly": False,
     "recorded_at": datetime(2026, 1, 15, 9, 0, 0),
     "raw_payload": None, "attachments": None},
    {"station_code": "MSK-03", "metric": "temp_c", "value": -2.1,
     "sample_count": 18, "is_anomaly": False,
     "recorded_at": datetime(2026, 1, 15, 9, 10, 0),
     "raw_payload": {"sensor": "BME280"}, "attachments": None},
]
