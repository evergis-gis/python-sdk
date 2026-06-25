# -*- coding: utf-8 -*-
"""GeoDataFrame conversion utilities for EverGIS API."""

from typing import List, Optional, Any, Dict, Union
import logging

import pandas as pd
import geopandas as gpd

from evergis_api.schemas import FeatureDc
from .logging import get_logger, temporary_level
from .attributes import clean_attributes_for_evergis

# Shapely geometry type
GeometryType = Any

_LOG = get_logger(__name__)


def _ensure_logger(logger: Optional[logging.Logger]) -> logging.Logger:
    """Return provided logger or module-scoped default."""
    return logger if logger is not None else _LOG


def create_geometry_dc(geom: GeometryType, target_sr: int) -> Optional[Any]:
    """Create GeometryDc from Shapely geometry.

    Args:
        geom: Shapely geometry
        target_sr: Target spatial reference ID

    Returns:
        GeometryDc object, or None for a missing/empty geometry (a row that
        legitimately has no geometry).

    Raises:
        ValueError: If a real (non-empty) geometry cannot be converted - an
            unsupported or malformed geometry is a hard error, not a silently
            dropped row.
    """
    if geom is None or getattr(geom, "is_empty", False):
        return None
    from .geometry.shapely import shapely_to_evergis_geometry
    return shapely_to_evergis_geometry(geom, target_sr)


# Geometry type aliases for filtering
# Maps EverGIS/API type names → list of valid shapely geom_types
_GEOMETRY_TYPE_ALIASES: Dict[str, List[str]] = {
    "multilinestring": ["LineString", "MultiLineString"],
    "multipolygon": ["Polygon", "MultiPolygon"],
    "polyline": ["LineString", "MultiLineString"],
}


def filter_gdf_by_geometry_type(
    gdf: "gpd.GeoDataFrame",
    geometry_type: str,
    *,
    logger: Optional[logging.Logger] = None,
    log_level: Optional[Union[str, int]] = None,
) -> "gpd.GeoDataFrame":
    """Filter GeoDataFrame by geometry type.

    Args:
        gdf: GeoDataFrame
        geometry_type: Geometry type ('Point', 'LineString', 'Polygon', 'MultiLineString', etc.)
            Supports aliases: 'polyline' -> LineString/MultiLineString
        logger: Custom logger
        log_level: Temporary log level

    Returns:
        Filtered GeoDataFrame
    """
    log = _ensure_logger(logger)
    with temporary_level(log, log_level):
        if gdf.empty:
            return gdf

        valid_mask = gdf.geometry.notna() & ~gdf.geometry.is_empty
        gdf_valid = gdf[valid_mask].copy()

        if gdf_valid.empty:
            return gdf_valid

        # Resolve aliases with case-insensitive lookup
        allowed_types = _GEOMETRY_TYPE_ALIASES.get(geometry_type.lower(), [geometry_type])

        geom_type_mask = gdf_valid.geometry.geom_type.isin(allowed_types)
        result = gdf_valid[geom_type_mask].copy()

        if log.isEnabledFor(logging.DEBUG):
            log.debug(
                "Filtered %s features of type %s from %s", len(result), geometry_type, len(gdf)
            )
        return result


