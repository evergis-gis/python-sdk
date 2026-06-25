"""DataSource (DS) connection helpers - catalog resources backed by
an external data store: Postgres, S3, ArcGIS, WMS, MosRu, Spark.

Each ``*DataSourceDc`` subclass goes to its own ``POST /ds/<type>``
endpoint on the server. This module hides that fan-out behind a
single ``create_data_source`` / ``update_data_source`` /
``test_data_source`` API: pick the right method by inspecting the
DTO's class, optionally resolve a catalog folder path into
``parentId``, optionally run ``test_connection`` first.

Universal operations (``get`` / ``delete`` / ``iter``) work on a
flat namespace - DataSource names are globally unique per
instance, independent of the catalog folder they're filed into.

Quick start::

    from evergis_api.schemas import PostgresDataSourceDc
    from evergis_tools import Client
    from evergis_tools.catalog.data_sources import create_data_source

    with Client() as client:
        create_data_source(client,
            PostgresDataSourceDc(
                name="john_doe.sales_db",
                alias="Sales Postgres",
                host="db.example",
                port=5432,
                database="sales",
                userName="reader",
                password="...",
                schema_="public",
            ),
            parent_path="john_doe/EverGIS Resources/Connections",
            test=True,
        )
"""

from __future__ import annotations

import logging
from typing import Optional

from evergis_api import ApiClientError, Client
from evergis_api.schemas import (
    ArcGisDataSourceDc,
    DataSourceDc,
    DataSourceType,
    MosRuDataSourceDc,
    PostgresDataSourceDc,
    S3DataSourceDc,
    SparkDataSourceDc,
    WmsDataSourceDc,
)

from .._errors import is_not_found, raise_conflict_as_exists
from .._http import silence_status_codes
from .folders import get_or_create_folder_by_path


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Per-type endpoint dispatch
# ---------------------------------------------------------------------------

# (create_method, update_method, [test_candidates])
# ``test_candidates`` is a list of method-name candidates: the
# generator has emitted both ``test_connection_<N>`` (one suffix
# per type from older OpenAPI specs) and a unified
# ``test_connection`` (newer specs dispatch by ``body.type`` on
# the server). We try the type-specific name first, then fall
# back to the generic one - that way the wrapper survives both
# autogen flavours without a hard pin.
_DISPATCH: dict[type, tuple[str, str, tuple[str, ...]]] = {
    ArcGisDataSourceDc:   ("create_arc_gis_data_source",   "update_arc_gis_data_source",   ("test_connection",)),
    PostgresDataSourceDc: ("create_data_source",           "update_data_source",           ("test_connection_2", "test_connection")),
    MosRuDataSourceDc:    ("create_mos_ru_data_source",    "update_mos_ru_data_source",    ("test_connection_1", "test_connection")),
    S3DataSourceDc:       ("create_s3_data_source",        "update_s3_data_source",        ("test_connection_3", "test_connection")),
    SparkDataSourceDc:    ("create_spark_data_source",     "update_spark_data_source",     ()),
    WmsDataSourceDc:      ("create_arc_gis_data_source_1", "update_arc_gis_data_source_1", ()),
}


def _resolve_dispatch(ds: DataSourceDc) -> tuple[str, str, tuple[str, ...]]:
    entry = _DISPATCH.get(type(ds))
    if entry is None:
        raise TypeError(
            f"Unsupported DataSourceDc subclass: {type(ds).__name__}. "
            f"Known: {[c.__name__ for c in _DISPATCH]}"
        )
    return entry


def _resolve_test_method(client: Client, candidates: tuple[str, ...]):
    """Return the first callable from ``candidates`` that exists on
    ``client.datasource``, or ``None`` if none of them does."""
    ds_client = client.datasource
    for name in candidates:
        if hasattr(ds_client, name):
            return getattr(ds_client, name)
    return None


# ---------------------------------------------------------------------------
# Create / Update / Test
# ---------------------------------------------------------------------------

