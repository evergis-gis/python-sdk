# -*- coding: utf-8 -*-
"""Utilities for working with EQL queries."""

from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
import logging
from .logging import get_logger, temporary_level
from evergis_api import Client

_LOG = get_logger(__name__)

if TYPE_CHECKING:
    import geopandas as gpd
    import pandas as pd
    from evergis_api.schemas import EqlRequestDc, PagedFeaturesListDc


# ---------------------------------------------------------------------------
# Shared helpers (used by both sync and async versions)
# ---------------------------------------------------------------------------

def _build_eql_request(
    query: str,
    chunk_size: int,
    offset: int,
    columns: Optional[Dict[str, str]],
    ds: Optional[str],
    geometry_field: Optional[str],
    id_field: Optional[str],
    parameters: Optional[Dict[str, Any]],
    with_geom: bool,
) -> "EqlRequestDc":
    """Build EqlRequestDc for a single chunk."""
    from evergis_api import schemas

    return schemas.EqlRequestDc(
        query=query,
        limit=chunk_size,
        offset=offset,
        columns=columns,
        ds=ds,
        geometryField=geometry_field,
        idField=id_field,
        parameters=parameters,
        withgeom=with_geom,
    )


def _rows_from_result(eql_result: "PagedFeaturesListDc") -> List[dict]:
    """Extract property dicts from EQL result."""
    return [f.properties if f.properties else {} for f in eql_result.features]


def _is_last_chunk(eql_result: "PagedFeaturesListDc", chunk_size: int) -> bool:
    """Check if this was the last chunk of data."""
    return not eql_result.features or len(eql_result.features) < chunk_size


def _combine_geodataframes(
    chunks: list,
    target_crs: Optional[str],
) -> "gpd.GeoDataFrame":
    """Combine list of GeoDataFrame chunks into one."""
    import geopandas as gpd
    import pandas as pd

    if not chunks:
        return gpd.GeoDataFrame(columns=["geometry"], crs=target_crs)

    combined = pd.concat(chunks, ignore_index=True)

    if hasattr(chunks[0], "crs"):
        return gpd.GeoDataFrame(combined, crs=chunks[0].crs)
    return gpd.GeoDataFrame(combined, crs=target_crs)


# Map the *AttributeConfigurationDc subclass to a friendly column kind.
_COLUMN_KIND = {
    "GeometryAttributeConfigurationDc": "geometry",
    "StringAttributeConfigurationDc": "string",
    "CalculatedAttributeConfigurationDc": "calculated",
}


def _describe_columns(raw: list) -> List[Dict[str, Any]]:
    """Turn the ``get_query_description`` result into friendly dicts.

    The endpoint returns ``*AttributeConfigurationDc`` instances; the
    geometry column is the ``GeometryAttributeConfigurationDc`` one. We
    expose ``name`` / ``type`` / ``kind`` / ``is_geometry`` so callers do
    not touch the low-level Dc classes.
    """
    columns: List[Dict[str, Any]] = []
    for attr in raw:
        kind = _COLUMN_KIND.get(type(attr).__name__, "attribute")
        columns.append(
            {
                "name": getattr(attr, "attributeName", None),
                "type": getattr(attr, "type", None),
                "kind": kind,
                "is_geometry": kind == "geometry",
            }
        )
    return columns


def _geometry_field_from_columns(columns: List[Dict[str, Any]]) -> Optional[str]:
    """Return the name of the geometry column, or None if there isn't one."""
    return next((c["name"] for c in columns if c["is_geometry"]), None)


# ---------------------------------------------------------------------------
# Sync API
# ---------------------------------------------------------------------------

def eql_query_to_dataframe(
    query: str,
    client: Client,
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

    Loads data in chunks automatically. Use this for aggregate queries,
    tabular data, or any query where geometry is not needed.

    Args:
        query: EQL query string
        client: EverGIS API client (sync)
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
        >>> client = Client(base_url="...", sb_token="...")
        >>> df = eql_query_to_dataframe(
        ...     "SELECT count(*) as cnt, type FROM john_doe.layer GROUP BY type",
        ...     client
        ... )
    """
    import pandas as pd

    log = logger if logger is not None else _LOG

    with temporary_level(log, log_level):
        log.debug("Loading EQL query in chunks of %s (no geometry)", chunk_size)

        all_rows: list[dict] = []
        offset = 0

        while True:
            eql_request = _build_eql_request(
                query, chunk_size, offset, columns, ds,
                None, id_field, parameters, False,
            )
            log.debug("Loading chunk: offset=%s, limit=%s", offset, chunk_size)

            # Backend errors (invalid EQL, 4xx/5xx, network timeouts)
            # propagate to the caller. A silent ``try/except`` here used to
            # turn any failure into an empty DataFrame with no signal.
            eql_result = client.eql.get_paged_query_result(body=eql_request)

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


def eql_query_to_geodataframe(
    query: str,
    client: Client,
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
    log_level: Optional[Union[str, int]] = None
) -> 'gpd.GeoDataFrame':
    """Execute EQL query and return result as GeoDataFrame.

    Loads data in chunks automatically.

    Args:
        query: EQL query string
        client: EverGIS API client (sync)
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
        >>> client = Client(base_url="...", sb_token="...")
        >>> gdf = eql_query_to_geodataframe("SELECT * FROM john_doe.places", client)
        >>>
        >>> # let the wrapper find the geometry column (geometry vs geom)
        >>> gdf = eql_query_to_geodataframe("SELECT * FROM john_doe.places", client,
        ...                                 geometry_field="auto")
        >>>
        >>> gdf = eql_query_to_geodataframe("SELECT * FROM john_doe.places", client,
        ...                                 chunk_size=500, target_crs='EPSG:4326')
    """
    from .geodataframes import paged_features_to_geodataframe

    log = logger if logger is not None else _LOG

    with temporary_level(log, log_level):
        log.debug("Loading EQL query in chunks of %s", chunk_size)

        # geometry_field="auto": ask the server for the column schema once
        # and use whichever column is the geometry one (fallback "geometry").
        # Costs a single lightweight /eql/description call, independent of
        # result size.
        if geometry_field == "auto":
            try:
                detected = _geometry_field_from_columns(
                    eql_describe(query, client, ds=ds, parameters=parameters, logger=log)
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

            # Backend errors propagate to the caller (see the same note in
            # ``eql_query_to_dataframe`` above).
            eql_result = client.eql.get_paged_query_result(body=eql_request)

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


def eql_describe(
    query: str,
    client: Client,
    *,
    ds: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None,
    log_level: Optional[Union[str, int]] = None,
) -> List[Dict[str, Any]]:
    """Describe an EQL query's output columns without fetching any rows.

    Thin wrapper over ``client.eql.get_query_description``
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
        >>> for col in eql_describe("SELECT * FROM john_doe.my_layer", client):
        ...     print(col["name"], col["type"], col["kind"])
    """
    from evergis_api import schemas

    log = logger if logger is not None else _LOG
    with temporary_level(log, log_level):
        request = schemas.EqlRequestDc(query=query, ds=ds, parameters=parameters)
        log.debug("Describing EQL query columns")
        raw = client.eql.get_query_description(body=request)
        return _describe_columns(raw)
