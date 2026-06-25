# -*- coding: utf-8 -*-
"""Declarative config for tutorial themes.

A theme = one ``ThemeConfig`` + a list of ``Layer*`` declarations.
Heavy values (Mapbox styles, EQL templates, card / edit configurations)
live in shared registries (``_styles.STYLES``, ``_queries.QUERIES``,
...) and the layer just references them by key. That keeps each layer
declaration small and lets unrelated themes share the same visual /
query primitives.

Naming convention (single source of truth):

* every layer declares a ``short`` name, e.g. ``"features_stations"``;
* full system name is built once by ``ThemePaths.layer_system_name``:
  ``{username}.{RESOURCE_PREFIX}_{short}`` -> ``john_doe.evg_features_stations``;
* cross-theme references (in ``LayerQuery.eql_refs``, ``MapLayerRef.short``)
  reuse the same ``short`` - no theme parsing, no string magic.

Layers managed by an external pipeline (Overture seeds) are listed in
``_externals.EXTERNAL_LAYERS`` so cross-references resolve and
``apply_theme`` can fail-fast on a typo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal, Type

from pydantic import BaseModel, ConfigDict, Field


# --- EQL parameters ----------------------------------------------------------


@dataclass
class EqlParam:
    """Declarative EQL parameter: ``EqlParam("String")`` or
    ``EqlParam("Double", default=0.5)``. Runner converts to the
    ``declare_eql_parameter`` wire format at apply time.
    """

    type: str
    default: Any = None


# --- Layers ------------------------------------------------------------------


class LayerBase(BaseModel):
    """Common fields for every layer kind."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    short: str | None = Field(
        default=None,
        description='Short name (no owner / prefix). Builds the full '
                    'system name as ``{username}.{RESOURCE_PREFIX}_{short}``. '
                    'Defaults to the module file stem - set explicitly only '
                    'when the layer name must differ from the file name.',
    )
    alias: str = Field(..., description='Display name in the catalog.')
    client_style: dict | None = Field(None,
        description='Mapbox-GL-flavoured client style ``{"items": [...]}``. '
                    'Inline by default; extract to a shared module only when '
                    'two or more layers really share it.')
    card_configuration: dict | None = Field(None,
        description='Feature-card configuration (raw EverGIS JSON). Inline.')
    edit_configuration: dict | None = Field(None,
        description='Edit-form configuration (raw EverGIS JSON). Inline.')


class LayerSchema(LayerBase):
    """Physical layer created from a Pydantic schema."""

    kind: Literal["schema"] = "schema"
    schema_: Type[BaseModel] = Field(..., alias="schema",
        description='Pydantic class describing the attribute columns.')
    geometry_type: str | None = Field(None,
        description='"Point" / "Polygon" / "MultiPolygon" / ... '
                    'None -> table-only layer.')
    geometry_field: str | None = Field("geometry",
        description='Attribute name carrying geometry (ignored when '
                    '``geometry_type`` is None).')
    srid: int | None = 4326
    populate: Callable[..., Any] | None = Field(default=None, exclude=True,
        description='Optional ``fn(client, full_name) -> None`` to seed '
                    'fixture rows after the layer is created.')


class LayerQuery(LayerBase):
    """Virtual query layer (no physical table).

    The EQL template uses ``${name}`` placeholders for layer system
    names; ``eql_refs`` maps the placeholder to a short name of another
    layer (local or external). The runner resolves these at apply time
    so the EQL string itself never knows the owning username.
    """

    kind: Literal["query"] = "query"
    eql: str = Field(...,
        description='EQL template. ``${name}`` placeholders are resolved '
                    'via ``eql_refs`` to full system names.')
    eql_refs: dict[str, str] = Field(default_factory=dict,
        description='Map placeholder -> short name of another layer. '
                    'e.g. ``{"places": "overture_places"}``.')
    eql_parameters: dict[str, EqlParam] = Field(default_factory=dict)
    geometry_type: str | None = None
    geometry_attribute: str = "geometry"
    srid: int | None = 4326
    create_table: bool = False


Layer = LayerSchema | LayerQuery


# --- Map ---------------------------------------------------------------------


