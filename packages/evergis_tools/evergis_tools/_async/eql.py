# -*- coding: utf-8 -*-
"""Async EQL query utilities."""

from typing import Any, Dict, Optional, Union, TYPE_CHECKING
import logging

from ..logging import get_logger, temporary_level
from ..eql import (
    _build_eql_request,
    _combine_geodataframes,
    _describe_columns,
    _geometry_field_from_columns,
    _is_last_chunk,
    _rows_from_result,
)

if TYPE_CHECKING:
    import geopandas as gpd
    import pandas as pd
    from evergis_api import AsyncClient

_LOG = get_logger(__name__)


async def eql_query_to_dataframe(
    query: str,
    client: "AsyncClient",
    chunk_size: int = 1000,
    columns: Optional[Dict[str, str]] = None,
    ds: Optional[str] = None,
    id_field: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    *,
    logger: Optional[logging.Logger] = None,
    log_level: Optional[Union[str, int]] = None,
) -> "pd.DataFrame":
    """Execute EQL query and return result as pandas DataFrame (no geometry).

    Async version. Loads data in chunks automatically.

    Args:
        query: EQL query string
        client: EverGIS API async client
        chunk_size: Chunk size for loading (default 1000)
        columns: Columns dict
        ds: Data source name
        id_field: ID field name
        parameters: EQL query parameters
        logger: Custom logger
        log_level: Temporary log level

    Returns:
        pandas DataFrame with query results

    Example:
        >>> from evergis_api import AsyncClient
        >>> from evergis_tools._async.eql import eql_query_to_dataframe
        >>>
        >>> async with AsyncClient(base_url="...", sb_token="...") as client:
        ...     df = await eql_query_to_dataframe(
        ...         "SELECT count(*) as cnt, type FROM john_doe.layer GROUP BY type",
        ...         client
        ...     )
    """
    import pandas as pd

    log = logger if logger is not None else _LOG

    with temporary_level(log, log_level):
        log.debug("Loading EQL query in chunks of %s (no geometry, async)", chunk_size)

        all_rows: list[dict] = []
        offset = 0

        while True:
            eql_request = _build_eql_request(
                query, chunk_size, offset, columns, ds,
                None, id_field, parameters, False,
            )
            log.debug("Loading chunk: offset=%s, limit=%s", offset, chunk_size)

            # Backend errors propagate to the caller; the previous silent
            # ``try/except`` turned any failure into an empty DataFrame.
            eql_result = await client.eql.get_paged_query_result(body=eql_request)

            if not eql_result.features:
                log.debug("No more data")
                break

            all_rows.extend(_rows_from_result(eql_result))
            log.debug("Loaded chunk with %s rows. Total: %s", len(eql_result.features), len(all_rows))

            if _is_last_chunk(eql_result, chunk_size):
                break

            offset += chunk_size

        df = pd.DataFrame(all_rows)
        log.debug("Created DataFrame with %s rows, %s columns", len(df), len(df.columns))
        return df


