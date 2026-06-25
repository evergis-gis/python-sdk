# -*- coding: utf-8 -*-
"""Functions for building isochrones, routes, and OD matrices via the EverGIS Worker API."""

from typing import List, Optional, Union, TYPE_CHECKING
from evergis_api import Client
from evergis_api.schemas import WorkerStartMethodDto
from shapely.geometry import Point, LineString, MultiLineString, MultiPolygon, Polygon
from evergis_tools.geometry import evergis_dict_to_shapely
from evergis_tools.tasks.worker_models import (
    NetengineOdmatrixrestStartParameters as _ODMatrixRestData,
)
import logging

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def build_isochrone(
    client: Client,
    point: Point,
    duration: int,
    provider_name: str = "sproute_isochrone_pedestrian",
    sr_in: int = 3857,
    sr_out: int = 4326,
    log: bool = False,
    **kwargs
) -> Optional[Union[Polygon, MultiPolygon]]:
    """
    Build an isochrone via the EverGIS Worker API and return a shapely MultiPolygon.

    Args:
        client: EverGIS API client
        point: Shapely Point object (in the sr_in coordinate system)
        duration: Time in minutes for building the isochrone
        provider_name: Provider name (default: "sproute_isochrone_pedestrian")
        sr_in: Input coordinate system (default: 3857 - Web Mercator)
        sr_out: Output coordinate system (default: 4326 - WGS84)
        log: Enable logging (default: True)
        **kwargs: Additional parameters to pass into data

    Returns:
        Optional[Union[Polygon, MultiPolygon]]: Isochrone geometry, or None when the worker returns no usable geometry. Request/parsing errors are raised.
    """

    # Build the payload for the worker API
    payload = {
        "workerType": "netEngine",
        "methodType": "availabilityAreaRest",
        "data": {
            "providerName": provider_name,
            "x": point.x,
            "y": point.y,
            "duration": duration,
            "srIn": sr_in,
            "srOut": sr_out,
            **kwargs  # Add extra parameters
        }
    }

    # Build the WorkerStartMethodDto object
    worker_request = WorkerStartMethodDto(
        workerType=payload["workerType"],
        methodType=payload["methodType"],
        data=payload["data"]
    )

    try:
        # Send the request via the worker API
        response_data = client.remotetaskmanager.post(body=worker_request)

        if not response_data:
            if log:
                logger.error("Worker method returned an empty response")
            return None

        if log:
            logger.info("Worker method completed successfully, extracting geometry...")

        # The response is a GeoJSON FeatureCollection dict.
        # Extract geometry from the first feature.
        if isinstance(response_data, dict) and "features" in response_data:
            features = response_data["features"]
            if not features:
                if log:
                    logger.error("FeatureCollection contains no features")
                return None
            geom_data = features[0].get("geometry")
        elif isinstance(response_data, list):
            # Fallback: the API returned a list of geometries directly
            geom_data = response_data[0]
        else:
            geom_data = response_data

        if not geom_data:
            if log:
                logger.error("Could not extract geometry from the response")
            return None

        geometry = evergis_dict_to_shapely(geom_data)

        if geometry.geom_type not in ('Polygon', 'MultiPolygon'):
            if log:
                logger.warning(f"Unexpected geometry type: {geometry.geom_type}")
            return None

        if log:
            logger.info(f"Isochrone created successfully ({geometry.geom_type})")
        return geometry

    except Exception as e:
        # None is reserved for "worker returned no usable geometry";
        # request/parsing failures must surface to the caller
        if log:
            logger.error(f"Worker request failed: {e}")
        raise


def build_route(
    client: Client,
    start_point: Point,
    end_point: Point,
    provider_name: str = "sproute_route_pedestrian",
    sr_in: int = 3857,
    sr_out: int = 4326,
    **kwargs
) -> Optional[Union[LineString, MultiLineString]]:
    """
    Build a route via the EverGIS Worker API and return a Shapely geometry.

    Args:
        client: EverGIS API client
        start_point: Shapely Point object for the start point (in the sr_in coordinate system)
        end_point: Shapely Point object for the end point (in the sr_in coordinate system)
        provider_name: Provider name (default: "sproute_route_pedestrian")
        sr_in: Input coordinate system (default: 3857 - Web Mercator)
        sr_out: Output coordinate system (default: 4326 - WGS84)
        **kwargs: Additional parameters to pass into data

    Returns:
        Optional[Union[LineString, MultiLineString]]: Route geometry, or None when the response contains no route segments. Request/parsing errors are raised.
    """

    # Build the payload for the worker API
    payload = {
        "workerType": "netEngine",
        "methodType": "route",
        "data": {
            "providerName": provider_name,
            "x1": start_point.x,
            "y1": start_point.y,
            "x2": end_point.x,
            "y2": end_point.y,
            "srIn": sr_in,
            "srOut": sr_out,
            **kwargs  # Add extra parameters
        }
    }

    # Build the WorkerStartMethodDto object
    worker_request = WorkerStartMethodDto(
        workerType=payload["workerType"],
        methodType=payload["methodType"],
        data=payload["data"]
    )

    try:
        # Send the request via the worker API
        response_data = client.remotetaskmanager.post(body=worker_request)

        if not response_data:
            logger.error("Worker method returned an empty response")
            return None

        logger.info("Worker method completed successfully, extracting route...")

        # Extract features from the FeatureCollection or handle as a list
        if isinstance(response_data, dict) and "features" in response_data:
            items_to_process = [
                f["geometry"] for f in response_data["features"]
                if isinstance(f, dict) and "geometry" in f
            ]
        elif isinstance(response_data, list):
            items_to_process = response_data
        else:
            items_to_process = [response_data]

        # Collect all geometries. A segment parsing error is propagated
        # (via the outer except), as the docstring promises - route segments
        # must not be dropped silently.
        geometries = []
        for item in items_to_process:
            if isinstance(item, dict):
                geometries.append(evergis_dict_to_shapely(item))

        if geometries:
            if len(geometries) == 1:
                logger.info("Route created successfully")
                return geometries[0]
            else:
                logger.info(f"Route created successfully from {len(geometries)} segments")
                return MultiLineString(geometries)
        else:
            logger.error("Could not process any route element")
            return None

    except Exception as e:
        # None is reserved for "no route segments in the response";
        # request/parsing failures must surface to the caller
        logger.error(f"Worker request failed: {e}")
        raise


