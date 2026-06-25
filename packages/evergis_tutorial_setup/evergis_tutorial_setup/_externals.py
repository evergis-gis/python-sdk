# -*- coding: utf-8 -*-
"""Registry of layers managed by an external pipeline.

These layers are NOT created by ``apply_theme`` - they are shared,
read-only sample data (Overture seeds) owned by ``SAMPLE_DATA_OWNER``
(default ``edu``); themes reference them but never create them. The
registry exists so cross-references resolve at apply time: a
``LayerQuery.eql_refs={"places": "overture_places"}`` or a
``MapLayerRef(short="overture_districts")`` validates against the union
of local layers + ``EXTERNAL_LAYERS``. A typo fails fast with a list of
valid keys.

Values are documentation strings (origin / owner / notes) and do not
affect resolution - only the keys matter.
"""

from __future__ import annotations


EXTERNAL_LAYERS: dict[str, str] = {
    "overture_places":         "sample-data pipeline (Overture)",
    "overture_divisions":      "sample-data pipeline (Overture)",
    "overture_districts":      "sample-data pipeline (Overture)",
    "overture_buildings":      "sample-data pipeline (Overture)",
    "overture_streets":        "sample-data pipeline (Overture)",
    "overture_metro_stations": "sample-data pipeline (Overture)",
}


__all__ = ["EXTERNAL_LAYERS"]
