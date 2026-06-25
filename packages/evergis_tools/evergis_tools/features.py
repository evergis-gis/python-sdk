# -*- coding: utf-8 -*-
"""Utilities for working with features in the EverGIS API."""

from typing import Optional, List, Any, TYPE_CHECKING
import logging
import json

from evergis_api import Client, ApiClientError
from evergis_api.schemas import UpdateFeatureDc, PagedFeaturesListDc, FeatureDc
from .logging import get_logger

if TYPE_CHECKING:
    import geopandas as gpd
from .geodataframes import gdf_to_features

_LOG = get_logger(__name__)


def chunk_features_by_size(
    features: List[Any],
    max_chunk_size_bytes: int = 5_000_000,
    log: bool = False,
) -> List[List[Any]]:
    """Split features into chunks by JSON payload size in bytes.

    Groups features into chunks where each chunk's serialized JSON size
    does not exceed max_chunk_size_bytes. This ensures predictable API
    payload sizes regardless of feature complexity.

    Args:
        features: List of feature objects (FeatureDc or UpdateFeatureDc)
        max_chunk_size_bytes: Maximum size per chunk in bytes (default: 5MB)
        log: Enable logging (default: False)

    Returns:
        List of feature chunks, where each chunk is a list of features

    Example:
        >>> chunks = chunk_features_by_size(features, max_chunk_size_bytes=5_000_000)
        >>> for i, chunk in enumerate(chunks):
        ...     print(f"Chunk {i+1}: {len(chunk)} features")
    """
    if not features:
        return []

    chunks = []
    current_chunk = []
    current_size = 0

    for feature in features:
        # Calculate JSON size of the feature
        try:
            feature_json = json.dumps(feature.model_dump())
            feature_size = len(feature_json.encode("utf-8"))
        except Exception as e:
            if log:
                _LOG.warning(f"Failed to calculate size for feature, using estimate: {e}")
            feature_size = 1000  # Fallback estimate

        # Check if adding this feature would exceed the limit
        if current_chunk and current_size + feature_size > max_chunk_size_bytes:
            # Current chunk is full, save it and start a new one
            chunks.append(current_chunk)
            if log:
                _LOG.debug(
                    f"Chunk {len(chunks)}: {len(current_chunk)} features, ~{current_size / 1_000_000:.2f} MB"
                )
            current_chunk = [feature]
            current_size = feature_size
        else:
            # Add to current chunk
            current_chunk.append(feature)
            current_size += feature_size

        # Edge case: single feature larger than max size
        if len(current_chunk) == 1 and feature_size > max_chunk_size_bytes:
            if log:
                _LOG.warning(
                    f"Single feature exceeds max chunk size: {feature_size / 1_000_000:.2f} MB > "
                    f"{max_chunk_size_bytes / 1_000_000:.2f} MB. Creating single-item chunk."
                )
            chunks.append(current_chunk)
            current_chunk = []
            current_size = 0

    # Add the last chunk if not empty
    if current_chunk:
        chunks.append(current_chunk)
        if log:
            _LOG.debug(
                f"Chunk {len(chunks)}: {len(current_chunk)} features, ~{current_size / 1_000_000:.2f} MB"
            )

    return chunks