async def eql_query_to_geodataframe(
    query: str,
    client: "AsyncClient",
    chunk_size: int = 1000,
    columns: Optional[Dict[str, str]] = None,
    ds: Optional[str] = None,
    geometry_field: Optional[str] = "geometry",
    id_field: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    with_geom: Optional[bool] = True,
    target_crs: Optional[str] = None,
    *,
    logger: Optional[logging.Logger] = None,
    log_level: Optional[Union[str, int]] = None,
) -> "gpd.GeoDataFrame":
    """Execute EQL query and return result as GeoDataFrame.

    Async version. Loads data in chunks automatically.

    Args:
        query: EQL query string
        client: EverGIS API async client
        chunk_size: Chunk size for loading (default 1000)
        columns: Columns dict
        ds: Data source name
        geometry_field: Geometry field name. Pass ``"auto"`` to detect it
            from the query schema (one ``/eql/description`` call) when the
            column may be ``geometry`` or ``geom``; defaults to ``"geometry"``.
        id_field: ID field name
        parameters: EQL query parameters
        with_geom: Include geometry in response
        target_crs: Target CRS (e.g. 'EPSG:4326', 'EPSG:3857')
        logger: Custom logger
        log_level: Temporary log level

    Returns:
        GeoDataFrame with query results

    Example:
        >>> from evergis_api import AsyncClient
        >>> from evergis_tools._async.eql import eql_query_to_geodataframe
        >>>
        >>> async with AsyncClient(base_url="...", sb_token="...") as client:
        ...     gdf = await eql_query_to_geodataframe(
        ...         "SELECT * FROM john_doe.layer", client
        ...     )
        ...     # let the wrapper find the geometry column (geometry vs geom)
        ...     gdf = await eql_query_to_geodataframe(
        ...         "SELECT * FROM john_doe.layer", client, geometry_field="auto"
        ...     )
    """
    from ..geodataframes import paged_features_to_geodataframe

    log = logger if logger is not None else _LOG

    with temporary_level(log, log_level):
        log.debug("Loading EQL query in chunks of %s (async)", chunk_size)

        # geometry_field="auto": ask the server for the column schema once
        # and use whichever column is the geometry one (fallback "geometry").
        # Costs a single lightweight /eql/description call, independent of
        # result size.
        if geometry_field == "auto":
            try:
                detected = _geometry_field_from_columns(
                    await eql_describe(query, client, ds=ds, parameters=parameters, logger=log)
                )
            except Exception as exc:
                log.debug("auto geometry_field detection failed: %s", exc)
                detected = None
            geometry_field = detected or "geometry"
            log.debug("auto geometry_field resolved to %r", geometry_field)

        all_chunks = []
        offset = 0
        total_loaded = 0

        while True:
            eql_request = _build_eql_request(
                query, chunk_size, offset, columns, ds,
                geometry_field, id_field, parameters, with_geom,
            )
            log.debug("Loading chunk: offset=%s, limit=%s", offset, chunk_size)

            # Backend errors propagate to the caller (same note as in the
            # dataframe path above).
            eql_result = await client.eql.get_paged_query_result(body=eql_request)

            if not eql_result.features:
                log.debug("No more data")
                break

            chunk_gdf = paged_features_to_geodataframe(
                eql_result, target_crs=target_crs, logger=log
            )

            if len(chunk_gdf) == 0:
                log.debug("Empty chunk, stopping")
                break

            all_chunks.append(chunk_gdf)
            total_loaded += len(chunk_gdf)
            log.debug("Loaded chunk with %s rows. Total: %s", len(chunk_gdf), total_loaded)

            if _is_last_chunk(eql_result, chunk_size):
                break

            offset += chunk_size

        result = _combine_geodataframes(all_chunks, target_crs)
        log.debug("Created GeoDataFrame with %s rows, CRS: %s", len(result), result.crs)
        return result


async def eql_describe(
    query: str,
    client: "AsyncClient",
    *,
    ds: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None,
    log_level: Optional[Union[str, int]] = None,
) -> list:
    """Describe an EQL query's output columns without fetching any rows.

    Async version. Thin wrapper over ``client.eql.get_query_description``
    (``POST /eql/description``). Returns one dict per output column:

    * ``name`` - column name
    * ``type`` - value type (e.g. ``"String"``, ``"Int64"``); for the
      geometry column this is the geometry type (``"Point"``, ...)
    * ``kind`` - ``"geometry"`` / ``"string"`` / ``"calculated"`` / ``"attribute"``
    * ``is_geometry`` - True for the geometry column

    Use it to validate a query, list its columns and types, or find the
    geometry field before fetching (see ``geometry_field="auto"`` in
    :func:`eql_query_to_geodataframe`).

    Example:
        >>> from evergis_api import AsyncClient
        >>> from evergis_tools._async.eql import eql_describe
        >>>
        >>> async with AsyncClient(base_url="...", sb_token="...") as client:
        ...     for col in await eql_describe("SELECT * FROM john_doe.my_layer", client):
        ...         print(col["name"], col["type"], col["kind"])
    """
    from evergis_api import schemas

    log = logger if logger is not None else _LOG
    with temporary_level(log, log_level):
        request = schemas.EqlRequestDc(query=query, ds=ds, parameters=parameters)
        log.debug("Describing EQL query columns (async)")
        raw = await client.eql.get_query_description(body=request)
        return _describe_columns(raw)
