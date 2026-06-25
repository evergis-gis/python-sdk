# -*- coding: utf-8 -*-
"""Universal runner: discovers themes from the filesystem, validates
cross-references, then provisions folders / seed layers / mirrored
example scripts / companion maps for each requested theme.

Theme modules contain only declarations (``THEME`` + per-layer
``LAYER`` constants + optional ``populate`` callables). All
imperative logic - folder creation, layer publishing, mirroring,
map rendering, ANSI output - lives here.

Adding behaviour for a single theme means either a new field on
``LayerSchema``/``LayerQuery``/``ThemeConfig`` plus the runner
branch that handles it (universal), or deciding the requirement
isn't universal and reshaping the theme.
"""

from __future__ import annotations

import fnmatch
import importlib
import pkgutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

from evergis_api.schemas import CreateSymlinkDc
from evergis_tools import Client
from evergis_tools._errors import ResourceNotFound, is_conflict
from evergis_tools.catalog.files import upload_file
from evergis_tools.catalog.folders import get_or_create_folder_by_path
from evergis_tools.catalog.maps import create_map
from evergis_tools.catalog.resources import delete_resource, resolve_resource
from evergis_tools.layers import (
    create_layer_from_schema,
    create_query_layer,
    declare_eql_parameter,
)

from ._config import (
    Layer, LayerSchema, LayerQuery, ThemeConfig,
)
from ._externals import EXTERNAL_LAYERS
from ._paths import ThemePaths, resource_prefix, sample_data_owner


# ---------------------------------------------------------------------------
# ANSI output
# ---------------------------------------------------------------------------

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
DIM    = "\033[2m"
RESET  = "\033[0m"


# ---------------------------------------------------------------------------
# Validation rules for short names
# ---------------------------------------------------------------------------

_SHORT_MAX_LEN = 27   # 31 (EverGIS limit) - len("evg_") prefix
_DEFAULT_MIRROR_EXCLUDES = ("__pycache__", "*.pyc", ".DS_Store", "*.egg-info")


def _validate_short(short: str) -> None:
    if not short:
        raise ValueError("layer short name is empty")
    if len(short) > _SHORT_MAX_LEN:
        raise ValueError(
            f"layer short {short!r} is {len(short)} chars; EverGIS caps the "
            f"system name at 31 (= {_SHORT_MAX_LEN} after the {resource_prefix()!r} prefix)"
        )
    if not short[0].isalpha():
        raise ValueError(f"layer short {short!r} must start with a letter")
    for ch in short:
        if not (ch.isalnum() or ch == "_") or (ch.isalpha() and not ch.islower()):
            raise ValueError(
                f"layer short {short!r} must be lowercase alphanumeric + underscores"
            )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

@dataclass
class LayerEntry:
    """Resolved layer entry in the global registry."""

    layer: Layer
    short: str        # resolved from LAYER.short or module file stem
    theme: str        # owning theme name
    module_name: str


@dataclass
class ThemeEntry:
    """Resolved theme entry: declaration + its owned layers."""

    theme: ThemeConfig
    layers: list[LayerEntry] = field(default_factory=list)


