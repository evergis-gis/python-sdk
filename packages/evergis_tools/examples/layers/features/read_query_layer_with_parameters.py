"""Read a virtual query layer that hides a CTE/JOIN behind one parameter.

This is the canonical use of EQL parameters: the layer's actual EQL is
a CTE+JOIN+GROUP BY that the reader never sees, and the only knob the
reader can turn is the parameter the layer designer chose to expose.

The layer ``evg_distr_poi_count`` (provisioned by the ``shared``
tutorial theme, ``evergis_tutorial_setup.themes.shared``)
returns one row per Moscow district (146 districts) with the count of
POIs of an arbitrary category that fall inside it. The expansion

    ${isset:@category, { AND category = @category }}

sits **inside the CTE that picks the POIs**, BEFORE the JOIN with the
districts. Switching ``@category`` switches what gets counted - the
district geometry is always the same, the ``n`` column changes. Output
carries the district MultiPolygon, ready for ``gdf.plot()`` as a
choropleth.

Plain ``condition`` cannot do this: it is added to the OUTER select,
after the GROUP BY, so it can only filter the aggregated result -
not the rows that go INTO the aggregation.
"""

import matplotlib.pyplot as plt

from evergis_tools import Client
from evergis_tools.features import query_layer_to_gdf


SOURCE_LAYER_SHORT = "evg_distr_poi_count"

CATEGORIES = ["hospital", "restaurant"]


with Client() as client:
    username = client.account.get_user_info().username
    source_layer = f"{username}.{SOURCE_LAYER_SHORT}"
    print(f"layer: {source_layer}\n")

    fig, axes = plt.subplots(1, len(CATEGORIES), figsize=(14, 7))
    for ax, category in zip(axes, CATEGORIES):
        gdf = query_layer_to_gdf(
            client, layer_name=source_layer,
            parameters={"@category": category},
            # CTE aliases the count as ``district`` and keeps the geometry
            # under its native column name ``geom`` (see shared.py EQL).
            attributes=["district", "n", "geom"],
            sort=["-n"],
        )
        print(f"@category={category!r}  top 5 districts:")
        print(gdf.drop(columns="geometry").head().to_string(index=False))
        print()
        gdf.plot(ax=ax, column="n", cmap="OrRd", legend=True,
                 edgecolor="white", linewidth=0.3)
        ax.set_title(f"POIs by district: category={category!r}")
        ax.set_axis_off()
    plt.tight_layout()
    plt.show()