def create_data_source(
    client: Client,
    ds: DataSourceDc,
    *,
    parent_id: Optional[str] = None,
    parent_path: Optional[str] = None,
    test: bool = False,
    log: bool = True,
) -> bool:
    """Create a DataSource connection.

    Args:
        client: EverGIS API client.
        ds: A populated ``*DataSourceDc`` instance. ``type`` field
            should match the subclass (the server uses it as a
            discriminator); subclasses ``ArcGisDataSourceDc`` /
            ``PostgresDataSourceDc`` / ``MosRuDataSourceDc`` /
            ``S3DataSourceDc`` / ``SparkDataSourceDc`` /
            ``WmsDataSourceDc`` are recognised.
        parent_id: ID of the catalog folder to file the resource
            under. Mutually exclusive with ``parent_path``.
        parent_path: Catalog folder path (``"john_doe:Projects/Connections"``);
            auto-created if missing.
        test: When True, call the type's ``test_connection`` endpoint
            before creating; raises ``RuntimeError`` if the test
            fails. Skipped for Spark / WMS (no test endpoint).
        log: Enable logging.

    Returns:
        Server response (``True`` on success).

    Raises:
        TypeError: ``ds`` is not a known DataSourceDc subclass.
        ValueError: both ``parent_id`` and ``parent_path`` provided.
        RuntimeError: ``test=True`` and the test failed.
    """
    create_name, _, test_candidates = _resolve_dispatch(ds)

    if parent_id and parent_path:
        raise ValueError("Pass parent_id OR parent_path, not both")
    if parent_path:
        ds.parentId = get_or_create_folder_by_path(
            client=client, path=parent_path,
        ).resourceId
    elif parent_id:
        ds.parentId = parent_id

    if test:
        test_fn = _resolve_test_method(client, test_candidates)
        if test_fn is None:
            if log:
                logger.warning(
                    "test=True ignored for %s - no test endpoint",
                    type(ds).__name__,
                )
        else:
            # Squash 403 DataSourceConnectionFailed into a single
            # RuntimeError carrying ProviderCode + ExceptionMessage.
            # The generated client's logger would otherwise dump the
            # same payload, and a bare traceback through autogen is
            # noisier than the message itself.
            try:
                with silence_status_codes(403):
                    ok = test_fn(body=ds)
            except ApiClientError as exc:
                if exc.status_code == 403:
                    resp = exc.response_json or {}
                    raise RuntimeError(
                        f"test_connection failed for {ds.name!r} "
                        f"({type(ds).__name__}): "
                        f"{resp.get('ProviderCode', '?')} - "
                        f"{resp.get('ExceptionMessage', '?')}"
                    ) from None
                raise
            if not ok:
                raise RuntimeError(
                    f"test_connection failed for {ds.name!r} "
                    f"({type(ds).__name__})"
                )
            if log:
                logger.info("test_connection OK for %s", ds.name)

    if log:
        logger.info("Creating DataSource %r (%s)", ds.name, type(ds).__name__)
    try:
        return getattr(client.datasource, create_name)(body=ds)
    except Exception as e:
        raise_conflict_as_exists(e, resource=f"data source {ds.name!r}", alias=ds.alias)
        raise


def update_data_source(
    client: Client,
    ds: DataSourceDc,
    *,
    log: bool = True,
) -> bool:
    """Update an existing DataSource.

    The DTO's ``name`` selects the existing record on the server;
    other fields replace their counterparts.
    """
    _, update_name, _ = _resolve_dispatch(ds)
    if log:
        logger.info("Updating DataSource %r (%s)", ds.name, type(ds).__name__)
    return getattr(client.datasource, update_name)(body=ds)