def discover_themes() -> dict[str, ThemeEntry]:
    """Walk ``evergis_tutorial_setup.themes.*`` and collect every
    ``THEME`` constant + sibling ``LAYER`` declarations.

    Returns ``{theme_name: ThemeEntry}`` ordered by import discovery.
    Modules without a ``THEME`` constant are silently skipped (helper
    modules like ``stations_data.py``).
    """
    import evergis_tutorial_setup.themes as themes_pkg

    result: dict[str, ThemeEntry] = {}
    for finder, sub_name, is_pkg in pkgutil.iter_modules(themes_pkg.__path__):
        if not is_pkg:
            continue
        pkg = importlib.import_module(f"{themes_pkg.__name__}.{sub_name}")
        theme = getattr(pkg, "THEME", None)
        if theme is None:
            continue   # subpackage without THEME -> skip
        if not isinstance(theme, ThemeConfig):
            raise TypeError(
                f"{pkg.__name__}.THEME must be ThemeConfig, got {type(theme).__name__}"
            )

        entry = ThemeEntry(theme=theme)
        # Collect LAYER constants from sibling modules.
        for _, mod_name, sub_is_pkg in pkgutil.iter_modules(pkg.__path__):
            if sub_is_pkg:
                continue
            mod_full = f"{pkg.__name__}.{mod_name}"
            mod = importlib.import_module(mod_full)
            layer = getattr(mod, "LAYER", None)
            if layer is None:
                continue
            if not isinstance(layer, (LayerSchema, LayerQuery)):
                raise TypeError(
                    f"{mod_full}.LAYER must be LayerSchema or LayerQuery, "
                    f"got {type(layer).__name__}"
                )
            short = layer.short or Path(mod.__file__).stem
            _validate_short(short)
            entry.layers.append(LayerEntry(
                layer=layer, short=short, theme=theme.name, module_name=mod_full,
            ))
        result[theme.name] = entry
    return result


def build_registry(themes: dict[str, ThemeEntry]) -> dict[str, LayerEntry]:
    """Build ``{short: LayerEntry}`` union and validate cross-references.

    Checks:
    * ``short`` uniqueness across all themes;
    * no overlap with ``EXTERNAL_LAYERS``;
    * every ``MapLayerRef.short`` resolves to a known layer (local or external);
    * every ``LayerQuery.eql_refs[*]`` resolves to a known layer.
    """
    registry: dict[str, LayerEntry] = {}
    for entry in themes.values():
        for le in entry.layers:
            if le.short in registry:
                other = registry[le.short]
                raise RuntimeError(
                    f"duplicate layer short {le.short!r}: declared in "
                    f"{other.module_name!r} and {le.module_name!r}"
                )
            if le.short in EXTERNAL_LAYERS:
                raise RuntimeError(
                    f"local layer short {le.short!r} ({le.module_name}) shadows "
                    f"an external layer of the same name"
                )
            registry[le.short] = le

    known = set(registry) | set(EXTERNAL_LAYERS)
    for entry in themes.values():
        for le in entry.layers:
            if isinstance(le.layer, LayerQuery):
                for placeholder, target in le.layer.eql_refs.items():
                    if target not in known:
                        raise RuntimeError(
                            f"{le.module_name}: eql_refs[{placeholder!r}] -> "
                            f"{target!r} is not a known layer"
                        )
        if entry.theme.map:
            for ref in entry.theme.map.layers:
                if ref.short not in known:
                    raise RuntimeError(
                        f"theme {entry.theme.name!r}: map layer ref "
                        f"{ref.short!r} is not a known layer"
                    )
            for ds in entry.theme.map.data_sources:
                if ds.layer not in known:
                    raise RuntimeError(
                        f"theme {entry.theme.name!r}: data_source layer ref "
                        f"{ds.layer!r} is not a known layer"
                    )
    return registry


# ---------------------------------------------------------------------------
# Selection / topological ordering
# ---------------------------------------------------------------------------