def gdf_to_features(
    gdf: "gpd.GeoDataFrame",
    target_sr: int = 4326,
    geometry_type: Optional[str] = None,
    *,
    logger: Optional[logging.Logger] = None,
    log_level: Optional[Union[str, int]] = None,
) -> List[FeatureDc]:
    """Convert GeoDataFrame to list of FeatureDc objects for EverGIS API.

    Args:
        gdf: GeoDataFrame with geometries and attributes
        target_sr: Target spatial reference (default 4326 - WGS84)
        geometry_type: Filter by geometry type ('Point', 'LineString', 'Polygon', etc.)
        logger: Custom logger
        log_level: Temporary log level

    Returns:
        List of FeatureDc objects
    """
    log = _ensure_logger(logger)
    with temporary_level(log, log_level):
        if gdf.empty:
            if log.isEnabledFor(logging.DEBUG):
                log.debug("GeoDataFrame is empty")
            return []

        if log.isEnabledFor(logging.DEBUG):
            log.debug("Converting %s GeoDataFrame rows to FeatureDc", len(gdf))

        working_gdf = gdf

        geometry_column = getattr(working_gdf, "_geometry_column_name", None)
        if geometry_column is None and "geometry" in working_gdf.columns:
            geometry_column = "geometry"

        geometry_series: Optional[pd.Series] = None
        has_geometry_data = False

        if geometry_column and geometry_column in working_gdf.columns:
            try:
                geometry_series = working_gdf[geometry_column]
            except Exception as exc:
                if log.isEnabledFor(logging.DEBUG):
                    log.debug("Failed to get geometry column %s: %s", geometry_column, exc)
            else:
                non_null_mask = geometry_series.notna()
                if non_null_mask.any():
                    has_geometry_data = True
                    try:
                        non_null_mask &= ~geometry_series.is_empty
                    except Exception:
                        pass
                    has_geometry_data = bool(non_null_mask.any())

        if has_geometry_data and working_gdf.crs:
            try:
                current_epsg = working_gdf.crs.to_epsg()
            except Exception as exc:
                current_epsg = None
                if log.isEnabledFor(logging.DEBUG):
                    log.debug("Failed to get EPSG for CRS %s: %s", working_gdf.crs, exc)
            if current_epsg != target_sr:
                if log.isEnabledFor(logging.DEBUG):
                    log.debug("Reprojecting from %s to EPSG:%s", working_gdf.crs, target_sr)
                working_gdf = working_gdf.to_crs(target_sr)
                if geometry_column and geometry_column in working_gdf.columns:
                    geometry_series = working_gdf[geometry_column]
        elif log.isEnabledFor(logging.DEBUG) and not has_geometry_data:
            log.debug("No valid geometry, skipping CRS reprojection")

        if geometry_type:
            if has_geometry_data:
                working_gdf = filter_gdf_by_geometry_type(working_gdf, geometry_type, logger=log)

                if working_gdf.empty:
                    if log.isEnabledFor(logging.WARNING):
                        log.warning("No features of type %s found", geometry_type)
                    return []

                if geometry_column and geometry_column in working_gdf.columns:
                    geometry_series = working_gdf[geometry_column]
            elif log.isEnabledFor(logging.DEBUG):
                log.debug("Skipping type filter %s: no geometry data", geometry_type)

        attr_columns = list(working_gdf.columns)
        if geometry_column and geometry_column in attr_columns:
            attr_columns.remove(geometry_column)
        elif "geometry" in attr_columns and geometry_column != "geometry":
            attr_columns.remove("geometry")

        if attr_columns:
            attributes_df = working_gdf[attr_columns].copy()
            attributes_df = attributes_df.replace([pd.NA, pd.NaT, float("nan")], None)
            attributes_df = attributes_df.where(pd.notna(attributes_df), None)
            raw_attributes = attributes_df.to_dict("records")
        else:
            raw_attributes = [{} for _ in range(len(working_gdf))]

        processed_attributes: List[Dict[str, Any]] = [
            clean_attributes_for_evergis(attrs) for attrs in raw_attributes
        ]

        if geometry_series is not None:
            geometry_values = list(geometry_series)
        else:
            geometry_values = [None] * len(working_gdf)

        features: List[FeatureDc] = []
        for attrs, geom in zip(processed_attributes, geometry_values):
            geom_dc = None
            if geom is not None and not getattr(geom, "is_empty", False):
                geom_dc = create_geometry_dc(geom, target_sr)

            feature_kwargs: Dict[str, Any] = {"properties": attrs}
            if geom_dc is not None:
                feature_kwargs["geometry"] = geom_dc

            features.append(FeatureDc(**feature_kwargs))

        if log.isEnabledFor(logging.DEBUG):
            log.debug("Created %s FeatureDc objects", len(features))
        return features


def _features_to_feature_collection(features: List[FeatureDc]) -> Dict[str, Any]:
    """Convert list of FeatureDc to GeoJSON FeatureCollection dict."""
    feature_dicts = []
    for i, f in enumerate(features):
        fd = f.model_dump(exclude_none=True)
        fd.setdefault("type", "Feature")
        fd.setdefault("id", str(i + 1))
        feature_dicts.append(fd)

    return {
        "type": "FeatureCollection",
        "features": feature_dicts,
        "totalCount": len(feature_dicts),
        "offset": 0,
        "limit": 0,
    }


def gdf_to_feature_collection(
    gdf: "gpd.GeoDataFrame",
    target_sr: int = 4326,
    geometry_type: Optional[str] = None,
    *,
    logger: Optional[logging.Logger] = None,
    log_level: Optional[Union[str, int]] = None,
) -> Dict[str, Any]:
    """Convert GeoDataFrame to GeoJSON FeatureCollection dict.

    Args:
        gdf: GeoDataFrame with geometries and attributes
        target_sr: Target spatial reference (default 4326)
        geometry_type: Filter by geometry type ('Point', 'Polygon', etc.)
        logger: Custom logger
        log_level: Temporary log level

    Returns:
        FeatureCollection dict:
        {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "geometry": {...}, "properties": {...}, "id": "1"}, ...],
            "totalCount": N,
            "offset": 0,
            "limit": 0,
        }
    """
    features = gdf_to_features(
        gdf, target_sr=target_sr, geometry_type=geometry_type,
        logger=logger, log_level=log_level,
    )
    return _features_to_feature_collection(features)


