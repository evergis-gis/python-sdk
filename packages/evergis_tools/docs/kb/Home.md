---
title: evergis_tools Knowledge Base
---

# evergis_tools

High-level Python utilities for the EverGIS geospatial platform.

## Quick Navigation

### Core Modules
- [[Layers/Layers|Layers]] - Create, read, update layers
- [[Features]] - Add/edit features, chunked upload
- [[EQL]] - Execute EQL queries, get DataFrames
- [[GeoDataFrames]] - Convert between GeoDataFrame and EverGIS formats
- [[Attributes]] - Type conversion and validation
- [[AttributeTypes/AttributeTypes|Attribute Types]] - Attachments, Calculated, custom subtypes
- [[Account]] - login_with_credentials, users, roles
- [[Errors]] - Typed exceptions (`ResourceExists`, ...) and status-code predicates

### Catalog
- [[Catalog/Catalog|Catalog]] - Resources, folders, files, maps, permissions

### Geometry
- [[Geometry]] - Shapely/EverGIS conversion, EWKT, reprojection, validators

### Tasks
- [[Tasks]] - Task execution, progress monitoring (TaskManager, run_task)
- [[Tasks/Import|Tasks/Import]] - CSV/XLSX/Shapefile/GPKG/FGDB to layer
- [[Tasks/Export|Tasks/Export]] - layer to CSV/XLSX/Shapefile/GPKG/GeoJSON
- [[Tasks/Geoprocessing|Tasks/Geoprocessing]] - copy / update / delete / union via EQL, validate / fix geometry
- [[Tasks/Network|Tasks/Network]] - batch isochrones, OD-matrix
- [[Tasks/WorkerModels|Tasks/WorkerModels]] - auto-generated StartParameters

### Specialized
- [[Tables]] - Materialized views, table column ops
- [[GeoTools]] - Single isochrones, routes, Voronoi
- [[Async]] - Async versions of EQL functions
- [[PydanticUtils]] - Pydantic model/layer schema utilities
- [[Validation]] - Input validation


### Use Cases
- [[UseCases/UseCases|Use Cases]] - End-to-end scenarios (geomarketing, analytics)

## Architecture

```
evergis_tools → evergis_api
```

All functions accept `client: Client` as first argument (sync) or `client: AsyncClient` (async).

## Releases
- [CHANGELOG](../../CHANGELOG.md) - what changed per version (Breaking / Changed / Added / Fixed)

## Common Patterns
- [[Patterns - Client]] - Client initialization
- [[Patterns - Overwrite]] - Layer overwrite modes
- [[Patterns - Chunking]] - Size-based chunking
- [[Patterns - StringFormat]] - Attribute formatting
