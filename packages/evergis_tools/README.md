# evergis-tools

High-level Python utilities for the EverGIS geospatial platform, built on top of
[`evergis-api`](../evergis_api).

It covers catalog management, task execution (import / export / geoprocessing),
EQL queries straight into pandas / GeoPandas, geometry conversion, and
GeoDataFrame integration - so you work with layers and data instead of raw API
calls.

## Install

`evergis-tools` depends on `evergis-api`; neither is on a package index yet, so
install both from git in one command (pip resolves them together - `evergis-api`
must be in the same command):

```bash
pip install \
  "git+https://github.com/evergis-gis/python-sdk.git#subdirectory=packages/evergis_api" \
  "git+https://github.com/evergis-gis/python-sdk.git#subdirectory=packages/evergis_tools"
```

> Once published to a package index this becomes `pip install evergis-tools`.

Editable, from a checkout of the monorepo (inside a virtualenv):

```bash
uv pip install -e packages/evergis_api      # the client it builds on
uv pip install -e packages/evergis_tools
```

`geopandas` / `shapely` are pulled in for the geospatial helpers.

## Quick start

The client reads credentials from the environment (`EVERGIS_HOST`,
`EVERGIS_SB_TOKEN`), so it is constructed with no arguments:

```python
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_geodataframe

with Client() as client:
    gdf = eql_query_to_geodataframe("SELECT * FROM em.my_layer", client)
```

Typed errors are importable from the top level:

```python
from evergis_tools import ResourceExists, ResourceNotFound
```

## Documentation

- **API reference** - `docs/kb/` (knowledge base: every public function, its
  parameters, returns, and gotchas).
- **Examples** - `examples/` (runnable, organized by topic).
- **Cookbook** - `docs/cookbook/` (task-oriented recipes for the EverGIS sandbox).
- **Changelog** - [`CHANGELOG.md`](CHANGELOG.md).

## License

Apache License 2.0. Copyright 2026 Everpoint.
