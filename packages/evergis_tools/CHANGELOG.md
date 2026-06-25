# Changelog

All notable user-facing changes to `evergis_tools` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- `Client()` now reads a `.env` file out of the box: `python-dotenv` is a
  dependency of `evergis-tools`, so credentials placed in a `.env` are picked
  up automatically - you no longer need to install `python-dotenv` yourself.
- Docstrings, examples, and the knowledge base are now in English.

## [0.2.0] - 2026-06-22

Catalog v3 support, clearer errors (functions now raise meaningful
exceptions instead of returning `None` or a vague `ValueError`), and new
EQL helpers.

### Breaking changes

- **A missing resource now raises `ResourceNotFound`.** When a layer, folder,
  file, map, etc. does not exist, functions raise `ResourceNotFound` instead
  of `ValueError`. If your code does `except ValueError` to detect "not
  found", change it to `except ResourceNotFound`
  (`from evergis_tools import ResourceNotFound`). A real server problem (e.g.
  the server is unreachable) is no longer reported as "not found" - you get
  the actual error.
- **A failed task now raises `TaskFailedError`.** If an import / export /
  processing task fails on the server, the function raises `TaskFailedError`
  instead of returning a result that looked like success. To get the old
  behaviour and check the result yourself, pass `raise_on_failure=False`.
- **A name or alias that is already taken now raises `ResourceExists`.**
  Creating a layer, map, folder, file or role whose name or alias already
  exists raises `ResourceExists`, with a message telling you which name or
  alias is taken and in which folder. The same happens when the resource
  already exists and you did not pass `overwrite=True` (previously this was a
  plain `ValueError`).
- **Some attribute flags were removed by the server.** The server no longer
  accepts the `isNullable` / `isAutoincrement` / `isUnique` flags on layer
  attributes (the primary key is decided server-side now), nor `bandsValues`
  on a feature. Make sure you are working against an up-to-date server.

### Changed

- **Resource paths use `/`.** A resource is addressed as
  `owner/folder/name` (slashes all the way through). The older
  `owner:folder/...` form still works, but `/` is now the recommended way.
- **Bad geometry is no longer dropped silently.** A broken or unsupported
  shape now raises a clear error instead of being quietly skipped (which used
  to save a feature with no geometry at all). Likewise, if reprojecting to
  your requested coordinate system fails, you get an error instead of data
  silently returned in the wrong coordinate system.
- **`count_features` adds `WHERE` for you.** The filter you pass should be a
  full `WHERE ...` clause (the same as in `query_layer_to_gdf` and
  `delete_features_by_condition`); `count_features` now adds the leading
  `WHERE` if you forget it.
- **Checking whether a path exists is faster** - `exists()` no longer fetches
  the whole resource just to answer yes/no.

### Added

- **`eql_describe(query, client)`** - get the columns an EQL query returns
  (name, type, whether it is the geometry column) without fetching any rows.
  Available for both the sync and async clients.
- **`geometry_field="auto"`** in `eql_query_to_geodataframe` - the wrapper
  finds the geometry column for you when it may be called `geometry` or
  `geom`.
- **Error types you can catch**, all importable from `evergis_tools`:
  `ResourceExists`, `ResourceNotFound`, `ApiTransientError`, `TaskFailedError`,
  plus the helpers `is_conflict` / `is_not_found` / `is_transient`.
- **`raise_on_failure`** option on `run_task` (and `TaskWaitOptions`), on by
  default.

### Fixed

- CSV import no longer crashes when you pass coordinate columns
  (`source_coord_fields`) without an attribute mapping.
- Creating a folder at the top level of the catalog now works, and you get a
  clear error when a path points at something that is not a folder (instead of
  it being treated as "not found").
- Routing and Voronoi helpers no longer drop broken pieces without telling
  you.
- EWKT parsing errors now keep the original cause, making them easier to debug.

[Unreleased]: https://github.com/evergis-gis/python-sdk/compare/evergis_tools%2Fv0.2.0...main
[0.2.0]: https://github.com/evergis-gis/python-sdk/releases/tag/evergis_tools%2Fv0.2.0
