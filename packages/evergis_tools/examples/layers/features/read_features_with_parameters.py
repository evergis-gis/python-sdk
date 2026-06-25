"""Read features using EQL parameters declared at the layer level.

Source: ``{username}.evg_places_qry`` - a thin **virtual** wrapper over
``{SAMPLE_DATA_OWNER}.evg_overture_places`` provisioned by the ``shared`` tutorial theme
(``evergis_tutorial_setup.themes.shared``). The wrapper exposes
three optional parameters via the EverGIS conditional expansion::

    SELECT * FROM <overture_places>
    WHERE TRUE
    ${isset:@category,  { AND category = @category }}
    ${isset:@min_conf,  { AND confidence >= @min_conf }}
    ${isset:@name_like, { AND name LIKE concat('%', @name_like, '%') }}

If ``@x`` is supplied at read time the inner snippet is in-lined into
the WHERE clause; otherwise it expands to the empty string and the
layer behaves as a plain ``SELECT *``. The matching ``eqlParameters``
declarations on the layer (built with ``declare_eql_parameter``) carry
the type only - ``default=""`` for String and ``default=None`` for
Double - so UI / introspection sees the parameters without the server
applying any always-on filter.

This example issues four reads against the same layer with different
parameter combinations and plots each result on its own subplot for
visual comparison.

Note: this is the **basic** parameter scenario - ``${isset:}`` over a
flat ``SELECT *``, equivalent to a client-side ``condition``. For the
canonical case (parameters reaching INSIDE a hidden CTE / JOIN), see
``read_query_layer_with_parameters.py``.
"""

import matplotlib.pyplot as plt

import os
from evergis_tools import Client
from evergis_tools.features import query_layer_to_gdf


SOURCE_LAYER_SHORT = "evg_places_qry"

CASES = [
    ({},                                                    "no parameters"),
    ({"@category": "hospital"},                             "@category=hospital"),
    ({"@category": "restaurant", "@min_conf": 0.9},         "@category=restaurant, @min_conf=0.9"),
    ({"@name_like": "Сеченов"},                             "@name_like='Сеченов'"),
]


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    source_layer = f"{username}.{SOURCE_LAYER_SHORT}"
    print(f"layer: {source_layer}\n")

    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    for ax, (params, label) in zip(axes.flat, CASES):
        gdf = query_layer_to_gdf(
            client, layer_name=source_layer,
            parameters=params or None,
            attributes=["gid", "name", "category", "confidence", "geom"],
            sort=["-confidence"],
            limit=500,
        )
        print(f"{label}  ({len(gdf)} points)")
        gdf.plot(ax=ax, markersize=6, color="#1f78b4")
        ax.set_title(f"{label}\n{len(gdf)} points")
        ax.set_axis_off()
    plt.tight_layout()
    plt.show()