def add_gdf_features_to_layer(
    client: Client,
    gdf: "gpd.GeoDataFrame",
    layer_name: Optional[str] = None,
    layer_path: Optional[str] = None,
    target_sr: int = 3857,
    geometry_type: Optional[str] = None,
    chunk_size_bytes: int = 1_200_000,
    allow_additional_attributes: bool = True,
    log: bool = False,
) -> List[Any]:
    """Add features from GeoDataFrame to EverGIS layer.

    Features are split into chunks by JSON payload size to ensure predictable
    API request sizes regardless of feature complexity.

    Args:
        client: EverGIS API client
        gdf: GeoDataFrame with geodata
        layer_name: Layer name (system name) for adding objects. Either layer_name or layer_path must be provided.
        layer_path: Resource identifier (catalog path, resource ID, or system name) to resolve the layer.
                   Either layer_name or layer_path must be provided.
        target_sr: Target coordinate system (default 3857 - Web Mercator)
        geometry_type: Filter by geometry type ('Point', 'LineString', 'Polygon', etc.)
        chunk_size_bytes: Maximum chunk size in bytes (default 5MB). Features are grouped into chunks
                         where each chunk's JSON payload does not exceed this size.
        allow_additional_attributes: If True, server accepts attributes not defined in layer schema.
                                   If False, server returns error for undefined attributes (default: True).
        log: Enable logging (default: False)

    Returns:
        List of object creation results

    Raises:
        ValueError: If neither layer_name nor layer_path is provided, or if both are provided,
                   or if layer_path doesn't resolve to a Layer resource
        ApiClientError: If allow_additional_attributes=False and GeoDataFrame contains fields
                       not in layer schema

    Example:
        >>> import geopandas as gpd
        >>> from evergis_api import Client
        >>> from evergis_tools.features import add_gdf_features_to_layer
        >>>
        >>> client = Client(base_url="...", sb_token="...")
        >>> gdf = gpd.read_file("data.geojson")
        >>>
        >>> # Add using layer name (allows extra fields by default)
        >>> results = add_gdf_features_to_layer(client, gdf, layer_name="my_layer")
        >>>
        >>> # Add using layer path with strict field checking
        >>> results = add_gdf_features_to_layer(
        ...     client, gdf,
        ...     layer_path="john_doe:Projects/Data/my_layer",
        ...     allow_additional_attributes=False
        ... )
        >>>
        >>> # Add with custom chunk size (10MB)
        >>> results = add_gdf_features_to_layer(
        ...     client, gdf,
        ...     layer_name="points_layer",
        ...     geometry_type="Point",
        ...     chunk_size_bytes=10_000_000
        ... )
    """
    from .catalog.resources import resolve_resource

    # Validate that exactly one of layer_name or layer_path is provided
    if layer_name is None and layer_path is None:
        raise ValueError("Either 'layer_name' or 'layer_path' must be provided")

    if layer_name is not None and layer_path is not None:
        raise ValueError("Only one of 'layer_name' or 'layer_path' should be provided, not both")

    # If layer_path is provided, resolve it to get layer_name
    if layer_path is not None:
        if log:
            _LOG.info(f"Resolving resource from identifier '{layer_path}'")

        try:
            resource = resolve_resource(client=client, identifier=layer_path)

            if resource.type != "Layer":
                raise ValueError(
                    f"Resource '{layer_path}' is not a Layer (type: {resource.type}). "
                    f"Only Layer resources are supported."
                )

            if not resource.systemName:
                raise ValueError(
                    f"Resource '{layer_path}' does not have a system name. "
                    f"Cannot add features to layer without system name."
                )

            layer_name = resource.systemName

            if log:
                _LOG.info(f"Resolved to layer with system name: '{layer_name}'")

        except (ValueError, ApiClientError):
            # Validation ValueErrors above and resolve errors (incl.
            # ResourceNotFound, which is an ApiClientError) propagate with
            # their type intact - not flattened into a generic ValueError.
            raise
        except Exception as e:
            raise ValueError(f"Failed to resolve resource '{layer_path}': {e}") from e

    # Convert GeoDataFrame to features
    log_level = logging.INFO if log else logging.ERROR

    features = gdf_to_features(
        gdf=gdf,
        target_sr=target_sr,
        geometry_type=geometry_type,
        logger=_LOG,
        log_level=log_level,
    )
    if not features:
        if log:
            _LOG.warning(f"No objects to add to layer {layer_name}")
        return []

    if log:
        _LOG.info(f"Starting addition of {len(features)} objects to layer '{layer_name}'")
        _LOG.info(f"First object: {features[0]}")

    # Split features into chunks by size
    chunks = chunk_features_by_size(features, chunk_size_bytes, log=log)

    if log:
        _LOG.info(
            f"Split into {len(chunks)} chunks (max {chunk_size_bytes / 1_000_000:.1f} MB each)"
        )

    results = []
    total_created = 0
    total_count = len(features)

    # Send objects in chunks
    for chunk_num, chunk in enumerate(chunks, 1):
        if log:
            # Calculate actual chunk size for logging
            chunk_json = json.dumps([f.model_dump(exclude_unset=True, exclude_none=True) for f in chunk])
            chunk_size_mb = len(chunk_json.encode("utf-8")) / 1_000_000
            _LOG.info(
                f"Chunk {chunk_num}/{len(chunks)}: {len(chunk)} features, ~{chunk_size_mb:.2f} MB"
            )
        # Serialize with exclude_none to avoid sending id=null etc.
        serialized_chunk = [
            f.model_dump(exclude_unset=True, exclude_none=True) for f in chunk
        ]
        try:
            result = client.layers.create_features(
                name=layer_name,
                body=serialized_chunk,
                allowAdditionalAttributes=allow_additional_attributes
            )
            created_count = len(result.createdIds or [])
            total_created += created_count
            results.append(result)

            total_count_left = total_count - total_created

            if log:
                _LOG.info(f" - Added: {created_count} objects, remaining: {total_count_left}")

        except ApiClientError as e:
            if log:
                _LOG.error(f"API Error {e.status_code} in chunk {chunk_num}: {e.response_text}")
            raise
        except Exception as e:
            if log:
                _LOG.error(f" - Unexpected error in chunk {chunk_num}: {e}")
            raise

    if log:
        _LOG.info(f"✅ Completed! Total {total_created} objects added to layer '{layer_name}'")
    return results


def add_df_features_to_layer(
    client: Client,
    df,  # pandas DataFrame
    layer_name: Optional[str] = None,
    layer_path: Optional[str] = None,
    chunk_size_bytes: int = 1_200_000,
    allow_additional_attributes: bool = True,
    log: bool = False,
) -> List[Any]:
    """Add features from pandas DataFrame to EverGIS layer (for non-spatial tables).

    This function is designed for adding features to non-spatial tables (tables without geometry).
    For spatial data, use add_gdf_features_to_layer instead.

    Features are split into chunks by JSON payload size to ensure predictable
    API request sizes regardless of feature complexity.

    Args:
        client: EverGIS API client
        df: pandas DataFrame with attributes
        layer_name: Layer name (system name) for adding objects. Either layer_name or layer_path must be provided.
        layer_path: Resource identifier (catalog path, resource ID, or system name) to resolve the layer.
                   Either layer_name or layer_path must be provided.
        chunk_size_bytes: Maximum chunk size in bytes (default 1.2MB). Features are grouped into chunks
                         where each chunk's JSON payload does not exceed this size.
        allow_additional_attributes: If True, server accepts attributes not defined in layer schema.
                                   If False, server returns error for undefined attributes (default: True).
        log: Enable logging (default: False)

    Returns:
        List of object creation results

    Raises:
        ValueError: If neither layer_name nor layer_path is provided, or if both are provided,
                   or if layer_path doesn't resolve to a Layer resource
        ApiClientError: If allow_additional_attributes=False and DataFrame contains fields
                       not in layer schema

    Example:
        >>> import pandas as pd
        >>> from evergis_api import Client
        >>> from evergis_tools.features import add_df_features_to_layer
        >>>
        >>> client = Client(base_url="...", sb_token="...")
        >>> df = pd.DataFrame({'name': ['a', 'b'], 'value': [1, 2]})
        >>>
        >>> # Add using layer name (allows extra fields by default)
        >>> results = add_df_features_to_layer(client, df, layer_name="my_table")
        >>>
        >>> # Add using layer path with strict field checking
        >>> results = add_df_features_to_layer(
        ...     client, df,
        ...     layer_path="john_doe:Projects/Data/my_table",
        ...     allow_additional_attributes=False
        ... )
        >>>
        >>> # Add with custom chunk size (10MB)
        >>> results = add_df_features_to_layer(
        ...     client, df,
        ...     layer_name="attributes_table",
        ...     chunk_size_bytes=10_000_000
        ... )
    """
    from .catalog.resources import resolve_resource

    # Validate that exactly one of layer_name or layer_path is provided
    if layer_name is None and layer_path is None:
        raise ValueError("Either 'layer_name' or 'layer_path' must be provided")

    if layer_name is not None and layer_path is not None:
        raise ValueError("Only one of 'layer_name' or 'layer_path' should be provided, not both")

    # If layer_path is provided, resolve it to get layer_name
    if layer_path is not None:
        if log:
            _LOG.info(f"Resolving resource from identifier '{layer_path}'")

        try:
            resource = resolve_resource(client=client, identifier=layer_path)

            if resource.type != "Layer":
                raise ValueError(
                    f"Resource '{layer_path}' is not a Layer (type: {resource.type}). "
                    f"Only Layer resources are supported."
                )

            if not resource.systemName:
                raise ValueError(
                    f"Resource '{layer_path}' does not have a system name. "
                    f"Cannot add features to layer without system name."
                )

            layer_name = resource.systemName

            if log:
                _LOG.info(f"Resolved to layer with system name: '{layer_name}'")

        except (ValueError, ApiClientError):
            # Validation ValueErrors above and resolve errors (incl.
            # ResourceNotFound, which is an ApiClientError) propagate with
            # their type intact - not flattened into a generic ValueError.
            raise
        except Exception as e:
            raise ValueError(f"Failed to resolve resource '{layer_path}': {e}") from e

    # Convert DataFrame to features
    features = df_to_features(df=df, log=log)

    if not features:
        if log:
            _LOG.warning(f"No objects to add to layer {layer_name}")
        return []

    if log:
        _LOG.info(f"Starting addition of {len(features)} objects to layer '{layer_name}'")
        _LOG.info(f"First object: {features[0]}")

    # Split features into chunks by size
    chunks = chunk_features_by_size(features, chunk_size_bytes, log=log)

    if log:
        _LOG.info(
            f"Split into {len(chunks)} chunks (max {chunk_size_bytes / 1_000_000:.1f} MB each)"
        )

    results = []
    total_created = 0
    total_count = len(features)

    # Send objects in chunks
    for chunk_num, chunk in enumerate(chunks, 1):
        # Serialize with exclude_none to avoid sending geometry=null, id=null etc.
        serialized_chunk = [
            f.model_dump(exclude_unset=True, exclude_none=True) for f in chunk
        ]
        if log:
            chunk_json = json.dumps(serialized_chunk)
            chunk_size_mb = len(chunk_json.encode("utf-8")) / 1_000_000
            _LOG.info(
                f"Chunk {chunk_num}/{len(chunks)}: {len(chunk)} features, ~{chunk_size_mb:.2f} MB"
            )

        try:
            result = client.layers.create_features(
                name=layer_name,
                body=serialized_chunk,
                allowAdditionalAttributes=allow_additional_attributes
            )
            created_count = len(result.createdIds or [])
            total_created += created_count
            results.append(result)

            total_count_left = total_count - total_created

            if log:
                _LOG.info(f" - Added: {created_count} objects, remaining: {total_count_left}")

        except ApiClientError as e:
            if log:
                _LOG.error(f"API Error {e.status_code} in chunk {chunk_num}: {e.response_text}")
            raise
        except Exception as e:
            if log:
                _LOG.error(f" - Unexpected error in chunk {chunk_num}: {e}")
            raise

    if log:
        _LOG.info(f"✅ Completed! Total {total_created} objects added to layer '{layer_name}'")
    return results


