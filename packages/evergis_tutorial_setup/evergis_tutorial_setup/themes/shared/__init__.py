# -*- coding: utf-8 -*-
"""Theme: ``shared`` - read-only query layers reused by multiple themes.

Wraps externally-managed Overture seeds (``overture_places``,
``overture_districts``) with thin parametrised virtual layers used by
the ``eql`` / ``widgets`` / ``layers`` examples and by their companion
maps. No companion map of its own.

* ``places_qry``        - SELECT * FROM places + three optional filters
* ``distr_poi_count``   - CTE + LEFT JOIN: POI count per Moscow district
"""

from ..._config import ThemeConfig  # noqa: TID252 (parent-pkg private module)

THEME = ThemeConfig(
    name="shared",
    alias="shared base - derived query layers over Overture",
    depends_on=[],
    map=None,
)
