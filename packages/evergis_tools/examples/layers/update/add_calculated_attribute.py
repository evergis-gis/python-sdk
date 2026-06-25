"""Add a calculated attribute to an existing layer.

A calculated attribute carries an EQL ``expression`` that the server
evaluates per feature and stores in the backing column. Use it for
derived values that should be queryable / indexable alongside the
source data (e.g. point density = population / area).

``CalculatedAttribute`` pre-fills ``attributeConfigurationType=Calculated``
and defaults ``columnName`` to ``attributeName`` - the current server
requires a physical column (a true compute-on-read mode is not exposed
by the API today).

The calculation below references ``population`` and ``area_km2`` -
run ``add_layer_attributes.py`` first to seed them on
``evg_sandbox_polygon``, otherwise the expression will be stored but
evaluate to NULL on every row.

Re-running is safe: an existing attribute is skipped.
"""

from evergis_tools import Client
from evergis_tools.attribute_types import CalculatedAttribute
from evergis_tools.layers import add_layer_attribute
from evergis_tools.layers.read import get_layer_configuration


SOURCE_LAYER_SHORT = "evg_sandbox_polygon"

DENSITY = CalculatedAttribute(
    attributeName="density",
    type="Double",
    alias="Population density",
    expression="population / NULLIF(area_km2, 0)",
    isEditable=False,
)


def _print_attrs(client, layer: str) -> None:
    cfg = get_layer_configuration(client, layer, log=False)
    for a in cfg.attributesConfiguration.attributes:
        kind = getattr(a, "attributeConfigurationType", None) or "Default"
        col = a.columnName or "-"
        expr = getattr(a, "expression", None) or "-"
        print(f"  - {a.attributeName:14s} kind={kind!s:10s} column={col:14s} expr={expr}")


with Client() as client:
    username = client.account.get_user_info().username
    layer = f"{username}.{SOURCE_LAYER_SHORT}"

    print(f"layer: {layer}")
    print("BEFORE:")
    _print_attrs(client, layer)

    try:
        add_layer_attribute(client, layer, DENSITY, log=False)
        print(f"  + {DENSITY.attributeName}")
    except ValueError:
        print(f"  = {DENSITY.attributeName} (already present)")

    print("\nAFTER:")
    _print_attrs(client, layer)
