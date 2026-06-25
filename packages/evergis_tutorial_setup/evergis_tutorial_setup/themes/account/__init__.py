# -*- coding: utf-8 -*-
"""Theme: ``account`` - auth / user / role administration.

Account examples are headless management ops (login, get current user,
list users, list roles, create users, manage roles). The companion map
is a landing page only.
"""

from ..._config import MapConfig, ThemeConfig

THEME = ThemeConfig(
    name="account",
    alias="account tutorial",
    depends_on=[],
    folders=("scripts",),
    map=MapConfig(),   # landing page, no layers
)