def gdf_to_update_features(
    gdf: "gpd.GeoDataFrame",
    target_sr: int = 3857,
    geometry_type: Optional[str] = None,
    id_column: str = "id",
    log: bool = True,
) -> List[UpdateFeatureDc]:
    """Convert GeoDataFrame to a list of UpdateFeatureDc objects for updating in the EverGIS API.

    Args:
        gdf: GeoDataFrame with geometries and attributes
        target_sr: Target coordinate system (default 3857 - Web Mercator)
        geometry_type: Filter by geometry type ('Point', 'LineString', 'Polygon', etc.)
        id_column: Name of the column with object IDs (default 'id')
        log: Enable logging (default: True)

    Returns:
        List of UpdateFeatureDc objects

    Raises:
        ValueError: If the ID column is not found or contains empty values

    Note:
        To include only specific fields, filter the GeoDataFrame before calling this function:
        `gdf = gdf[['id', 'field1', 'field2', 'geometry']]`

    Example:
        >>> gdf['id'] = ['1', '2', '3']  # ID must be a string
        >>> update_features = gdf_to_update_features(gdf, target_sr=3857)
        >>>
        >>> # Include only specific fields (filter the GeoDataFrame beforehand)
        >>> filtered_gdf = gdf[['id', 'name', 'status', 'geometry']]
        >>> update_features = gdf_to_update_features(filtered_gdf)
    """
    from .geodataframes import (
        clean_attributes_for_evergis,
        create_geometry_dc,
        filter_gdf_by_geometry_type,
    )

    log_level = logging.INFO if log else logging.ERROR

    if gdf.empty:
        if log:
            _LOG.info("GeoDataFrame is empty")
        return []

    # Check that the ID column exists
    if id_column not in gdf.columns:
        raise ValueError(
            f"Column '{id_column}' not found in GeoDataFrame. Available columns: {list(gdf.columns)}"
        )

    # Check that all IDs are filled
    if gdf[id_column].isna().any():
        raise ValueError(
            f"Column '{id_column}' contains empty values. All objects must have an ID for update."
        )

    if log:
        _LOG.info(f"Converting {len(gdf)} GeoDataFrame objects to UpdateFeatureDc")

    # Reproject to the target coordinate system if needed
    if gdf.crs and gdf.crs.to_epsg() != target_sr:
        if log:
            _LOG.info(f"Reprojecting from {gdf.crs} to EPSG:{target_sr}")
        gdf = gdf.to_crs(target_sr)

    # Filter by geometry type if specified
    if geometry_type:
        gdf = filter_gdf_by_geometry_type(gdf, geometry_type, logger=_LOG, log_level=log_level)

        if gdf.empty:
            if log:
                _LOG.warning(f"No objects of type {geometry_type} found")
            return []

    # Prepare attributes (exclude geometry and ID column)
    attr_columns = [col for col in gdf.columns if col not in ["geometry", id_column]]

    # Get attributes
    if attr_columns:
        attributes_df = gdf[attr_columns].copy()
        # Replace all kinds of NaN values with None
        import pandas as pd

        attributes_df = attributes_df.replace([pd.NA, pd.NaT, float("nan")], None)
        attributes_df = attributes_df.where(pd.notna(attributes_df), None)
        attributes_list = attributes_df.to_dict("records")
    else:
        attributes_list = [{}] * len(gdf)

    # Process attributes for EverGIS API compatibility
    processed_attributes = [clean_attributes_for_evergis(attrs) for attrs in attributes_list]

    # Process geometries
    geometry_dcs = []
    for geom in gdf.geometry:
        geom_dc = create_geometry_dc(geom, target_sr)
        geometry_dcs.append(geom_dc)

    # Get object IDs and convert to string
    ids = gdf[id_column].astype(str).tolist()

    # Create UpdateFeatureDc objects
    update_features = []
    for obj_id, attrs, geom_dc in zip(ids, processed_attributes, geometry_dcs):
        if geom_dc is not None:
            update_feature = UpdateFeatureDc(id=obj_id, attributes=attrs, geometry=geom_dc)
            update_features.append(update_feature)
        else:
            if log:
                _LOG.warning(f"Skipping object with ID '{obj_id}' - failed to create geometry")

    if log:
        _LOG.info(f"Created {len(update_features)} UpdateFeatureDc objects")
    return update_features


