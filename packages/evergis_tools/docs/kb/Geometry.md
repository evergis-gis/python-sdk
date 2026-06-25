---
title: Geometry
module: evergis_tools.geometry
---

# Geometry

Shapely/EverGIS geometry conversion, EWKT, reprojection, validators. Import: `from evergis_tools.geometry import ...`

## Conversions

### shapely_to_evergis_geometry
Shapely geometry -> EverGIS GeometryDc (PointDc, PolygonDc, etc.)

```python
from evergis_tools.geometry import shapely_to_evergis_geometry
from shapely.geometry import Point

geom_dc = shapely_to_evergis_geometry(Point(37.6, 55.7), sr_id=4326)
# PointDc(type='Point', coordinates=(37.6, 55.7), srId=4326)
```

### evergis_geometry_to_shapely
EverGIS GeometryDc -> Shapely geometry.

```python
from evergis_tools.geometry import evergis_geometry_to_shapely

shapely_geom = evergis_geometry_to_shapely(point_dc)
```

### evergis_dict_to_shapely
EverGIS geometry dict (old or GeoJSON format) -> Shapely.

```python
from evergis_tools.geometry import evergis_dict_to_shapely

geom = evergis_dict_to_shapely({"type": "Point", "coordinates": [37.6, 55.7], "srId": 4326})
```

## EWKT

### ewkt_to_shapely / shapely_to_ewkt
Parse/generate Extended WKT strings.

```python
from evergis_tools.geometry import ewkt_to_shapely, shapely_to_ewkt

geom = ewkt_to_shapely("SRID=4326;POINT(37.6 55.7)")
ewkt = shapely_to_ewkt(geom, srid=4326)  # "SRID=4326;POINT (37.6 55.7)"
```

## Reprojection

### shapely_reproject
Reproject Shapely geometry between coordinate systems.

```python
from evergis_tools.geometry import shapely_reproject

geom_3857 = shapely_reproject(geom_4326, source_srid=4326, target_srid=3857)
```

## Validators

```python
from evergis_tools.geometry import (
    validate_srid,           # SRID in valid range (1-32767)
    validate_geometry_type,  # Valid type name
    validate_ewkt_format,    # Valid EWKT string
    validate_coordinates,    # Valid coordinate arrays
    validate_bbox,           # Valid bounding box [minx,miny,maxx,maxy]
    validate_geojson_feature,# Valid GeoJSON structure
    assert_geometry_instance,# Assert type match
)
```

## See Also
- [[GeoDataFrames]] - GeoDataFrame conversions using geometry module
- [[GeoTools]] - Network analysis using geometries
