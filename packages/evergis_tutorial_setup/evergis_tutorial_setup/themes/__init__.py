# -*- coding: utf-8 -*-
"""Theme subpackages live here.

Each theme is a Python subpackage:

* ``themes/<theme>/__init__.py`` declares ``THEME = ThemeConfig(...)``.
* Sibling modules (``themes/<theme>/<layer>.py``) declare ``LAYER``
  constants - one layer per file, file stem becomes the short name.
* Optional helpers like ``<layer>_data.py`` (with ``ROWS = [...]``)
  sit alongside their layer module.

The runner discovers everything by walking this package - no
explicit registration needed.
"""