def df_to_update_features(
    df,  # pandas DataFrame
    id_column: str = "id",
    log: bool = True,
) -> List[UpdateFeatureDc]:
    """Convert pandas DataFrame to list of UpdateFeatureDc objects without geometry.

    This function is designed for updating non-spatial tables (tables without geometry).
    For spatial data, use gdf_to_update_features instead.

    Args:
        df: pandas DataFrame with attributes
        id_column: Name of the ID column (default 'id')
        log: Enable logging (default: True)

    Returns:
        List of UpdateFeatureDc objects

    Raises:
        ValueError: If ID column is not found or contains empty values

    Note:
        To include only specific fields, filter the DataFrame before calling this function:
        `df = df[['id', 'field1', 'field2']]`

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({'id': ['1', '2'], 'field1': ['a', 'b']})
        >>> update_features = df_to_update_features(df, id_column='id')
    """
    import pandas as pd
    from .geodataframes import clean_attributes_for_evergis

    if df.empty:
        if log:
            _LOG.info("DataFrame is empty")
        return []

    # Check ID column exists
    if id_column not in df.columns:
        raise ValueError(
            f"Column '{id_column}' not found in DataFrame. Available columns: {list(df.columns)}"
        )

    # Check all IDs are filled
    if df[id_column].isna().any():
        raise ValueError(
            f"Column '{id_column}' contains empty values. All objects must have ID for update."
        )

    if log:
        _LOG.info(f"Converting {len(df)} objects from DataFrame to UpdateFeatureDc")

    # Prepare attributes (exclude ID column)
    attr_columns = [col for col in df.columns if col != id_column]

    # Get attributes
    if attr_columns:
        attributes_df = df[attr_columns].copy()
        # Replace all NaN values with None
        attributes_df = attributes_df.replace([pd.NA, pd.NaT, float("nan")], None)
        attributes_df = attributes_df.where(pd.notna(attributes_df), None)
        attributes_list = attributes_df.to_dict("records")
    else:
        attributes_list = [{}] * len(df)

    # Process attributes for EverGIS API compatibility
    processed_attributes = [clean_attributes_for_evergis(attrs) for attrs in attributes_list]

    # Get object IDs and convert to string
    ids = df[id_column].astype(str).tolist()

    # Create UpdateFeatureDc objects without geometry
    # Don't pass geometry at all - exclude_unset=True will omit it from serialization
    update_features = []
    for obj_id, attrs in zip(ids, processed_attributes):
        update_feature = UpdateFeatureDc(id=obj_id, attributes=attrs)
        update_features.append(update_feature)

    if log:
        _LOG.info(f"Created {len(update_features)} UpdateFeatureDc objects")
    return update_features


def df_to_features(
    df,  # pandas DataFrame
    log: bool = True,
) -> List[FeatureDc]:
    """Convert pandas DataFrame to list of FeatureDc objects without geometry.

    This function is designed for adding features to non-spatial tables (tables without geometry).
    For spatial data, use gdf_to_features instead.

    Args:
        df: pandas DataFrame with attributes
        log: Enable logging (default: True)

    Returns:
        List of FeatureDc objects

    Note:
        - IDs are auto-generated by the server, so no ID column is required
        - All DataFrame columns will be converted to feature attributes
        - To include only specific fields, filter the DataFrame before calling this function:
          `df = df[['field1', 'field2']]`

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({'name': ['a', 'b'], 'value': [1, 2]})
        >>> features = df_to_features(df)
    """
    import pandas as pd
    from .geodataframes import clean_attributes_for_evergis

    if df.empty:
        if log:
            _LOG.info("DataFrame is empty")
        return []

    if log:
        _LOG.info(f"Converting {len(df)} objects from DataFrame to FeatureDc")

    # Get all columns as attributes
    attr_columns = list(df.columns)

    # Get attributes
    if attr_columns:
        attributes_df = df[attr_columns].copy()
        # Replace all NaN values with None
        attributes_df = attributes_df.replace([pd.NA, pd.NaT, float("nan")], None)
        attributes_df = attributes_df.where(pd.notna(attributes_df), None)
        attributes_list = attributes_df.to_dict("records")
    else:
        attributes_list = [{}] * len(df)

    # Process attributes for EverGIS API compatibility
    processed_attributes = [clean_attributes_for_evergis(attrs) for attrs in attributes_list]

    # Create FeatureDc objects without geometry (IDs will be auto-generated by server)
    features = []
    for attrs in processed_attributes:
        feature = FeatureDc(properties=attrs, geometry=None)
        features.append(feature)

    if log:
        _LOG.info(f"Created {len(features)} FeatureDc objects")
    return features


