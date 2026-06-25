# -*- coding: utf-8 -*-
"""High-level utilities for EverGIS tables and materialized views."""

from .columns import add_columns, modify_table_columns, remove_columns
from .create import create_materialized_view, create_materialized_view_from_layer
from .refresh import refresh_materialized_view

__all__ = [
    # Materialized views
    "create_materialized_view",
    "create_materialized_view_from_layer",
    "refresh_materialized_view",
    # Column operations on Table resources
    "add_columns",
    "remove_columns",
    "modify_table_columns",
]
