"""Delete an attribute from an existing layer.

Symmetric to ``add_layer_attribute``: reads the layer's current
``attributesConfiguration``, drops the entry by name, and PATCH'es
the layer. The server drops the backing physical column on its own.

The seed sandbox polygon (``evg_sandbox_polygon``) starts with only
``gid`` + ``geometry``; this example adds a ``note`` attribute first
so the deletion has something to remove (so the script is safe to
re-run).
"""

from evergis_api.schemas import AttributeConfigurationDc

from evergis_tools import Client
from evergis_tools.layers import (
    add_layer_attribute,
    delete_layer_attribute,
)
from evergis_tools.layers.read import get_layer_configuration


SOURCE_LAYER_SHORT = "evg_sandbox_polygon"
ATTRIBUTE_NAME = "note"


def _names(cfg) -> list[str]:
    return [a.attributeName for a in cfg.attributesConfiguration.attributes]


with Client() as client:
    username = client.account.get_user_info().username
    source = f"{username}.{SOURCE_LAYER_SHORT}"

    # Make sure the attribute is present so the demo is idempotent.
    cfg = get_layer_configuration(client, source, log=False)
    if ATTRIBUTE_NAME not in _names(cfg):
        add_layer_attribute(
            client, source,
            AttributeConfigurationDc(
                attributeName=ATTRIBUTE_NAME, columnName=ATTRIBUTE_NAME,
                type="String", alias="Inspector note",
                isEditable=True,
            ),
            log=False,
        )
        cfg = get_layer_configuration(client, source, log=False)
        print(f"before: added {ATTRIBUTE_NAME!r} → {_names(cfg)}")
    else:
        print(f"before: {_names(cfg)}")

    delete_layer_attribute(client, source, ATTRIBUTE_NAME, log=False)

    cfg = get_layer_configuration(client, source, log=False)
    print(f"after:  {_names(cfg)}")
