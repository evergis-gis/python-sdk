---
title: Tutorial Setup
module: evergis_tutorial_setup
---

# Tutorial Setup

Provisions folders, seed layers, mirrored example scripts, and companion maps for the `evergis_tools` tutorial in a live EverGIS instance. Import: `from evergis_tutorial_setup import setup`

---

## CLI

```bash
python -m evergis_tutorial_setup themes <names> [--force]
```

`themes` is an `argparse` subcommand (`__main__.py` uses `add_subparsers(dest="step", required=True)`). `names` is a positional `nargs="+"` argument on that subparser.

| Arg / Flag | Description |
|------------|-------------|
| `names` | One or more theme subpackage names under `tutorial_setup/themes/`. Use `all` to provision every discovered theme. |
| `--force` | Overwrite existing mirrored example files (`upload_file(..., rewrite=True)`). Seed layers are recreated on every run independent of this flag. |

Examples:

```bash
# Full rebuild of every theme.
python -m evergis_tutorial_setup themes all --force

# Just the features tutorial (pulls in 'shared' as a dependency).
python -m evergis_tutorial_setup themes features
```

Dependencies declared via `ThemeConfig.depends_on` are pulled in transitively and applied first (topological order, deterministic).

---

## Python API

### setup

```python
from evergis_tutorial_setup import setup

setup(["features"], force=True)
```

Signature: `setup(themes: Sequence[str], *, force: bool = False, client: Client | None = None) -> None`. `force` and `client` are keyword-only.

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `themes` | required | Theme names, or `["all"]`. Dependencies are pulled in transitively. |
| `force` | `False` | Overwrite mirrored example files. Seed layers are always recreated regardless of this flag (see Key Behaviors). |
| `client` | `None` | Optional pre-built [[Patterns - Client\|Client]]; when omitted, `Client()` is opened and closed by this call. |

**Returns:** `None`. Progress is printed to stdout per theme / per layer.

---

## Themes

A theme is a Python subpackage under `evergis_tutorial_setup.themes.<name>/`:

* `__init__.py` declares `THEME = ThemeConfig(...)` (metadata, folder layout, optional companion map, optional symlinks).
* Sibling modules each declare one `LAYER = LayerSchema(...)` or `LAYER = LayerQuery(...)` constant. The runner discovers them by walking the package; modules without a `LAYER` are silently skipped (helper modules like `stations_data.py` carrying fixture rows).
* The `short` name of each layer defaults to the module file stem (`themes/features/stations.py` -> `evg_stations`); set `short=` explicitly only when the layer name must differ from the file name.

Bundled themes:

| Theme | Notes |
|-------|-------|
| `shared` | Cross-theme derived layers (e.g. `places_qry`, `distr_poi_count`) reused by other themes. |
| `account` | Auth / users / roles examples. |
| `catalog` | Folder, file, permission, symlink operations. |
| `eql` | EQL query examples (parametrised queries, joins). |
| `features` | Add / read / edit / delete features against seed `stations` / `logs`. |
| `geo_tools` | Geo-processing tasks (isochrones, routing). |
| `layers` | Layer create / read / update flows. |
| `tasks` | Async task orchestration; symlinks to shared `source_files/`. |
| `widgets` | Widget configuration examples. |

`ThemeConfig` fields worth knowing (`tutorial_setup/_config.py`):

| Field | Purpose |
|-------|---------|
| `name`, `alias` | Folder + theme module name; display name in the catalog / map. |
| `depends_on` | Other themes to set up first. |
| `folders` | Subfolders created under `<theme>/`. Defaults to `("scripts", "data", "results")`. |
| `mirror_source` | Path under `packages/evergis_tools/examples/` to mirror from. Defaults to the theme name; override when the examples directory is nested (e.g. `features` mirrors `layers/features/`). |
| `mirror_excludes` | Extra glob patterns appended to the default mirror excludes. |
| `map` | `MapConfig` for the companion map. `None` -> no map is published. |
| `symlinks` | Catalog symlinks under `<theme>/` pointing at resources outside the theme folder (e.g. shared `Sample data & maps/source_files`). |

---

## Catalog Layout

Each theme owns the same folder layout under `{username}/{PROJECT_PATH}/<theme>/` (`scripts/`, `data/`, `results/`), plus a companion map `evg_map_<theme>` and a symlink back to the theme folder visible inside the map's list of layers. This page describes the pipeline that materialises that layout.

`PROJECT_PATH` and `RESOURCE_PREFIX` come from the environment (`.env`, loaded once by `evergis_tools.Client`); defaults are `EverGIS Resources/python` and `evg`.

---

## Key Behaviors

**Idempotent re-runs.** Folders are created via `get_or_create_folder_by_path`. Seed layers are always recreated with `overwrite=True` (cascade-drop + recreate) on every run - `force` does not change this. Mirrored example files: without `--force`, each destination is resolved first and skipped on hit; with `--force`, `upload_file(..., rewrite=True)` overwrites the existing file. Companion maps are dropped and recreated on every run (avoids `patch_project` quirks).

**Layer naming.** Full system name is `{username}.{RESOURCE_PREFIX}_{short}` (built by `ThemePaths.layer_system_name`). `short` defaults to the module file stem - `themes/features/stations.py` -> `john_doe.evg_stations`. The runner's `_validate_short` enforces: non-empty, length <= `_SHORT_MAX_LEN = 27` (31-char EverGIS cap minus the 4-char `evg_` prefix), starts with a letter (`isalpha()`), every character is lowercase alphanumeric or underscore.

**Cross-theme uniqueness.** `build_registry` enforces `short` is globally unique across themes and does not collide with any name in `EXTERNAL_LAYERS`. Every `MapLayerRef.short` and every `LayerQuery.eql_refs[*]` target must resolve to a known layer (local or external) - a typo fails fast at registry build time with a list of valid keys.

**External layers.** Names listed in `tutorial_setup/_externals.py::EXTERNAL_LAYERS` (`overture_places`, `overture_districts`, ...) are **not** created here. They come from an external sample-data pipeline and sit under `{username}/EverGIS Resources/Sample data & maps/overture/`. The registry exists only so cross-references resolve and `apply_theme` can fail-fast on a typo.

**Companion maps.** When `ThemeConfig.map.publish` is True, the runner drops and recreates `{username}.{RESOURCE_PREFIX}_map_{theme}` (avoids `patch_project` quirks), renders `MapLayerRef` / `DataSourceSpec` into the EverGIS dashboard JSON, and adds a symlink from the map to the theme root folder so the catalog tree is reachable from the map's list of layers.

**Mirrored examples.** The runner mirrors `packages/evergis_tools/examples/<theme>/` into `<theme>/scripts/` so the same files users can `git clone` are also browseable in the catalog. When `tutorial_setup` is pip-installed without the surrounding monorepo checkout, the examples directory is not found and the mirror step is skipped - layers, folders, and maps are still created.

**EQL placeholders.** `LayerQuery.eql` is a template using `${name}` placeholders; `eql_refs` maps placeholder -> short name of another layer. The runner substitutes full system names at apply time so the EQL string itself never knows the owning username.

---

## See Also

- [[Catalog/Folders|Folders]] - low-level `get_or_create_folder_by_path` used to materialise the theme folder tree.
- [[Layers/Create|Layers Create]] - `create_layer_from_schema` / `create_query_layer` invoked by `apply_seed`.
- [[UseCases/UseCases|Use Cases]] - end-to-end demos that run against the layers provisioned here.
