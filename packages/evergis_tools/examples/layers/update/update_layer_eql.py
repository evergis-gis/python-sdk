"""Update the EQL query and parameters of an existing virtual layer.

The seed layer ``evg_places_update_layer`` (see
``themes/layers.py::_seed_places_update_layer``) starts as a plain
``SELECT * FROM places`` - no joins, no parameters. This example
enriches it in two steps:

* Step 1: add two parameters (``@category``, ``@min_conf``) with
  ``${isset:}`` blocks so callers can filter on read.
* Step 2: rewrite the EQL as a JOIN with ``evg_overture_districts``
  and add a third parameter ``@district`` (default 'Тверской район',
  the Tverskoy district).

Two important details:

* ``update_layer_eql`` **replaces** the full parameter dict each call -
  re-send the parameters you want to keep, otherwise they disappear.
* It touches **only** the EQL + parameters; the layer's
  ``attributesConfiguration.attributes`` is not re-synced. If your new
  EQL projects a new column, expose it via :func:`add_layer_attribute`
  so the layer schema and the new EQL agree.

To reset the layer, run::

    .venv/bin/python -m evergis_tutorial_setup themes layers --force
"""

import os

from evergis_tools import Client
from evergis_tools.layers import (
    declare_eql_parameter,
    get_layer_configuration,
    update_layer_eql,
)


SOURCE_LAYER_SHORT = "evg_places_update_layer"
SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")

# EQL templates - ``__S__`` is swapped for SAMPLE_DATA_OWNER at runtime
# (the shared Overture layers are read-only sample data). Built via
# str.replace so the EverGIS ``${isset:@x, { ... }}`` blocks are
# readable as-is (no Python f-string ``{{`` / ``}}`` escapes).
EQL_WITH_PARAMS = """
SELECT
    p.gid,
    p.name,
    p.category,
    p.confidence,
    p.geom
FROM __S__.evg_overture_places AS p
WHERE TRUE
${isset:@category, { AND p.category    = @category }}
${isset:@min_conf, { AND p.confidence >= @min_conf }}
"""

EQL_WITH_JOIN = """
SELECT
    p.gid,
    p.name,
    p.category,
    p.confidence,
    p.geom
FROM __S__.evg_overture_places    AS p
JOIN __S__.evg_overture_districts AS d ON ST_Within(p.geom, d.geom)
WHERE d.name = @district
${isset:@category, { AND p.category    = @category }}
${isset:@min_conf, { AND p.confidence >= @min_conf }}
"""


def _summary(cfg) -> str:
    params = list((cfg.eqlParameters or {}).keys())
    return f"eql={len(cfg.eql)} chars, params={params}"


with Client() as client:
    username = client.account.get_user_info().username
    layer = f"{username}.{SOURCE_LAYER_SHORT}"

    print(f"layer: {layer}\n")
    print(f"BEFORE:\n  {_summary(get_layer_configuration(client, layer, log=False))}")

    # Step 1 - add two optional parameters with ${isset:} blocks.
    update_layer_eql(
        client, layer,
        eql_query=EQL_WITH_PARAMS.replace("__S__", SAMPLE_DATA_OWNER),
        eql_parameters={
            "@category": declare_eql_parameter("String", default="restaurant"),
            "@min_conf": declare_eql_parameter("Double"),
        },
        log=False,
    )
    print(
        f"\nAFTER step 1 (added @category default='restaurant', @min_conf):"
        f"\n  {_summary(get_layer_configuration(client, layer, log=False))}"
    )

    # Step 2 - add JOIN with districts + a required @district parameter.
    update_layer_eql(
        client, layer,
        eql_query=EQL_WITH_JOIN.replace("__S__", SAMPLE_DATA_OWNER),
        eql_parameters={
            "@district": declare_eql_parameter("String", default="Тверской район"),
            "@category": declare_eql_parameter("String", default="restaurant"),
            "@min_conf": declare_eql_parameter("Double"),
        },
        log=False,
    )
    print(
        f"\nAFTER step 2 (JOIN districts, added @district):"
        f"\n  {_summary(get_layer_configuration(client, layer, log=False))}"
    )
