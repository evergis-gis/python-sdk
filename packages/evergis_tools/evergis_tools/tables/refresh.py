# -*- coding: utf-8 -*-
"""Materialized view refresh utilities for EverGIS."""

import logging

from evergis_api import Client
from evergis_api.schemas import (
    CreateViewFromQueryDc,
    DetailedTableInfoDc,
    MaterializedViewConfigurationDc,
)

from ..layers._utils import _normalize_layer_name

logger = logging.getLogger(__name__)


def refresh_materialized_view(
    client: Client,
    view_name: str,
    *,
    log: bool = True,
) -> DetailedTableInfoDc:
    """Refresh materialized view by recreating it with current data.

    Reads the existing view configuration and recreates it with override=True.
    The view must already exist and be a materialized view.

    Args:
        client: EverGIS API client
        view_name: Name of the materialized view to refresh
        log: Enable logging output

    Returns:
        DetailedTableInfoDc with refreshed view information

    Raises:
        ValueError: If the resource is not a materialized view

    Example:
        >>> refresh_materialized_view(client, "my_cached_data")
    """
    if log:
        logger.info(f"Refreshing materialized view: '{view_name}'")

    view_name = _normalize_layer_name(client, view_name, log=log)

    # Get current configuration
    table_info = client.tables.get_table_info(name=view_name)
    config = table_info.configuration

    if not isinstance(config, MaterializedViewConfigurationDc):
        raise ValueError(
            f"'{view_name}' is not a materialized view (type: {type(config).__name__})"
        )

    if log:
        logger.debug(f"Current EQL: {config.eql}")

    # Recreate with override
    request = CreateViewFromQueryDc(
        viewName=view_name,
        eql=config.eql,
        isMaterialized=True,
        override=True,
        parameters=config.eqlParameters,
    )

    try:
        result = client.tables.create_view_from_query(body=request)

        if log:
            logger.info(f"Materialized view '{view_name}' refreshed successfully")
        return result
    except Exception as e:
        if log:
            logger.error(f"Error refreshing materialized view '{view_name}': {e}")
        raise