def _to_points(points) -> List[Point]:
    """Coerce a heterogenous ``points`` argument into ``list[shapely.Point]``.

    Accepts a ``geopandas.GeoDataFrame`` (geometry column), a sequence of
    shapely ``Point``, or a sequence of ``(x, y)`` tuples.
    """
    # geopandas.GeoDataFrame - imported lazily to keep the module light.
    try:
        import geopandas as gpd
        if isinstance(points, gpd.GeoDataFrame):
            return list(points.geometry)
    except ImportError:
        pass
    out: List[Point] = []
    for p in points:
        if isinstance(p, Point):
            out.append(p)
        elif isinstance(p, (tuple, list)) and len(p) == 2:
            out.append(Point(float(p[0]), float(p[1])))
        else:
            raise TypeError(
                f"Unsupported point type {type(p).__name__}; "
                "expected shapely.Point, (x, y) tuple, or GeoDataFrame."
            )
    return out


def _as_feature(point: Point, gid: int) -> dict:
    """Wrap a shapely Point as a minimal GeoJSON Feature."""
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [point.x, point.y]},
        "properties": {"gid": gid},
    }


def build_od_matrix_rest(
    client: Client,
    points_from,
    points_to,
    *,
    transport_type: str = "car",
    epsg_code: int = 4326,
    seconds: bool = True,
    log: bool = False,
):
    """Synchronously compute an origin-destination matrix via the worker REST API.

    Calls ``POST /scheduler/worker`` with ``workerType=netEngine``,
    ``methodType=ODMatrix-rest`` and returns a flat table with one row per
    (from, to) pair.

    Use this for interactive N×M cases (no result layer published) - for the
    layer-producing variant see ``evergis_tools.tasks.network.build_od_matrix``.

    Args:
        client: EverGIS API client.
        points_from: Origin points - ``GeoDataFrame``, list of shapely ``Point``,
            or list of ``(x, y)`` tuples. Coordinates must be in ``epsg_code``.
        points_to: Destination points - same accepted types as ``points_from``.
        transport_type: Transport mode (``"car"``, ``"pedestrian"``, …). Server
            decides what it supports.
        epsg_code: SRID of the input coordinates (default 4326; 3857 also works).
        seconds: ``True`` returns travel time in seconds, ``False`` returns
            distance in metres. Surfaced in the ``weightparameter`` column.
        log: If ``True``, log info messages.

    Returns:
        ``pandas.DataFrame`` with columns
        ``from, to, distance, transporttype, weightparameter`` - one row per
        ordered pair (len(points_from) × len(points_to)).
    """
    import pandas as pd

    pts_from = _to_points(points_from)
    pts_to = _to_points(points_to)
    if not pts_from or not pts_to:
        raise ValueError(
            "Both 'points_from' and 'points_to' must contain at least one point."
        )

    params = _ODMatrixRestData(
        arrayFrom=[_as_feature(p, i) for i, p in enumerate(pts_from)],
        arrayTo=[_as_feature(p, i) for i, p in enumerate(pts_to)],
        transportType=transport_type,
        epsgCode=epsg_code,
        seconds=seconds,
    )

    body = WorkerStartMethodDto(
        workerType="netEngine",
        methodType="ODMatrix-rest",
        data=params.model_dump(by_alias=True, exclude_none=True),
    )

    if log:
        logger.info(
            "OD-matrix-rest: %d FROM × %d TO, transport=%s, epsg=%d, seconds=%s",
            len(pts_from), len(pts_to), transport_type, epsg_code, seconds,
        )

    response = client.remotetaskmanager.post(body=body)
    if not isinstance(response, dict) or "features" not in response:
        raise RuntimeError(f"Unexpected OD-matrix response shape: {response!r}")

    rows = [f.get("properties") or {} for f in response["features"]]
    return pd.DataFrame(rows)