def edit_layer_by_gdf(
    client: Client,
    gdf: "gpd.GeoDataFrame",
    layer_name: Optional[str] = None,
    layer_path: Optional[str] = None,
    target_sr: int = 3857,
    geometry_type: Optional[str] = None,
    id_column: str = "id",
    chunk_size_bytes: int = 5_000_000,
    log: bool = True,
) -> List[Any]:
    """Update layer objects in EverGIS from GeoDataFrame.

    Features are split into chunks by JSON payload size to ensure predictable
    API request sizes regardless of feature complexity.

    Note:
        The update_feature API endpoint does NOT support the allowAdditionalAttributes parameter.
        Fields in the GeoDataFrame that are not in the layer schema will be automatically
        filtered out during conversion. To update the layer schema, see create_layer functions.

    Args:
        client: EverGIS API client
        gdf: GeoDataFrame with geodata. Must contain a column with object IDs
        layer_name: Layer name (system name) for updating objects. Either layer_name or layer_path must be provided.
        layer_path: Resource identifier (catalog path, resource ID, or system name) to resolve the layer.
                   Either layer_name or layer_path must be provided.
        target_sr: Target coordinate system (default 3857 - Web Mercator)
        geometry_type: Filter by geometry type ('Point', 'LineString', 'Polygon', etc.)
        id_column: Name of the ID column (default 'id')
        chunk_size_bytes: Maximum chunk size in bytes (default 5MB). Features are grouped into chunks
                         where each chunk's JSON payload does not exceed this size.
        log: Enable logging (default: True)

    Returns:
        List of update results

    Raises:
        ValueError: If CRS is not set, neither layer_name nor layer_path is provided, or if both are provided,
                   or if layer_path doesn't resolve to a Layer resource, or if ID column is not found
                   or contains empty values

    Example:
        >>> import geopandas as gpd
        >>> from evergis_api import Client
        >>> from evergis_tools.features import edit_layer_by_gdf
        >>>
        >>> client = Client(base_url="...", sb_token="...")
        >>> gdf = gpd.read_file("data.geojson")
        >>> gdf['id'] = ['1', '2', '3']  # Add object IDs
        >>>
        >>> # Update using layer name
        >>> results = edit_layer_by_gdf(client, gdf, layer_name="my_layer")
        >>>
        >>> # Update using layer path
        >>> results = edit_layer_by_gdf(client, gdf, layer_path="john_doe:Projects/Data/my_layer")
        >>>
        >>> # Update with custom chunk size (10MB)
        >>> results = edit_layer_by_gdf(
        ...     client, gdf,
        ...     layer_name="polygons_layer",
        ...     geometry_type="Polygon",
        ...     target_sr=4326,
        ...     chunk_size_bytes=10_000_000
        ... )
    """
    from .catalog.resources import resolve_resource

    # Validate that exactly one of layer_name or layer_path is provided
    if layer_name is None and layer_path is None:
        raise ValueError("Either 'layer_name' or 'layer_path' must be provided")

    if layer_name is not None and layer_path is not None:
        raise ValueError("Only one of 'layer_name' or 'layer_path' should be provided, not both")

    # If layer_path is provided, resolve it to get layer_name
    if layer_path is not None:
        if log:
            _LOG.info(f"Resolving resource from identifier '{layer_path}'")

        try:
            resource = resolve_resource(client=client, identifier=layer_path)

            if resource.type != "Layer":
                raise ValueError(
                    f"Resource '{layer_path}' is not a Layer (type: {resource.type}). "
                    f"Only Layer resources are supported."
                )

            if not resource.systemName:
                raise ValueError(
                    f"Resource '{layer_path}' does not have a system name. "
                    f"Cannot update layer without system name."
                )

            layer_name = resource.systemName

            if log:
                _LOG.info(f"Resolved to layer with system name: '{layer_name}'")

        except (ValueError, ApiClientError):
            # Validation ValueErrors above and resolve errors (incl.
            # ResourceNotFound, which is an ApiClientError) propagate with
            # their type intact - not flattened into a generic ValueError.
            raise
        except Exception as e:
            raise ValueError(f"Failed to resolve resource '{layer_path}': {e}") from e

    # Check CRS
    if gdf.crs is None:
        raise ValueError(
            "GeoDataFrame must have a coordinate reference system (CRS) set. "
            "Set CRS: gdf = gdf.set_crs('EPSG:4326') or gdf = gdf.set_crs('EPSG:3857')"
        )

    # Determine geometry type from first record if not specified
    if geometry_type is None and not gdf.empty:
        first_geom_type = gdf.geometry.iloc[0].geom_type
        geometry_type = first_geom_type
        if log:
            _LOG.info(f"Geometry type not specified, using type from first record: {geometry_type}")

    # Convert GeoDataFrame to UpdateFeatureDc objects
    update_features = gdf_to_update_features(
        gdf=gdf,
        target_sr=target_sr,
        geometry_type=geometry_type,
        id_column=id_column,
        log=log,
    )

    if not update_features:
        if log:
            _LOG.warning(f"No objects to update in layer {layer_name}")
        return []

    if log:
        _LOG.info(f"Starting update of {len(update_features)} objects in layer '{layer_name}'")
        _LOG.info(
            f"First object: ID={update_features[0].id}, geometry_type={getattr(update_features[0].geometry, 'type', None)}"
        )

    # Split features into chunks by size
    chunks = chunk_features_by_size(update_features, chunk_size_bytes, log=log)

    if log:
        _LOG.info(
            f"Split into {len(chunks)} chunks (max {chunk_size_bytes / 1_000_000:.1f} MB each)"
        )

    results = []
    total_updated = 0
    total_count = len(update_features)

    # Send objects in chunks
    for chunk_num, chunk in enumerate(chunks, 1):
        if log:
            # Calculate actual chunk size for logging
            chunk_json = json.dumps([f.model_dump(exclude_unset=True, exclude_none=True) for f in chunk])
            chunk_size_mb = len(chunk_json.encode("utf-8")) / 1_000_000
            _LOG.info(
                f"Chunk {chunk_num}/{len(chunks)}: {len(chunk)} features, ~{chunk_size_mb:.2f} MB"
            )

        try:
            result = client.layers.update_feature(name=layer_name, body=chunk)
            updated_count = len(result.updatedIds or [])
            total_updated += updated_count
            results.append(result)

            total_count_left = total_count - total_updated

            if log:
                _LOG.info(f" - Updated: {updated_count} objects, remaining: {total_count_left}")

        except ApiClientError as e:
            if log:
                _LOG.error(f"API Error {e.status_code} in chunk {chunk_num}: {e.response_text}")
            raise
        except Exception as e:
            if log:
                _LOG.error(f" - Unexpected error in chunk {chunk_num}: {e}")
            raise

    if log:
        _LOG.info(f"✅ Completed! Total {total_updated} objects updated in layer '{layer_name}'")
    return results