def test_data_source(
    client: Client,
    ds: DataSourceDc,
) -> bool:
    """Probe the connection for ``ds`` without creating / updating.

    Returns ``True`` when the server confirms the connection works,
    ``False`` when it answers with ``DataSourceConnectionFailed``
    (wrong credentials, host unreachable, etc.) - the function's
    whole job is to surface that as a boolean, not as an exception.
    Other errors (auth, 5xx, missing endpoint) propagate as-is.

    Raises ``TypeError`` for Spark / WMS which have no test endpoint.
    """
    _, _, test_candidates = _resolve_dispatch(ds)
    test_fn = _resolve_test_method(client, test_candidates)
    if test_fn is None:
        raise TypeError(
            f"{type(ds).__name__} has no test_connection endpoint"
        )
    try:
        return test_fn(body=ds)
    except ApiClientError as exc:
        if exc.status_code == 403:
            # DataSourceConnectionFailed - surface as False. The
            # underlying logger.error in the generated client
            # already printed ProviderType / ProviderCode /
            # ExceptionMessage, so callers see the diagnosis even
            # though we return a plain bool here.
            return False
        raise


# ---------------------------------------------------------------------------
# Read / Delete / Iterate
# ---------------------------------------------------------------------------

def get_data_source(
    client: Client,
    name: str,
):
    """Read a DataSource by name (returns a union of ``*DataSourceInfoDc``)."""
    return client.datasource.get_data_source(name)


def delete_data_source(
    client: Client,
    name: str,
    *,
    missing_ok: bool = False,
    log: bool = True,
) -> bool:
    """Remove a DataSource by name.

    Args:
        client: EverGIS API client.
        name: Full DataSource system name (``"<user>.<short>"``).
        missing_ok: When True, a 404 from the server (DataSource
            doesn't exist) is swallowed and the function returns
            ``False`` instead of raising. Use for idempotent cleanup.
        log: Enable logging.

    Returns:
        ``True`` if the resource was present and removed,
        ``False`` if it didn't exist (only with ``missing_ok=True``).
        The raw ``DELETE /ds/<name>`` response is unreliable -
        the server returns ``False`` even on success - so we infer
        from the HTTP status instead.
    """
    if log:
        logger.info("Removing DataSource %r", name)
    try:
        with silence_status_codes(404):
            client.datasource.remove_data_source(name)
        return True
    except ApiClientError as exc:
        if missing_ok and is_not_found(exc):
            return False
        raise


# ---------------------------------------------------------------------------
# Keyword-style helpers for the two most common types
# ---------------------------------------------------------------------------

def create_postgres_data_source(
    client: Client,
    *,
    name: str,
    host: str,
    database: str,
    user: str,
    password: str,
    port: int = 5432,
    schema: str = "public",
    alias: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[list[str]] = None,
    parent_id: Optional[str] = None,
    parent_path: Optional[str] = None,
    test: bool = False,
    log: bool = True,
) -> bool:
    """Convenience over :func:`create_data_source` for Postgres."""
    ds = PostgresDataSourceDc(
        name=name, alias=alias, description=description,
        tags=list(tags) if tags else None,
        host=host, port=port, database=database,
        userName=user, password=password,
        schema=schema,
        type=DataSourceType.POSTGRES,
    )
    return create_data_source(
        client, ds, parent_id=parent_id, parent_path=parent_path,
        test=test, log=log,
    )


def create_s3_data_source(
    client: Client,
    *,
    name: str,
    endpoint: str,
    access_key: str,
    secret_key: str,
    region: Optional[str] = None,
    port: Optional[int] = None,
    alias: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[list[str]] = None,
    parent_id: Optional[str] = None,
    parent_path: Optional[str] = None,
    test: bool = False,
    log: bool = True,
) -> bool:
    """Convenience over :func:`create_data_source` for S3."""
    ds = S3DataSourceDc(
        name=name, alias=alias, description=description,
        tags=list(tags) if tags else None,
        endpoint=endpoint, port=port, region=region,
        accessKey=access_key, secretKey=secret_key,
        type=DataSourceType.S3,
    )
    return create_data_source(
        client, ds, parent_id=parent_id, parent_path=parent_path,
        test=test, log=log,
    )


__all__ = [
    "create_data_source",
    "update_data_source",
    "test_data_source",
    "get_data_source",
    "delete_data_source",
    "create_postgres_data_source",
    "create_s3_data_source",
]
