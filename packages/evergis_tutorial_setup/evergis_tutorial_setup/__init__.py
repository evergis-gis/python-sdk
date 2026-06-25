# -*- coding: utf-8 -*-
"""Tutorial demo-data setup: provisions folders, layers and companion
maps in an EverGIS instance for the evergis_tools tutorial.

Entry points:

* CLI -> ``python -m evergis_tutorial_setup themes <names> [--force]``
* API -> ``from evergis_tutorial_setup import setup``

Themes live in ``evergis_tutorial_setup.themes.*``. Each theme is a Python
subpackage whose ``__init__.py`` declares a ``THEME = ThemeConfig(...)``
and whose sibling modules declare individual layers as ``LAYER = ...``.
The runner discovers everything from the filesystem - no explicit
registration. See ``_runner.py`` for the orchestration.

Tutorial example scripts (mirrored into the EverGIS catalog by the
runner) live under ``packages/evergis_tools/examples/`` and are picked
up automatically when ``tutorial_setup`` runs from a monorepo checkout.
When the package is pip-installed without the surrounding repo, the
mirror step is skipped (the layers, folders and maps are still created).
"""

from __future__ import annotations

from ._runner import setup

__all__ = ["setup"]
