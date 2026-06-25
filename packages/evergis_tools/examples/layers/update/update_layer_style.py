"""Update the Mapbox GL style of a layer to scale circles by ``confidence``.

The seed layer ``evg_places_update_layer`` (see
``themes/layers.py::_seed_places_update_layer``) starts with no style.
This example sets a single-item ``circle`` style whose **radius** and
**color** are driven by the ``confidence`` attribute via Mapbox GL
``interpolate`` expressions:

* radius: linear from 4px at confidence=0.0 to 12px at confidence=1.0;
* color: sequential pink from ``#fde0dd`` (low) to ``#c51b8a`` (high).

After running, open the layer's companion map (``evg_map_layers``) -
high-confidence POIs render as larger and darker than low-confidence ones.

To reset the style, run::

    .venv/bin/python -m evergis_tutorial_setup themes layers --force
"""

from evergis_tools import Client
from evergis_tools.layers import update_layer_style


SOURCE_LAYER_SHORT = "evg_places_update_layer"

# EverGIS client-style format: ``{"items": [{type, paint}]}``. Inside
# ``paint`` the values use the standard Mapbox GL Style Spec:
#
#   * paint properties:   https://docs.mapbox.com/style-spec/reference/layers/#circle
#   * expression grammar: https://docs.mapbox.com/style-spec/reference/expressions/
#   * ``interpolate``:    https://docs.mapbox.com/style-spec/reference/expressions/#interpolate
#
# Shape used below:
#   ``["interpolate", ["linear"], ["get", "<attr>"], stop, value, stop, value, ...]``
STYLE = {
    "items": [
        {
            "type": "circle",
            "paint": {
                "circle-radius": [
                    "interpolate", ["linear"], ["get", "confidence"],
                    0.0,  4,
                    1.0, 12,
                ],
                "circle-color": [
                    "interpolate", ["linear"], ["get", "confidence"],
                    0.0,  "#fde0dd",
                    0.5,  "#fa9fb5",
                    1.0,  "#c51b8a",
                ],
                "circle-stroke-color": "#ffffff",
                "circle-stroke-width": 1,
                "circle-opacity": 0.85,
            },
        }
    ],
}


with Client() as client:
    username = client.account.get_user_info().username
    layer = f"{username}.{SOURCE_LAYER_SHORT}"

    update_layer_style(client, layer, STYLE, log=False)
    print(f"{layer}: style updated  "
          f"(radius 4-12 + color pink ramp, both by confidence)")
