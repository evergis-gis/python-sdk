# -*- coding: utf-8 -*-
"""Path resolver for tutorial themes.

Every theme owns the same folder layout under
``{username}:{PROJECT_PATH}/<theme>/``:

* ``scripts/``  - mirrored ``examples/<theme>/`` tree (read-only copy)
* ``data/``     - seed layers the theme pre-creates (sandboxes, fixtures)
* ``results/``  - output of examples that create their own layers

``ThemePaths`` centralises that layout so themes never glue path strings
themselves. ``PROJECT_PATH`` and ``RESOURCE_PREFIX`` come from env
(``.env`` is loaded once by ``evergis_tools.Client``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def project_path() -> str:
    """``PROJECT_PATH`` env value with the trailing slash stripped."""
    return os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")


def resource_prefix() -> str:
    """``RESOURCE_PREFIX`` env value (default ``evg``)."""
    return os.getenv("RESOURCE_PREFIX", "evg")


def sample_data_owner() -> str:
    """``SAMPLE_DATA_OWNER`` env value (default ``edu``).

    Owner of the shared, read-only sample-data layers (Overture seeds,
    see ``EXTERNAL_LAYERS``) that tutorial themes reference but do not
    create. Local per-user seeds keep the caller's username.
    """
    return os.getenv("SAMPLE_DATA_OWNER", "edu")


@dataclass(frozen=True)
class ThemePaths:
    """Resolved catalog paths for a single tutorial theme."""

    username: str
    theme_name: str

    @property
    def root(self) -> str:
        """``{username}:{PROJECT_PATH}/<theme>``"""
        return f"{self.username}:{project_path()}/{self.theme_name}"

    @property
    def scripts(self) -> str:
        return f"{self.root}/scripts"

    @property
    def data(self) -> str:
        return f"{self.root}/data"

    @property
    def results(self) -> str:
        return f"{self.root}/results"

    def layer_system_name(self, short: str, *, external: bool = False) -> str:
        """Full system name: ``{owner}.{RESOURCE_PREFIX}_{short}``.

        ``short`` is expected to already include the theme tag (e.g.
        ``"features_stations"``, ``"overture_places"``) - that keeps the
        names unique across themes and lets a single grep find all
        resources a theme created.

        ``external=True`` (the short names an ``EXTERNAL_LAYERS`` entry,
        i.e. shared sample data) builds the name under
        ``sample_data_owner()`` instead of the caller's username.
        """
        owner = sample_data_owner() if external else self.username
        return f"{owner}.{resource_prefix()}_{short}"


__all__ = ["ThemePaths", "project_path", "resource_prefix", "sample_data_owner"]