def df_to_feature_collection(
    df: "pd.DataFrame",
    *,
    logger: Optional[logging.Logger] = None,
    log_level: Optional[Union[str, int]] = None,
) -> Dict[str, Any]:
    """Convert pandas DataFrame (no geometry) to FeatureCollection dict.

    Args:
        df: pandas DataFrame with tabular data
        logger: Custom logger
        log_level: Temporary log level

    Returns:
        FeatureCollection dict with geometry=None for each feature
    """
    log = _ensure_logger(logger)
    with temporary_level(log, log_level):
        if df.empty:
            return _features_to_feature_collection([])

        raw_attrs = df.replace([pd.NA, pd.NaT, float("nan")], None)
        raw_attrs = raw_attrs.where(pd.notna(raw_attrs), None)
        records = raw_attrs.to_dict("records")

        features = [
            FeatureDc(properties=clean_attributes_for_evergis(attrs))
            for attrs in records
        ]
        return _features_to_feature_collection(features)


def paged_features_to_geodataframe(
    paged_features_list: Union[List, Any],
    target_crs: Optional[str] = None,
    geometry_column: str = "geometry",
    *,
    logger: Optional[logging.Logger] = None,
    log_level: Optional[Union[str, int]] = None,
) -> "gpd.GeoDataFrame":
    """Convert PagedFeaturesListDc to GeoDataFrame.

    Uses GeoJSON-native conversion via gpd.GeoDataFrame.from_features().

    Args:
        paged_features_list: PagedFeaturesListDc object(s)
        target_crs: Target CRS (e.g. 'EPSG:4326', 'EPSG:3857')
        geometry_column: Geometry column name
        logger: Custom logger
        log_level: Temporary log level

    Returns:
        GeoDataFrame with geometries and attributes
    """
    log = _ensure_logger(logger)
    with temporary_level(log, log_level):
        # Normalize input to list
        if not isinstance(paged_features_list, list):
            paged_features_list = [paged_features_list]

        # Collect all features from all pages
        all_features = []
        for page in paged_features_list:
            if page is None:
                continue
            if hasattr(page, "features") and page.features is not None:
                all_features.extend(page.features)
            elif isinstance(page, list):
                all_features.extend(page)
            else:
                if log.isEnabledFor(logging.WARNING):
                    log.warning("Unknown page format: %s", type(page))

        if not all_features:
            if log.isEnabledFor(logging.DEBUG):
                log.debug("No features, creating empty GeoDataFrame")
            return gpd.GeoDataFrame(columns=[geometry_column], crs=target_crs)

        if log.isEnabledFor(logging.DEBUG):
            log.debug("Converting %s features to GeoDataFrame", len(all_features))

        # Auto-detect CRS from first feature's geometry srId
        source_crs = target_crs
        if not source_crs:
            for f in all_features:
                if f.geometry is not None and hasattr(f.geometry, 'srId') and f.geometry.srId:
                    source_crs = f"EPSG:{f.geometry.srId}"
                    if log.isEnabledFor(logging.DEBUG):
                        log.debug("Detected CRS from data: %s", source_crs)
                    break

        # Convert FeatureDc → GeoJSON-compatible dicts for from_features().
        # ``exclude_none=True`` drops keys whose value is ``None``, but
        # ``gpd.GeoDataFrame.from_features`` requires the ``geometry`` key
        # to be present (it does bracket access, not ``.get``). Restore
        # it explicitly so rows with no geometry land as ``geometry=None``
        # in the resulting GeoDataFrame instead of crashing with KeyError.
        feature_dicts = []
        for f in all_features:
            fd = f.model_dump(exclude_none=True)
            fd.setdefault('geometry', None)
            if fd.get('geometry'):
                fd['geometry'].pop('srId', None)
            feature_dicts.append(fd)

        # GeoJSON → GeoDataFrame in one call
        gdf = gpd.GeoDataFrame.from_features(feature_dicts, crs=source_crs)

        # Reproject if needed. A failure here propagates: silently returning
        # un-reprojected data while claiming target_crs would hand the caller
        # wrong coordinates for any downstream spatial operation.
        if target_crs and gdf.crs and str(gdf.crs) != target_crs:
            if log.isEnabledFor(logging.DEBUG):
                log.debug("Reprojecting from %s to %s", gdf.crs, target_crs)
            gdf = gdf.to_crs(target_crs)

        if log.isEnabledFor(logging.DEBUG):
            log.debug("Created GeoDataFrame with %s rows, CRS: %s", len(gdf), gdf.crs)
        return gdf


__all__ = ["filter_gdf_by_geometry_type", "gdf_to_features", "paged_features_to_geodataframe"]
