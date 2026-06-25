# -*- coding: utf-8 -*-
"""Materialized view creation utilities for EverGIS."""

from typing import Any, Dict, List, Optional
import logging

from evergis_api import Client
from evergis_api.schemas import (
    CreateViewFromQueryDc,
    CreateViewFromQueryLayerDc,
    DetailedTableInfoDc,
)

from ..layers._utils import _normalize_layer_name
from .._utils import _remove_none_values
from .._errors import raise_conflict_as_exists

logger = logging.getLogger(__name__)


def create_materialized_view(
    client: Client,
    view_name: str,
    eql: str,
    *,
    gid_column_name: str = "gid",
    add_gid_column: bool = False,
    override: bool = False,
    drop_cascade: bool = False,
    parameters: Optional[Dict[str, Any]] = None,
    log: bool = True,
) -> DetailedTableInfoDc:
    """Create materialized view from EQL query.

    Args:
        client: EverGIS API client
        view_name: Name for the materialized view
        eql: EQL query defining the view data
        gid_column_name: Name of the GID column (default "gid")
        add_gid_column: Add auto-incrementing GID column
        override: Recreate if already exists
        drop_cascade: Drop with cascade when overriding
        parameters: EQL query parameters (e.g. {"@status": "active"})
        log: Enable logging output

    Returns:
        DetailedTableInfoDc with created view information

    Example:
        >>> result = create_materialized_view(
        ...     client,
        ...     "my_cached_data",
        ...     "SELECT * FROM john_doe.parcels WHERE area > 1000",
        ...     override=True
        ... )
    """
    if log:
        logger.info(f"Creating materialized view: '{view_name}'")

    view_name = _normalize_layer_name(client, view_name, log=log)

    request = CreateViewFromQueryDc(
        viewName=view_name,
        eql=eql,
        isMaterialized=True,
        gidColumnName=gid_column_name,
        addGidColumn=add_gid_column,
        override=override,
        dropCascade=drop_cascade,
        parameters=parameters,
    )
    request = _remove_none_values(request)

    try:
        if log:
            logger.debug(f"Request: {request.model_dump()}")

        result = client.tables.create_view_from_query(body=request)

        if log:
            logger.info(f"Materialized view '{view_name}' created successfully")
        return result
    except Exception as e:
        if log:
            logger.error(f"Error creating materialized view '{view_name}': {e}")
        raise_conflict_as_exists(e, resource=f"materialized view {view_name!r}")
        raise


def create_materialized_view_from_layer(
    client: Client,
    view_name: str,
    layer_name: str,
    *,
    gid_column_name: str = "gid",
    add_gid_column: bool = False,
    override: bool = False,
    drop_cascade: bool = False,
    conditions: Optional[List[str]] = None,
    parameters: Optional[Dict[str, Any]] = None,
    data_filter_id: Optional[str] = None,
    log: bool = True,
) -> DetailedTableInfoDc:
    """Create materialized view from existing layer.

    Args:
        client: EverGIS API client
        view_name: Name for the materialized view
        layer_name: Source layer name
        gid_column_name: Name of the GID column (default "gid")
        add_gid_column: Add auto-incrementing GID column
        override: Recreate if already exists
        drop_cascade: Drop with cascade when overriding
        conditions: List of filtering conditions
        parameters: Query parameters
        data_filter_id: Override data filter ID
        log: Enable logging output

    Returns:
        DetailedTableInfoDc with created view information

    Example:
        >>> result = create_materialized_view_from_layer(
        ...     client,
        ...     "parcels_cached",
        ...     "john_doe.parcels",
        ...     conditions=["area > 1000"],
        ...     override=True
        ... )
    """
    if log:
        logger.info(f"Creating materialized view '{view_name}' from layer '{layer_name}'")

    view_name = _normalize_layer_name(client, view_name, log=log)
    layer_name = _normalize_layer_name(client, layer_name, log=log)

    request = CreateViewFromQueryLayerDc(
        viewName=view_name,
        layerName=layer_name,
        isMaterialized=True,
        gidColumnName=gid_column_name,
        addGidColumn=add_gid_column,
        override=override,
        dropCascade=drop_cascade,
        conditions=conditions,
        parameters=parameters,
        dataFilterId=data_filter_id,
    )
    request = _remove_none_values(request)

    try:
        if log:
            logger.debug(f"Request: {request.model_dump()}")

        result = client.tables.create_view_from_query_layer(body=request)

        if log:
            logger.info(f"Materialized view '{view_name}' created from layer '{layer_name}'")
        return result
    except Exception as e:
        if log:
            logger.error(f"Error creating materialized view '{view_name}': {e}")
        raise_conflict_as_exists(e, resource=f"materialized view {view_name!r}")
        raise