def edit_layer_by_df(
    client: Client,
    df,  # pandas DataFrame
    layer_name: Optional[str] = None,
    layer_path: Optional[str] = None,
    id_column: str = "id",
    chunk_size_bytes: int = 1_200_000,
    log: bool = True,
) -> List[Any]:
    """Update layer objects in EverGIS from pandas DataFrame (for non-spatial tables).

    This function is designed for updating non-spatial tables (tables without geometry).
    For spatial data, use edit_layer_by_gdf instead.

    Features are split into chunks by JSON payload size to ensure predictable
    API request sizes regardless of feature complexity.

    Note:
        The update_feature API endpoint does NOT support the allowAdditionalAttributes parameter.
        Fields in the DataFrame that are not in the layer schema will be automatically
        filtered out during conversion. To update the layer schema, see create_layer functions.

    Args:
        client: EverGIS API client
        df: pandas DataFrame with attributes. Must contain a column with object IDs
        layer_name: Layer name (system name) for updating objects. Either layer_name or layer_path must be provided.
        layer_path: Resource identifier (catalog path, resource ID, or system name) to resolve the layer.
                   Either layer_name or layer_path must be provided.
        id_column: Name of the ID column (default 'id')
        chunk_size_bytes: Maximum chunk size in bytes (default 5MB). Features are grouped into chunks
                         where each chunk's JSON payload does not exceed this size.
        log: Enable logging (default: True)

    Returns:
        List of update results

    Raises:
        ValueError: If neither layer_name nor layer_path is provided, or if both are provided,
                   or if layer_path doesn't resolve to a Layer resource, or if ID column is not found
                   or contains empty values

    Example:
        >>> import pandas as pd
        >>> from evergis_api import Client
        >>> from evergis_tools.features import edit_layer_by_df
        >>>
        >>> client = Client(base_url="...", sb_token="...")
        >>> df = pd.DataFrame({'id': ['1', '2'], 'field1': ['a', 'b']})
        >>>
        >>> # Update using layer name
        >>> results = edit_layer_by_df(client, df, layer_name="my_table")
        >>>
        >>> # Update using layer path
        >>> results = edit_layer_by_df(client, df, layer_path="john_doe:Projects/Data/my_table")
        >>>
        >>> # Update with custom chunk size (10MB)
        >>> results = edit_layer_by_df(
        ...     client, df,
        ...     layer_name="attributes_table",
        ...     chunk_size_bytes=10_000_000
        ... )
    """
    from .catalog.resources import resolve_resource

    # Validate that exactly one of layer_name or layer_path is provided
    if layer_name is None and layer_path is None:
        raise ValueError("Either 'layer_name' or 'layer_path' must be provided")

    if layer_name is not None and layer_path is not None:
        raise ValueError("Only one of 'layer_name' or 'layer_path' should be provided, not both")

    # If layer_path is provided, resolve it to get layer_name
    if layer_path is not None:
        if log:
            _LOG.info(f"Resolving resource from identifier '{layer_path}'")

        try:
            resource = resolve_resource(client=client, identifier=layer_path)

            if resource.type != "Layer":
                raise ValueError(
                    f"Resource '{layer_path}' is not a Layer (type: {resource.type}). "
                    f"Only Layer resources are supported."
                )

            if not resource.systemName:
                raise ValueError(
                    f"Resource '{layer_path}' does not have a system name. "
                    f"Cannot update layer without system name."
                )

            layer_name = resource.systemName

            if log:
                _LOG.info(f"Resolved to layer with system name: '{layer_name}'")

        except (ValueError, ApiClientError):
            # Validation ValueErrors above and resolve errors (incl.
            # ResourceNotFound, which is an ApiClientError) propagate with
            # their type intact - not flattened into a generic ValueError.
            raise
        except Exception as e:
            raise ValueError(f"Failed to resolve resource '{layer_path}': {e}") from e

    # Convert DataFrame to UpdateFeatureDc objects
    update_features = df_to_update_features(
        df=df,
        id_column=id_column,
        log=log,
    )
    if not update_features:
        if log:
            _LOG.warning(f"No objects to update in layer {layer_name}")
        return []

    if log:
        _LOG.info(f"Starting update of {len(update_features)} objects in layer '{layer_name}'")

    # Split features into chunks by size
    chunks = chunk_features_by_size(update_features, chunk_size_bytes, log=log)

    if log:
        _LOG.info(
            f"Split into {len(chunks)} chunks (max {chunk_size_bytes / 1_000_000:.1f} MB each)"
        )

    results = []
    total_updated = 0
    total_count = len(update_features)

    # Send objects in chunks
    for chunk_num, chunk in enumerate(chunks, 1):
        if log:
            # Calculate actual chunk size for logging
            chunk_json = json.dumps([f.model_dump(exclude_unset=True, exclude_none=True) for f in chunk])
            chunk_size_mb = len(chunk_json.encode("utf-8")) / 1_000_000
            _LOG.info(
                f"Chunk {chunk_num}/{len(chunks)}: {len(chunk)} features, ~{chunk_size_mb:.2f} MB"
            )

        try:

            result = client.layers.update_feature(name=layer_name, body=chunk)
            updated_count = len(result.updatedIds or [])
            total_updated += updated_count
            results.append(result)

            total_count_left = total_count - total_updated

            if log:
                _LOG.info(f" - Updated: {updated_count} objects, remaining: {total_count_left}")

        except ApiClientError as e:
            if log:
                _LOG.error(f"API Error {e.status_code} in chunk {chunk_num}: {e.response_text}")
            raise
        except Exception as e:
            if log:
                _LOG.error(f" - Unexpected error in chunk {chunk_num}: {e}")
            raise

    if log:
        _LOG.info(f"✅ Completed! Total {total_updated} objects updated in layer '{layer_name}'")
    return results


