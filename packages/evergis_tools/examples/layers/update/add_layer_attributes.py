"""Add attributes of every supported type to an existing layer.

The seed sandbox polygon (``evg_sandbox_polygon``, see
``themes/layers.py::_seed_sandbox_polygon``) starts with only ``gid``
+ ``geometry``. ``add_layer_attribute`` appends one column at a time -
the server creates the backing physical column on its own from the
PATCH /layers call, no second ``PATCH /tables`` is needed.

Re-run resets the sandbox (drops the layer in python -m evergis_tutorial_setup themes layers
--force, then re-creates it empty).
"""

from evergis_api.schemas import AttributeConfigurationDc

from evergis_tools import Client
from evergis_tools.attribute_types import AttachmentsAttribute
from evergis_tools.layers import add_layer_attribute
from evergis_tools.layers.read import get_layer_configuration


SOURCE_LAYER_SHORT = "evg_sandbox_polygon"


def _attr(name: str, type_: str, alias: str) -> AttributeConfigurationDc:
    return AttributeConfigurationDc(
        attributeName=name, columnName=name, type=type_,
        alias=alias, isEditable=True,
    )


# One example per supported AttributeType. ``AttachmentsAttribute`` is
# the only entry that needs its own class - its ``subType`` flag is
# what tells the UI to render the file-list widget.
ATTRIBUTES = [
    _attr("name",          "String",   "Display name"),
    _attr("population",    "Int64",    "Population"),
    _attr("area_km2",      "Double",   "Area, sq.km"),
    _attr("is_protected",  "Boolean",  "Protected zone"),
    _attr("surveyed_at",   "DateTime", "Last survey"),
    _attr("meta",          "Json",     "Free-form metadata"),
    AttachmentsAttribute(attributeName="docs", alias="Documents"),
]


with Client() as client:
    username = client.account.get_user_info().username
    layer = f"{username}.{SOURCE_LAYER_SHORT}"

    print(f"layer: {layer}")
    print("BEFORE:")
    for a in get_layer_configuration(client, layer, log=False).attributesConfiguration.attributes:
        print(f"  - {a.attributeName:14s} {a.type}")

    for attr in ATTRIBUTES:
        try:
            add_layer_attribute(client, layer, attr, log=False)
            print(f"  + {attr.attributeName}")
        except ValueError:
            print(f"  = {attr.attributeName} (already present)")

    print("\nAFTER:")
    for a in get_layer_configuration(client, layer, log=False).attributesConfiguration.attributes:
        sub = getattr(a, "subType", None)
        sub_label = f"  subType={sub!r}" if sub else ""
        print(f"  - {a.attributeName:14s} {a.type!s:10s}{sub_label}")