def _resolve_selection(
    requested: Sequence[str],
    themes: dict[str, ThemeEntry],
) -> list[str]:
    """Expand 'all', pull in transitive ``depends_on``, topo-sort."""
    if list(requested) == ["all"]:
        selected = set(themes)
    else:
        unknown = set(requested) - set(themes)
        if unknown:
            raise ValueError(
                f"unknown theme(s): {sorted(unknown)}. Known: {sorted(themes)}"
            )
        selected = set(requested)

    # Transitive closure over depends_on.
    queue = list(selected)
    while queue:
        name = queue.pop()
        for dep in themes[name].theme.depends_on:
            if dep not in themes:
                raise RuntimeError(
                    f"theme {name!r} depends on unknown theme {dep!r}"
                )
            if dep not in selected:
                selected.add(dep)
                queue.append(dep)

    # Kahn topo-sort on selected subset.
    indeg = {n: 0 for n in selected}
    edges: dict[str, list[str]] = {n: [] for n in selected}
    for n in selected:
        for dep in themes[n].theme.depends_on:
            edges[dep].append(n)
            indeg[n] += 1
    ready = [n for n, d in indeg.items() if d == 0]
    ordered: list[str] = []
    while ready:
        ready.sort()   # deterministic
        n = ready.pop(0)
        ordered.append(n)
        for m in edges[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                ready.append(m)
    if len(ordered) != len(selected):
        raise RuntimeError("dependency cycle in tutorial themes")
    return ordered


# ---------------------------------------------------------------------------
# Folders / mirror / map publish helpers (formerly in _common.py)
# ---------------------------------------------------------------------------

def _ensure_folder(client: Client, full_path: str) -> str:
    return get_or_create_folder_by_path(client=client, path=full_path).resourceId


def _ensure_folder_tree(client: Client, base: str, subpaths: Iterable[str]) -> None:
    _ensure_folder(client, base)
    for sub in subpaths:
        _ensure_folder(client, f"{base}/{sub}")


def _is_excluded(rel_posix: str, patterns: Sequence[str]) -> bool:
    segments = rel_posix.split("/")
    for pat in patterns:
        if "/" in pat:
            if fnmatch.fnmatch(rel_posix, pat):
                return True
            if any(
                fnmatch.fnmatch("/".join(segments[: i + 1]), pat)
                for i in range(len(segments))
            ):
                return True
        else:
            if any(fnmatch.fnmatch(seg, pat) for seg in segments):
                return True
    return False


def _find_examples_root() -> Path | None:
    """Locate ``packages/evergis_tools/examples/`` relative to this file.

    Returns None when running from a wheel without the surrounding repo
    (prod case) - mirror_examples then logs a notice and skips.
    """
    here = Path(__file__).resolve()
    # evergis_tutorial_setup/evergis_tutorial_setup/_runner.py
    #   -> parents[2] == packages/  -> sibling evergis_tools/examples
    candidate = here.parents[2] / "evergis_tools" / "examples"
    return candidate if candidate.exists() else None


def mirror_examples(
    client: Client,
    theme: ThemeConfig,
    paths: ThemePaths,
    *,
    force: bool,
) -> None:
    """Mirror ``examples/<source>/`` into ``<theme>/scripts/`` in EverGIS.

    ``source`` defaults to the theme name; set ``ThemeConfig.mirror_source``
    when examples live in a different subdirectory (e.g. ``layers/features``).
    """
    root = _find_examples_root()
    if root is None:
        print(f"  {DIM}-{RESET} examples directory not found; mirror skipped "
              f"(prod-install, no repo checkout)")
        return
    source = theme.mirror_source or theme.name
    local_dir = root / source
    if not local_dir.exists():
        print(f"  {DIM}-{RESET} no examples/{source}/ directory; nothing to mirror")
        return

    excludes = (*_DEFAULT_MIRROR_EXCLUDES, *theme.mirror_excludes)
    uploaded = skipped = 0
    for path in sorted(local_dir.rglob("*")):
        if not path.is_file():
            continue
        rel_posix = path.relative_to(local_dir).as_posix()
        if _is_excluded(rel_posix, excludes):
            continue
        rel_parent = "/".join(rel_posix.split("/")[:-1])
        dest_dir = f"{paths.scripts}/{rel_parent}".rstrip("/")
        dest_resource = f"{dest_dir}/{path.name}"

        if not force:
            try:
                resolve_resource(client, dest_resource)
                skipped += 1
                continue
            except ResourceNotFound:
                pass  # not uploaded yet - proceed; other errors propagate

        _ensure_folder(client, dest_dir)
        try:
            upload_file(client=client, file_path=path, parent_path=dest_dir, rewrite=force)
            uploaded += 1
            print(f"  {GREEN}+{RESET} {rel_posix}")
        except Exception as exc:
            print(f"  {RED}x{RESET} {rel_posix}: {exc}")
    print(f"  {DIM}={RESET} mirror: {uploaded} uploaded, {skipped} skipped")


def _publish_map(
    client: Client,
    *,
    name: str,
    parent_path: str,
    alias: str,
    dashboard: dict,
    description: str | None = None,
    tags: list[str] | None = None,
) -> Any:
    """Drop-and-recreate the map: delete it (if present) then create fresh.

    Idempotent - re-running gives the same result. Recreating is more
    reliable here than patching an existing project in place.
    """
    delete_resource(client, name, missing_ok=True, cascade=True)
    return create_map(
        client=client, name=name,
        alias=alias, description=description, tags=tags,
        parent_path=parent_path,
        dashboard_configuration=dashboard,
    )


def _link_folder_into_map(
    client: Client, *, folder_path: str, map_name: str, link_name: str | None = None,
) -> None:
    try:
        folder = resolve_resource(client, folder_path)
    except Exception as e:
        raise SystemExit(f"folder {folder_path!r} not found: {e}")
    map_info = client.projects.get_project_info(map_name)
    body = CreateSymlinkDc(
        name=link_name or folder_path.rstrip("/").split("/")[-1],
        targetResourceId=folder.resourceId,
        parentId=map_info.resourceId,
    )
    try:
        client.catalog.post_link(body=body)
    except Exception as exc:
        if not is_conflict(exc):
            raise


def _apply_symlinks(
    client: Client, theme: ThemeConfig, paths: ThemePaths, username: str,
) -> None:
    """Create ``ExternalSymlink`` entries under the theme root.

    Idempotent: 409 ``ResourceExists`` from the server is swallowed.
    """
    if not theme.symlinks:
        return
    parent = resolve_resource(client, paths.root)
    for link in theme.symlinks:
        # Shared sample-data targets live under SAMPLE_DATA_OWNER (edu),
        # the caller's own resources under their username.
        owner = sample_data_owner() if link.external else username
        try:
            tgt = resolve_resource(client, f"{owner}/{link.target_path}")
        except Exception as e:
            print(f"  {RED}x{RESET} symlink target {link.target_path!r} not found: {e}")
            continue
        body = CreateSymlinkDc(
            name=link.name,
            targetResourceId=tgt.resourceId,
            parentId=parent.resourceId,
        )
        try:
            client.catalog.post_link(body=body)
            print(f"  {GREEN}+{RESET} symlink {link.name} -> {link.target_path}")
        except Exception as exc:
            if is_conflict(exc):
                print(f"  {DIM}={RESET} symlink {link.name} already in place")
            else:
                raise


# ---------------------------------------------------------------------------
# Apply: seeds + dashboard + theme orchestration
# ---------------------------------------------------------------------------

def _resolve_eql(layer: LayerQuery, paths: ThemePaths,
                 registry: dict[str, LayerEntry]) -> str:
    """Substitute ``${name}`` placeholders with full system names."""
    eql = layer.eql
    for placeholder, target_short in layer.eql_refs.items():
        full = paths.layer_system_name(
            target_short, external=target_short in EXTERNAL_LAYERS)
        eql = eql.replace("${" + placeholder + "}", full)
    return eql


def _resolve_eql_parameters(layer: LayerQuery) -> dict[str, Any] | None:
    if not layer.eql_parameters:
        return None
    out: dict[str, Any] = {}
    for name, param in layer.eql_parameters.items():
        out[name] = declare_eql_parameter(param.type, default=param.default)
    return out


def apply_seed(
    client: Client,
    entry: LayerEntry,
    paths: ThemePaths,
    *,
    registry: dict[str, LayerEntry],
    force: bool,
) -> None:
    """Create one seed layer + optional populate. ``force`` is implicit
    (the runner always uses ``overwrite=True`` so reruns are idempotent)."""
    full_name = paths.layer_system_name(entry.short)
    layer = entry.layer

    # Cascade-drop any existing seed first. ``overwrite=True`` on the
    # create calls below does not drop the backing table, so an orphan
    # survives and the server rejects the recreate with
    # "table already exist". delete_resource(cascade=True) drops both the
    # layer and its table; missing_ok makes the first run a no-op.
    delete_resource(client, full_name, missing_ok=True)

    if isinstance(layer, LayerSchema):
        create_layer_from_schema(
            client=client,
            schema=layer.schema_,
            layer_name=full_name,
            layer_alias=layer.alias,
            parent_path=paths.data,
            geometry_field=layer.geometry_field if layer.geometry_type else None,
            geometry_type=layer.geometry_type,
            srid=layer.srid if layer.geometry_type else None,
            client_style=layer.client_style,
            card_configuration=layer.card_configuration,
            edit_configuration=layer.edit_configuration,
            overwrite=True, log=False,
        )
        print(f"  {GREEN}+{RESET} {full_name}  ({layer.geometry_type or 'table'})")
        if layer.populate is not None:
            layer.populate(client, full_name)
            print(f"    {DIM}-> populated{RESET}")
    else:  # LayerQuery
        create_query_layer(
            client=client,
            layer_name=full_name,
            eql_query=_resolve_eql(layer, paths, registry),
            layer_alias=layer.alias,
            parent_path=paths.data,
            geometry_type=layer.geometry_type,
            srid=layer.srid,
            geometry_attribute=layer.geometry_attribute,
            create_table=layer.create_table,
            overwrite=True, log=False,
            client_style=layer.client_style,
            card_configuration=layer.card_configuration,
            edit_configuration=layer.edit_configuration,
            eql_parameters=_resolve_eql_parameters(layer),
        )
        params = ", ".join(layer.eql_parameters) if layer.eql_parameters else "no params"
        print(f"  {GREEN}+{RESET} {full_name}  (query, {params})")


def build_dashboard(
    theme_entry: ThemeEntry,
    registry: dict[str, LayerEntry],
    username: str,
) -> dict[str, Any]:
    """Render ``ThemeConfig.map`` into the EverGIS dashboard JSON."""
    theme = theme_entry.theme
    assert theme.map is not None, "build_dashboard called for a theme without a map"
    m = theme.map
    rp = resource_prefix()

    def full(short: str) -> str:
        # External layers (shared sample data) live under SAMPLE_DATA_OWNER;
        # the theme's own seeds under the caller's username.
        owner = sample_data_owner() if short in EXTERNAL_LAYERS else username
        return f"{owner}.{rp}_{short}"

    layers_json = []
    for ref in m.layers:
        entry = {
            "name": full(ref.short),
            "isVisible": ref.visible,
            "selectable": ref.selectable,
        }
        if ref.parameters:
            entry["parameters"] = ref.parameters
        layers_json.append(entry)

    data_sources_json = [
        {
            "name": ds.name,
            "layerName": full(ds.layer),
            "type": ds.type,
            "attributeAlias": ds.attribute_alias,
            "attributeValue": ds.attribute_value,
        }
        for ds in m.data_sources
    ]

    page = {
        "id": "page1",
        "style": {},
        "tasks": [],
        "layers": layers_json,
        "filters": [],
        "options": {
            "title": m.title or theme.alias,
            "position": list(m.position),
            "resolution": m.resolution,
            "themeName": m.theme_name,
            "baseMapName": m.base_map_name,
            "expandedLayers": m.expanded_layers,
            "baseMapSettings": m.base_map_settings,
        },
        "children": [],
        "dataSources": data_sources_json,
        "templateName": "ContainersGroup",
    }

    return {
        "filters": [],
        "options": {},
        "children": [{
            "id": "pages", "style": {}, "options": {},
            "children": [page], "templateName": "Pages",
        }],
        "dataSources": data_sources_json,
    }


def apply_theme(
    client: Client,
    theme_entry: ThemeEntry,
    *,
    registry: dict[str, LayerEntry],
    force: bool,
) -> None:
    """End-to-end provision of one theme: folders -> seeds -> mirror -> map -> symlink."""
    theme = theme_entry.theme
    username = client.account.get_user_info().username
    paths = ThemePaths(username=username, theme_name=theme.name)

    print(f"{YELLOW}=== theme {theme.name!r}: folders ==={RESET}")
    _ensure_folder_tree(client, paths.root, theme.folders)

    if theme_entry.layers:
        print(f"{YELLOW}=== theme {theme.name!r}: seed layers ==={RESET}")
        for le in theme_entry.layers:
            apply_seed(client, le, paths, registry=registry, force=force)

    print(f"{YELLOW}=== theme {theme.name!r}: mirror examples ==={RESET}")
    mirror_examples(client, theme, paths, force=force)

    if theme.symlinks:
        print(f"{YELLOW}=== theme {theme.name!r}: external symlinks ==={RESET}")
        _apply_symlinks(client, theme, paths, username)

    if theme.map and theme.map.publish:
        print(f"{YELLOW}=== theme {theme.name!r}: map ==={RESET}")
        map_name = f"{username}.{resource_prefix()}_map_{theme.name}"
        dashboard = build_dashboard(theme_entry, registry, username)
        _publish_map(
            client,
            name=map_name, parent_path=paths.root,
            alias=f"map - {theme.name}",
            description=f"Companion map for the '{theme.name}' tutorial theme.",
            tags=["tutorial", theme.name],
            dashboard=dashboard,
        )
        _link_folder_into_map(client, folder_path=paths.root, map_name=map_name,
                              link_name=theme.name)
        print(f"  {GREEN}+{RESET} {map_name}")

    print(f"{GREEN}OK{RESET} theme {theme.name!r} ready")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def setup(
    themes: Sequence[str],
    *,
    force: bool = False,
    client: Client | None = None,
) -> None:
    """Provision the requested tutorial themes in EverGIS.

    This is the programmatic entry point - use it (not the ``python -m``
    CLI) inside the EverGIS ``python-script-runner`` sandbox, which runs
    Python only. Example-script mirroring needs a monorepo checkout, so
    in the sandbox that step is skipped; layers, folders and maps are
    still created.

    Args:
        themes: List of theme names, e.g. ``["features"]`` or ``["all"]``.
            Pass a list even for one theme - a bare string would iterate
            character by character. Dependencies (``depends_on``) are
            pulled in transitively and applied first.
        force: When True, seed layers are dropped + recreated and mirrored
            files overwritten.
        client: Optional pre-constructed ``Client``. When omitted, a fresh
            ``Client()`` is opened and closed by this call.
    """
    discovered = discover_themes()
    if not discovered:
        print(f"{YELLOW}no themes discovered under "
              f"evergis_tutorial_setup.themes{RESET}")
        return

    registry = build_registry(discovered)
    print(f"{DIM}registry: {len(registry)} layers across "
          f"{len(discovered)} themes{RESET}")

    selected = _resolve_selection(themes, discovered)
    print(f"{DIM}apply order: {selected}{RESET}\n")

    owns_client = client is None
    if owns_client:
        client = Client()
    try:
        for name in selected:
            apply_theme(client, discovered[name], registry=registry, force=force)
            print()
    finally:
        if owns_client:
            client.close()


__all__ = [
    "setup",
    "discover_themes", "build_registry",
    "apply_theme", "apply_seed", "build_dashboard", "mirror_examples",
    "LayerEntry", "ThemeEntry",
    "GREEN", "YELLOW", "RED", "DIM", "RESET",
]