def gdf_to_paged_feature_list(
    gdf: "gpd.GeoDataFrame",
    offset: int = 0,
    limit: Optional[int] = None,
    target_sr: int = 4326,
    geometry_type: Optional[str] = None,
) -> PagedFeaturesListDc:
    """Convert GeoDataFrame to PagedFeaturesListDc with pagination.

    Args:
        gdf: GeoDataFrame with geodata
        offset: Offset for pagination (default 0)
        limit: Maximum number of objects per page (if None - all objects)
        target_sr: Target coordinate system (default 4326 - WGS84)
        geometry_type: Filter by geometry type ('Point', 'LineString', 'Polygon', etc.)

    Returns:
        PagedFeaturesListDc object with pagination

    Example:
        >>> paged_result = gdf_to_paged_feature_list(
        ...     gdf=my_gdf,
        ...     offset=0,
        ...     limit=100,
        ...     target_sr=4326
        ... )
        >>> print(f"Total: {paged_result.totalCount}, Features: {len(paged_result.features)}")
    """
    # Convert GeoDataFrame to a list of FeatureDc
    all_features = gdf_to_features(gdf=gdf, target_sr=target_sr, geometry_type=geometry_type)

    total_count = len(all_features)

    # Apply pagination
    if limit is None:
        # If limit is not set, take all objects starting from offset
        features_page = all_features[offset:]
        actual_limit = total_count - offset
    else:
        # Take a slice from offset to offset + limit
        features_page = all_features[offset : offset + limit]
        actual_limit = limit

    # Create PagedFeaturesListDc
    paged_result = PagedFeaturesListDc(
        features=features_page, offset=offset, limit=actual_limit, totalCount=total_count
    )

    return paged_result