class MapLayerRef(BaseModel):
    """Reference to a layer in the theme's companion map."""

    short: str
    visible: bool = True
    selectable: bool = True
    parameters: dict[str, Any] | None = None


class DataSourceSpec(BaseModel):
    """Map data source - table-only layer feeding a dropdown / card."""

    name: str
    layer: str = Field(..., description='Short name of the source layer.')
    attribute_alias: str
    attribute_value: str
    type: str = "layer"


class MapDefaults(BaseModel):
    """Defaults shared across every theme's companion map.

    Override individual fields by passing them to ``MapConfig``
    (e.g. ``MapConfig(position=(10, 30), resolution=2)`` for a global
    view). Changing the basemap / theme once here updates every
    tutorial map.
    """

    position: tuple[float, float] = (37.6173, 55.7558)   # Moscow
    resolution: float = 11
    theme_name: str = "light"
    base_map_name: str = "OpenFreeMap_Liberty"
    expanded_layers: bool = True
    base_map_settings: dict = Field(default_factory=dict)


class MapConfig(MapDefaults):
    """Theme-specific map composition (inherits ``MapDefaults``)."""

    title: str | None = Field(None,
        description='Map title. Falls back to ``ThemeConfig.alias`` if unset.')
    layers: list[MapLayerRef] = Field(default_factory=list)
    data_sources: list[DataSourceSpec] = Field(default_factory=list)
    publish: bool = Field(True,
        description='Set False for themes that do not publish a map.')


# --- External symlink --------------------------------------------------------


class ExternalSymlink(BaseModel):
    """Catalog symlink pointing outside the theme folder.

    The symlink itself lives at ``<theme>/<name>``; the target is the
    catalog resource at ``target_path``. ``target_path`` is the full
    EverGIS path **without** owner prefix - the runner prepends the owner.
    By default the owner is the caller; set ``external=True`` when the
    target is shared sample data owned by ``SAMPLE_DATA_OWNER`` (e.g. the
    ``tasks`` theme exposing the shared source-files folder under edu).
    """

    name: str
    target_path: str = Field(...,
        description='Path of the target resource (no owner prefix).')
    external: bool = Field(
        default=False,
        description="Target is shared sample data under SAMPLE_DATA_OWNER, "
                    "not the caller's account.")


# --- Theme -------------------------------------------------------------------


class ThemeConfig(BaseModel):
    """Top-level declarative config for one tutorial theme.

    Layers are declared in a sibling module-level ``LAYERS = [...]``
    list and discovered by the runner via the theme module - keeping
    the layer collection out of ``ThemeConfig`` keeps the latter
    cheap to instantiate at import time.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(..., description='Folder + theme module name (e.g. "layers").')
    alias: str = Field(..., description='Display name shown in the catalog / map.')
    depends_on: list[str] = Field(default_factory=list,
        description='Other theme names that must be set up first.')
    folders: tuple[str, ...] = Field(default=("scripts", "data", "results"),
        description='Subfolders created under ``<theme>/`` on setup. '
                    'Override to drop the default ones (e.g. ``("scripts", "data")`` '
                    'for themes that never publish results) or to add sandbox subdirs '
                    'an example expects (catalog uses ``rename/folder_a`` etc.).')
    symlinks: list[ExternalSymlink] = Field(default_factory=list,
        description='Catalog symlinks under ``<theme>/`` pointing at resources '
                    'outside the theme folder (e.g. shared sample_data/source_files).')
    map: MapConfig | None = Field(None,
        description='Companion map. None -> no map published.')
    mirror_source: str | None = Field(default=None,
        description='Relative path under ``packages/evergis_tools/examples/`` to '
                    'mirror from. Defaults to the theme name; override when the '
                    'examples live in a different subdirectory (e.g. features mirrors '
                    'from ``layers/features/``).')
    mirror_excludes: tuple[str, ...] = Field(default=(),
        description='Extra glob patterns appended to ``DEFAULT_EXCLUDES`` '
                    'when mirroring ``examples/<theme>/`` into the catalog.')


__all__ = [
    "EqlParam",
    "LayerBase", "LayerSchema", "LayerQuery", "Layer",
    "MapLayerRef", "DataSourceSpec",
    "MapDefaults", "MapConfig",
    "ExternalSymlink",
    "ThemeConfig",
]
