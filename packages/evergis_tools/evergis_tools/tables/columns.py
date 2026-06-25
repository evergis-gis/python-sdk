# -*- coding: utf-8 -*-
"""Column-level operations on EverGIS Table resources.

These helpers work with the **Table** resource type (catalog resources
without geometry), via ``client.tables.update_table`` and
:class:`UpdateTableDc`. For column-level operations on **Layer**
resources, see :func:`evergis_tools.layers.add_layer_attribute` and
friends - the server handles the underlying column on its own from
the layer's PATCH call, so no separate ``PATCH /tables`` step is
needed.
"""

from typing import Any, Dict, List, Optional
import logging

from evergis_api import Client
from evergis_api.schemas import ColumnDescriptionDc, DetailedTableInfoDc, UpdateTableDc

from ..layers._utils import _normalize_layer_name

logger = logging.getLogger(__name__)


def _to_column_objects(columns: List[Dict[str, Any]]) -> List[ColumnDescriptionDc]:
    """Convert ``{"name", "type"}`` dicts to ColumnDescriptionDc."""
    if any("nullable" in col or "isNullable" in col for col in columns):
        logger.warning(
            "Per-column nullability is no longer supported by the EverGIS API "
            "(isNullable was removed from ColumnDescriptionDc); the key is ignored"
        )
    return [
        ColumnDescriptionDc(
            name=col["name"],
            type=col["type"],
        )
        for col in columns
    ]


def add_columns(
    client: Client,
    table_name: str,
    columns: List[Dict[str, Any]],
    *,
    log: bool = True,
) -> DetailedTableInfoDc:
    """Add columns to an EverGIS Table.

    Args:
        client: EverGIS API client.
        table_name: Table name (username prefix added when missing).
        columns: List of column descriptions:
            ``[{"name": "col", "type": "String"}, ...]``.
        log: Enable logging output.

    Supported types: ``String``, ``Int32``, ``Int64``, ``Double``,
    ``Boolean``, ``DateTime``, ``Geometry``.

    Returns:
        DetailedTableInfoDc with the updated table information.

    Example:
        >>> add_columns(client, "john_doe.my_table", [
        ...     {"name": "population", "type": "Int32"},
        ...     {"name": "area_name", "type": "String"},
        ... ])
    """
    return modify_table_columns(client, table_name, add_columns=columns, log=log)


def remove_columns(
    client: Client,
    table_name: str,
    column_names: List[str],
    *,
    log: bool = True,
) -> DetailedTableInfoDc:
    """Remove columns from an EverGIS Table.

    Args:
        client: EverGIS API client.
        table_name: Table name (username prefix added when missing).
        column_names: Names of columns to remove.
        log: Enable logging output.

    Returns:
        DetailedTableInfoDc with the updated table information.

    Example:
        >>> remove_columns(client, "john_doe.my_table", ["old_col", "unused"])
    """
    return modify_table_columns(client, table_name, remove_columns=column_names, log=log)


def modify_table_columns(
    client: Client,
    table_name: str,
    add_columns: Optional[List[Dict[str, Any]]] = None,
    remove_columns: Optional[List[str]] = None,
    *,
    log: bool = True,
) -> DetailedTableInfoDc:
    """Add and/or remove columns in a single PATCH call.

    Args:
        client: EverGIS API client.
        table_name: Table name (username prefix added when missing).
        add_columns: Columns to add (same shape as :func:`add_columns`).
        remove_columns: Names of columns to remove.
        log: Enable logging output.

    Returns:
        DetailedTableInfoDc with the updated table information.

    Raises:
        ValueError: If both ``add_columns`` and ``remove_columns`` are empty.

    Example:
        >>> modify_table_columns(
        ...     client, "john_doe.my_table",
        ...     add_columns=[{"name": "new_field", "type": "String"}],
        ...     remove_columns=["old_field"],
        ... )
    """
    if not add_columns and not remove_columns:
        raise ValueError("Nothing to do: both add_columns and remove_columns are empty")

    table_name = _normalize_layer_name(client, table_name, log=log)

    update_request = UpdateTableDc(
        name=table_name,
        columnsAdd=_to_column_objects(add_columns) if add_columns else None,
        columnsDelete=remove_columns or None,
    )

    try:
        result = client.tables.update_table(name=table_name, body=update_request)

        if log:
            ops = []
            if add_columns:
                ops.append(f"added {[col['name'] for col in add_columns]}")
            if remove_columns:
                ops.append(f"removed {remove_columns}")
            logger.info(f"Modified table {table_name}: {', '.join(ops)}")
        return result
    except Exception as e:
        if log:
            logger.error(f"Error modifying table {table_name}: {e}")
        raise
