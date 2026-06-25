# EverGIS Python

Python client and high-level tooling for the EverGIS geospatial platform.

## Packages

| Package | What it is |
|---------|-----------|
| `evergis_api` | Low-level client generated from the OpenAPI/swagger spec (sync + async). |
| `evergis_tools` | High-level utilities: catalog, tasks, EQL -> (Geo)DataFrame, geometry, GeoPandas. |
| `evergis_tutorial_setup` | Provisions the tutorial workspace (seed layers, maps, mirrored example scripts) that the examples read from. Optional. |

Dependency flow: `evergis_tutorial_setup -> evergis_tools -> evergis_api`.

## Install

`evergis-tools` depends on `evergis-api`; neither is on a package index yet, so
install both from git in a single command (pip resolves them together):

```bash
pip install \
  "git+https://github.com/evergis-gis/python-sdk.git#subdirectory=packages/evergis_api" \
  "git+https://github.com/evergis-gis/python-sdk.git#subdirectory=packages/evergis_tools"
```

Add `evergis-tutorial-setup` only if you want to provision the tutorial workspace:

```bash
pip install \
  "git+https://github.com/evergis-gis/python-sdk.git#subdirectory=packages/evergis_tutorial_setup"
```

Editable, for development (from a checkout, inside a virtualenv):

```bash
uv pip install -e packages/evergis_api      # not on an index - install first
uv pip install -e packages/evergis_tools
uv pip install -e packages/evergis_tutorial_setup   # optional
```

## Quick start

```python
from evergis_tools import Client          # reads EVERGIS_HOST / EVERGIS_SB_TOKEN

with Client() as client:
    ...
```

## Documentation

- **API reference (KB)** - `packages/evergis_tools/docs/kb/`
- **Examples** - `packages/evergis_tools/examples/`
- **Cookbook** - `packages/evergis_tools/docs/cookbook/`
- **Changelog** - `packages/evergis_tools/CHANGELOG.md`

## Development

```bash
pip install -e packages/evergis_api -e packages/evergis_tools
pytest packages/evergis_api packages/evergis_tools   # integration tests self-skip without EVERGIS_*
ruff check packages/
```

## License

[Apache License 2.0](LICENSE). Copyright 2026 Everpoint.
