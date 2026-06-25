---
title: GeoDataFrames
module: evergis_tools.geodataframes
---

# GeoDataFrames

Convert between GeoDataFrame/DataFrame and EverGIS formats. Import: `from evergis_tools.geodataframes import ...`

## gdf_to_features
Convert GeoDataFrame to list of FeatureDc objects.

```python
from evergis_tools.geodataframes import gdf_to_features

features = gdf_to_features(gdf, target_sr=4326, geometry_type="Point")
```

## gdf_to_feature_collection
Convert GeoDataFrame to GeoJSON FeatureCollection dict.

```python
from evergis_tools.geodataframes import gdf_to_feature_collection

result = gdf_to_feature_collection(gdf, target_sr=4326)
# {"type": "FeatureCollection", "features": [...], "totalCount": N, "offset": 0, "limit": 0}
```

## df_to_feature_collection
Convert pandas DataFrame (no geometry) to FeatureCollection dict.

```python
from evergis_tools.geodataframes import df_to_feature_collection

result = df_to_feature_collection(df)
```

## paged_features_to_geodataframe
Convert API response (PagedFeaturesListDc) to GeoDataFrame.

```python
from evergis_tools.geodataframes import paged_features_to_geodataframe

gdf = paged_features_to_geodataframe(paged_result, target_crs="EPSG:4326")
```

## filter_gdf_by_geometry_type
Filter GeoDataFrame by geometry type with alias support.

```python
from evergis_tools.geodataframes import filter_gdf_by_geometry_type

polygons_only = filter_gdf_by_geometry_type(gdf, "MultiPolygon")
```

Aliases: `"multipolygon"` matches both Polygon and MultiPolygon, etc.

## See Also
- [[Features]] - High-level feature upload
- [[EQL]] - Query results as GeoDataFrame
