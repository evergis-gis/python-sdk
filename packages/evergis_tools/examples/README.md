# evergis-tools examples

Runnable scripts that show how to use `evergis-tools`, organized by topic.

## Topics

- **account/** - authentication, user and role management
- **catalog/** - resources, folders, files, permissions, data sources, links
- **eql/** - EQL queries into pandas / GeoPandas
- **layers/** - create layers, read / add / edit / delete features, update schema and style
- **tables/** - table column operations
- **tasks/** - server-side tasks: import, export, geoprocessing, network analysis, the task manager
- **geo_tools/** - isochrones, routes, OD-matrix, Voronoi
- **utils/** - helpers (e.g. safe field-name transliteration)

## Setup

1. Install the packages (editable, from a checkout):

```bash
pip install -e packages/evergis_api -e packages/evergis_tools
```

2. Create a `.env` in the repository root (the client reads it automatically):

```ini
EVERGIS_HOST=https://beta.evergis.ru/sp
EVERGIS_SB_TOKEN=your_token_here
```

`Client()` picks up `EVERGIS_HOST` / `EVERGIS_SB_TOKEN` from the environment
(or that `.env`), so the examples construct it with no arguments.

3. Optional - provision the demo layers most examples read from
   (`evg_overture_*`, `evg_stations`, ...):

```bash
python -m evergis_tutorial_setup themes all
```

## Running

Run from the repository root:

```bash
python packages/evergis_tools/examples/eql/nearest_metro.py
python packages/evergis_tools/examples/layers/create/gdf_to_layer.py
python packages/evergis_tools/examples/tasks/import/csv_import_to_layer.py
```

Some examples create resources under `{username}/EverGIS Resources/python/...`;
`PROJECT_PATH` and `RESOURCE_PREFIX` can be overridden via `.env`.