def query_layer_to_gdf(
    client: Client,
    layer_name: Optional[str] = None,
    layer_path: Optional[str] = None,
    attributes: Optional[List[str]] = None,
    conditions: Optional[List[str]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    parameters: Optional[dict] = None,
    sort: Optional[List[str]] = None,
    sr_id: int = 4326,
    with_geom: bool = True,
    target_crs: str = "EPSG:4326",
    log: bool = True,
) -> "gpd.GeoDataFrame":
    """Query layer objects and return them as GeoDataFrame.

    Args:
        client: EverGIS API client
        layer_name: Layer name (system name) for querying objects. Either layer_name or layer_path must be provided.
        layer_path: Resource identifier (catalog path, resource ID, or system name) to resolve the layer.
                   Either layer_name or layer_path must be provided.
        attributes: List of attributes to fetch (if None - all attributes)
        conditions: List of SQL WHERE conditions for filtering
        limit: Maximum number of objects to return
        offset: Offset for pagination
        parameters: Dictionary of parameters for condition substitution (e.g., {'@status': 'active'})
        sort: List of fields for sorting using the ``±field`` format -
            ``"field"`` for ASC and ``"-field"`` for DESC. The SQL form
            (``"name DESC"``) is **not** accepted by the server. Example:
            ``["-created_at", "name"]``.
        sr_id: Coordinate system ID for geometry (default 4326)
        with_geom: Include geometry in result (default True)
        target_crs: Target coordinate system for GeoDataFrame (default 'EPSG:4326')
        log: Enable logging (default: True)

    Returns:
        GeoDataFrame with layer objects

    Raises:
        ValueError: If neither layer_name nor layer_path is provided, or if both are provided,
                   or if layer_path doesn't resolve to a Layer resource

    Example:
        >>> from evergis_api import Client
        >>> from evergis_tools.features import query_layer_to_gdf
        >>>
        >>> client = Client(base_url="...", sb_token="...")
        >>>
        >>> # Simple query using layer name
        >>> gdf = query_layer_to_gdf(client, layer_name="my_layer")
        >>>
        >>> # Query using layer path (catalog path, resource ID, or system name)
        >>> gdf = query_layer_to_gdf(client, layer_path="john_doe:Projects/Data/my_layer")
        >>>
        >>> # Query with filtering and sorting. Sort uses ``±field``:
        >>> # ``"name"`` is ASC, ``"-name"`` is DESC.
        >>> gdf = query_layer_to_gdf(
        ...     client=client,
        ...     layer_name="my_layer",
        ...     attributes=["id", "name", "status"],
        ...     conditions=["WHERE status = @status"],
        ...     parameters={"@status": "active"},
        ...     limit=100,
        ...     sort=["-name"],
        ...     sr_id=3857
        ... )
    """
    from .geodataframes import paged_features_to_geodataframe
    from evergis_api.schemas import GetFeaturesParametersDc
    from .catalog.resources import resolve_resource

    log_level = logging.INFO if log else logging.ERROR

    # Validate that exactly one of layer_name or layer_path is provided
    if layer_name is None and layer_path is None:
        raise ValueError("Either 'layer_name' or 'layer_path' must be provided")

    if layer_name is not None and layer_path is not None:
        raise ValueError("Only one of 'layer_name' or 'layer_path' should be provided, not both")

    # If layer_path is provided, resolve it to get layer_name
    if layer_path is not None:
        if log:
            _LOG.info(f"Resolving resource from identifier '{layer_path}'")

        try:
            resource = resolve_resource(client=client, identifier=layer_path)

            if resource.type != "Layer":
                raise ValueError(
                    f"Resource '{layer_path}' is not a Layer (type: {resource.type}). "
                    f"Only Layer resources are supported."
                )

            if not resource.systemName:
                raise ValueError(
                    f"Resource '{layer_path}' does not have a system name. "
                    f"Cannot query layer without system name."
                )

            layer_name = resource.systemName

            if log:
                _LOG.info(f"Resolved to layer with system name: '{layer_name}'")

        except (ValueError, ApiClientError):
            # Validation ValueErrors above and resolve errors (incl.
            # ResourceNotFound, which is an ApiClientError) propagate with
            # their type intact - not flattened into a generic ValueError.
            raise
        except Exception as e:
            raise ValueError(f"Failed to resolve resource '{layer_path}': {e}") from e

    if log:
        _LOG.info(f"Querying objects from layer '{layer_name}'")

    # Server's POST /features/query rejects null values for Int32 fields.
    # The generated client serializes the body with exclude_unset=True, so
    # build the model with only the keys the caller actually provided.
    kwargs = {"srId": sr_id, "withGeom": with_geom}
    if attributes is not None:
        # When the caller projects a subset of columns but still wants
        # geometry in the GeoDataFrame, make sure the geometry column is
        # part of the projection.
        if with_geom and "geometry" not in attributes:
            attributes = list(attributes) + ["geometry"]
        kwargs["attributes"] = attributes
    if conditions is not None:
        kwargs["conditions"] = conditions
    if limit is not None:
        kwargs["limit"] = limit
    if offset is not None:
        kwargs["offset"] = offset
    if parameters is not None:
        kwargs["parameters"] = parameters
    if sort is not None:
        kwargs["sort"] = sort
    query_params = GetFeaturesParametersDc(**kwargs)

    try:
        # Execute API request
        result = client.layers.get_features(name=layer_name, body=query_params)

        # Convert result to GeoDataFrame
        gdf = paged_features_to_geodataframe(
            paged_features_list=result, target_crs=target_crs, logger=_LOG, log_level=log_level
        )

        if log:
            _LOG.info(f"Retrieved GeoDataFrame with {len(gdf)} objects from layer '{layer_name}'")
        return gdf

    except ApiClientError as e:
        if log:
            _LOG.error(
                f"API Error {e.status_code} when querying layer '{layer_name}': {e.response_text}"
            )
        raise
    except Exception as e:
        if log:
            _LOG.error(f"Unexpected error when querying layer '{layer_name}': {e}")
        raise


def query_layer_to_df(
    client: Client,
    layer_name: str,
    *,
    attributes: Optional[List[str]] = None,
    conditions: Optional[List[str]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    parameters: Optional[dict] = None,
    sort: Optional[List[str]] = None,
    log: bool = False,
):
    """Query a table layer (no geometry) and return a pandas DataFrame.

    Counterpart to :func:`query_layer_to_gdf` for non-spatial tables.
    Issues a single ``client.layers.get_features`` call with
    ``withGeom=False`` and folds ``properties`` of every returned
    feature into a DataFrame. For paged reads issue several calls
    incrementing ``offset`` yourself - the wrapper does not auto-page.

    Args:
        client: EverGIS API client.
        layer_name: Layer name (system name) for querying objects.
        attributes: List of attributes to fetch (if None - all attributes).
        conditions: List of SQL WHERE conditions (combined by the server).
        limit: Maximum number of rows to return.
        offset: Offset for pagination.
        parameters: Dictionary of parameters for condition substitution.
        sort: List of fields for sorting using the ``±field`` format -
            ``"field"`` for ASC and ``"-field"`` for DESC. The SQL form
            (``"name DESC"``) is **not** accepted by the server. Example:
            ``["-created_at", "name"]``.
        log: Enable logging (default: False).

    Returns:
        pandas DataFrame with feature attributes (no geometry column).

    Example:
        >>> df = query_layer_to_df(
        ...     client,
        ...     layer_name="john_doe.evg_features_logs",
        ...     attributes=["station_code", "metric", "value", "recorded_at"],
        ...     conditions=["WHERE metric = 'temp_c'"],
        ...     sort=["-recorded_at"],
        ...     limit=100,
        ... )
    """
    import pandas as pd
    from evergis_api.schemas import GetFeaturesParametersDc

    # Server's POST /features/query rejects null values for Int32 fields.
    # The generated client serializes the body with exclude_unset=True, so
    # build the model with only the keys the caller actually provided.
    kwargs = {"withGeom": False}
    if attributes is not None:
        kwargs["attributes"] = attributes
    if conditions is not None:
        kwargs["conditions"] = conditions
    if limit is not None:
        kwargs["limit"] = limit
    if offset is not None:
        kwargs["offset"] = offset
    if parameters is not None:
        kwargs["parameters"] = parameters
    if sort is not None:
        kwargs["sort"] = sort
    body = GetFeaturesParametersDc(**kwargs)
    if log:
        _LOG.info(f"Querying table objects from layer '{layer_name}'")
    result = client.layers.get_features(name=layer_name, body=body)
    rows = [f.properties for f in (result.features or [])]
    return pd.DataFrame(rows)


# Long-form public name kept as an alias of ``query_layer_to_df`` so
# external callers can use the symmetric pair with ``query_layer_to_gdf``.
query_layer_to_dataframe = query_layer_to_df


def count_features(
    client: Client,
    layer_name: str,
    *,
    condition: Optional[str] = None,
    log: bool = False,
) -> int:
    """Return the number of features in a layer.

    Thin wrapper over ``client.layers.get_filtered_features_count_1``.
    Pass ``condition`` as an EQL filter to count a subset, with or without
    a leading ``WHERE`` (it is added when missing, matching
    :func:`delete_features_by_condition` / :func:`query_layer_to_gdf`);
    pass ``None`` to count every row.

    The endpoint's ``condition`` is a ``WHERE`` clause: a string-literal
    filter without the leading ``WHERE`` (e.g. ``status = 'closed'``) is
    rejected by the server, so this wrapper prepends ``WHERE`` when absent.
    """
    if condition:
        condition = condition.strip()
        if not condition.upper().startswith("WHERE"):
            condition = f"WHERE {condition}"
    if log:
        _LOG.info(
            f"Counting features in '{layer_name}'"
            + (f" {condition!r}" if condition else "")
        )
    return client.layers.get_filtered_features_count_1(
        name=layer_name, condition=condition,
    )


def delete_features_by_ids(
    client: Client,
    layer_name: str,
    ids: List[Any],
    *,
    chunk_size: int = 1000,
    log: bool = False,
) -> int:
    """Delete features by id from a layer in chunks.

    Splits ``ids`` into batches of ``chunk_size`` and issues one
    ``client.layers.delete_features`` call per batch. Returns the total
    number of ids submitted (the server does not differentiate matched
    vs missing ids in the response).
    """
    str_ids = [str(i) for i in ids]
    if not str_ids:
        return 0
    total = 0
    for i in range(0, len(str_ids), chunk_size):
        batch = str_ids[i : i + chunk_size]
        if log:
            _LOG.info(
                f"Deleting {len(batch)} features from '{layer_name}'"
                f" (chunk {i // chunk_size + 1})"
            )
        client.layers.delete_features(name=layer_name, ids=batch)
        total += len(batch)
    return total


def delete_features_by_condition(
    client: Client,
    layer_name: str,
    condition: str,
    *,
    log: bool = False,
):
    """Delete features matching an EQL ``WHERE`` clause.

    Thin wrapper over ``client.layers.delete_by_condition``. ``condition``
    must include the leading ``WHERE`` keyword, e.g.
    ``"WHERE is_anomaly = true OR value < 0"``. This matches the EverGIS
    convention for filter strings on every endpoint that accepts one.
    """
    if log:
        _LOG.info(f"Deleting features from '{layer_name}' where {condition!r}")
    return client.layers.delete_by_condition(
        name=layer_name, condition=condition,
    )
