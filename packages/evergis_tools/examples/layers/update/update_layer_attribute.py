"""Update one attribute of an existing layer in place.

Demonstrates two use cases for ``update_layer_attribute``:

1. Cosmetic patch - read the current attribute, tweak fields, push back.
2. Type promotion - replace a Default attribute with a CalculatedAttribute
   that has an ``expression`` (server materialises values into the
   backing column).

The seed sandbox polygon (``evg_sandbox_polygon``) is reused. The
example first ensures a ``density`` attribute exists (Double, with
default settings), then runs both updates; the second run after a
reset will produce the same final state - operation is idempotent
on a fresh layer.
"""

from evergis_api.schemas import (
    AttributeConfigurationDc,
    AttributeFormatConfigurationDc,
)

from evergis_tools import Client
from evergis_tools.attribute_types import CalculatedAttribute
from evergis_tools.layers import (
    add_layer_attribute,
    update_layer_attribute,
)
from evergis_tools.layers.read import get_layer_configuration


SOURCE_LAYER_SHORT = "evg_sandbox_polygon"
ATTR = "density"


def _print(client, layer: str, label: str) -> None:
    cfg = get_layer_configuration(client, layer, log=False)
    for a in cfg.attributesConfiguration.attributes:
        if a.attributeName == ATTR:
            kind = getattr(a, "attributeConfigurationType", None) or "Default"
            expr = getattr(a, "expression", None) or "-"
            fmt = getattr(a, "stringFormat", None)
            print(f"  {label}: kind={kind!s:11s} alias={a.alias!r:25s} "
                  f"expr={expr!r}  fmt={fmt!r}")


with Client() as client:
    username = client.account.get_user_info().username
    layer = f"{username}.{SOURCE_LAYER_SHORT}"

    # Ensure the attribute exists (Default Double, no expression).
    cfg = get_layer_configuration(client, layer, log=False)
    if not any(a.attributeName == ATTR for a in cfg.attributesConfiguration.attributes):
        add_layer_attribute(client, layer, AttributeConfigurationDc(
            attributeName=ATTR, columnName=ATTR, type="Double",
            alias=ATTR, isEditable=True,
        ), log=False)
    _print(client, layer, "start  ")

    # --- 1) cosmetic patch - change alias + stringFormat only ---
    cfg = get_layer_configuration(client, layer, log=False)
    attr = next(a for a in cfg.attributesConfiguration.attributes
                if a.attributeName == ATTR)
    attr.alias = "Population density"
    attr.stringFormat = AttributeFormatConfigurationDc(format="#,#.00")
    update_layer_attribute(client, layer, attr, log=False)
    _print(client, layer, "patched")

    # --- 2) promote Default → Calculated ---
    update_layer_attribute(client, layer, CalculatedAttribute(
        attributeName=ATTR,
        columnName=ATTR,
        type="Double",
        alias="Population density",
        expression="population / NULLIF(area_km2, 0)",
        isEditable=False,
    ), log=False)
    _print(client, layer, "calc   ")
