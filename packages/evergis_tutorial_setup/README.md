# evergis-tutorial-setup

Per-user tutorial workspace provisioner for the EverGIS examples.

It builds the writable, per-user side of the tutorial catalog - seed
layers, query layers, companion maps, mirrored example scripts and
navigation symlinks - that the `evergis_tools` examples read from and
mutate. The shared, read-only sample data (Overture layers and raw
source files under `SAMPLE_DATA_OWNER`, default `edu`) is provisioned
separately by `evergis_catalog_tools`; this package only references it
via the `EXTERNAL_LAYERS` registry.

## Install

```bash
uv pip install -e packages/evergis_tools
uv pip install -e packages/evergis_tutorial_setup
```

## Usage

```bash
# Provision one or more themes (or `all`); --force resets existing seeds.
python -m evergis_tutorial_setup themes features --force
python -m evergis_tutorial_setup themes all --force
```

```python
from evergis_tutorial_setup import setup

setup(["features"], force=True)
setup(["all"], force=True)
```

### CLI vs API (sandbox note)

The `python -m evergis_tutorial_setup ...` form is a convenience for
local use. The EverGIS `python-script-runner` sandbox runs **Python
only - no CLI**, so there provision through the `setup()` API instead.

`setup()` also mirrors the example scripts from
`packages/evergis_tools/examples/` into the catalog. That step needs a
monorepo checkout; in the sandbox (no repo on disk) it is skipped with a
`examples directory not found; mirror skipped` notice - layers, folders,
maps and symlinks are still created normally.

## Themes

Nine themes, each a self-contained topic. Dependencies (`depends on`)
are pulled in automatically, so provisioning a theme also provisions
what it needs (every theme except `account` / `catalog` needs `shared`,
which seeds the derived Overture query layers).

| Theme | What it provisions | Example scripts |
|-------|--------------------|-----------------|
| `account` | Companion map only | `examples/account/` - users, roles, auth (7) |
| `catalog` | Companion map + sandbox folders | `examples/catalog/` - folders, files, links, permissions, data sources (31) |
| `shared` | Seed query layers `evg_places_qry`, `evg_distr_poi_count` (parametrised wrappers over Overture) | none - base for other themes |
| `features` | Seed layers `evg_stations` (Point), `evg_logs` (table) + map | `examples/layers/features/` - read / add / edit / delete features (12) |
| `layers` | Seed layers `evg_places_update_layer`, `evg_sandbox_polygon` + map | `examples/layers/create`, `read`, `update` - create / configure layers (17) |
| `eql` | Map only | `examples/eql/` - EQL to (Geo)DataFrame, joins, window functions (12) |
| `geo_tools` | Seed result layers (isochrones / routes / voronoi, + their input points) + map | `examples/geo_tools/` - isochrones, routes, Voronoi, OD matrix (8) |
| `tasks` | Map + `source_files` symlink to the shared sample data | `examples/tasks/` - import, export, geoprocessing, network analysis (23) |
| `widgets` | Map + `images/` folder | `examples/widgets/` - feature cards / edit forms (4) |

## Running a theme and its examples

1. Provision the theme (creates folders, seed layers, the map and mirrors
   the example scripts into the catalog). `--force` resets existing seeds:

   ```bash
   python -m evergis_tutorial_setup themes features --force
   ```

2. Run any example for that theme from the repo root (each script is
   standalone and reads `EVERGIS_HOST` / `EVERGIS_SB_TOKEN` from the env):

   ```bash
   python packages/evergis_tools/examples/layers/features/read_features.py
   python packages/evergis_tools/examples/layers/features/add_features.py
   ```

The example folder that pairs with each theme is listed in the table
above. Provision `all` to set up every theme at once:

```bash
python -m evergis_tutorial_setup themes all --force
```

## Where it lands in the catalog

Everything is created under your own account, in one folder per theme:

```
{username}:{PROJECT_PATH}/
└── <theme>/
    ├── scripts/                  mirrored example scripts (read-only copy)
    ├── data/                     seed layers the theme pre-creates
    ├── results/                  output of examples that create layers
    ├── {username}.evg_map_<theme>   companion map
    └── (symlink) <theme>         link back, visible in the map's layer list
```

`PROJECT_PATH` (default `EverGIS Resources/python`) and the resource
prefix `RESOURCE_PREFIX` (default `evg`) come from the environment / `.env`,
so seed layers are named `{username}.evg_<short>` (e.g. `john.evg_stations`).
The shared Overture sample data the examples read from stays under
`SAMPLE_DATA_OWNER` (default `edu`) and is never created here.

So after `python -m evergis_tutorial_setup themes features --force` you get
`{username}:EverGIS Resources/python/features/` with `data/` (the
`evg_stations` / `evg_logs` seeds), `scripts/` (the mirrored feature
examples), an empty `results/`, and the `evg_map_features` map.

## Package layout (source)

Each theme is a subpackage under `evergis_tutorial_setup/themes/<theme>/`.
Its `__init__.py` declares `THEME = ThemeConfig(...)`; sibling modules
declare individual layers as `LAYER = ...`. The runner (`_runner.py`)
discovers everything from the filesystem - no explicit registration.

Dependency direction: `evergis_tutorial_setup -> evergis_tools -> evergis_api`.
