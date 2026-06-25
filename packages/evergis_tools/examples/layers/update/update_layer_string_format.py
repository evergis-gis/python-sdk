"""Set per-attribute display formatting (numbers and dates).

EverGIS layers can attach a ``stringFormat`` hint to each attribute -
the popup / feature card uses it when rendering the value. Format
strings follow the standard .NET conventions:

* Numeric format strings:
  https://learn.microsoft.com/dotnet/standard/base-types/custom-numeric-format-strings
* Date / time format strings:
  https://learn.microsoft.com/dotnet/standard/base-types/custom-date-and-time-format-strings

Built-in fields used here (``stations`` seed from the ``features`` theme):

* ``elevation_m``    Double   -> ``156.3`` rendered as ``"156.3 m"``
* ``floors_visible`` Int64    -> ``5`` rendered as ``"5 floors"``
* ``installed_at``   DateTime -> ``2018-04-12`` rendered as
  ``"April 12, 2018"``

``culture`` flips the locale - swap ``en-US`` for ``ru-RU`` to get
``"12 апреля 2018 г."`` from the same DateTime format. Run
``python -m evergis_tutorial_setup themes features --force`` to drop the stringFormat hints
applied here.
"""

from evergis_api.schemas import AttributeFormatConfigurationDc

from evergis_tools import Client
from evergis_tools.layers import (
    get_layer_configuration,
    update_layer_attributes,
)


SOURCE_LAYER_SHORT = "evg_stations"

FORMATS = {
    "elevation_m": AttributeFormatConfigurationDc(
        format="#,#.0", splitDigitGroup=True, rounding=1,
        unitsLabel=" m", culture="en-US",
    ),
    "floors_visible": AttributeFormatConfigurationDc(
        format="#,#", splitDigitGroup=True, rounding=0,
        unitsLabel=" floors", culture="en-US",
    ),
    "installed_at": AttributeFormatConfigurationDc(
        format="MMMM dd, yyyy", culture="en-US",
    ),
}


with Client() as client:
    username = client.account.get_user_info().username
    layer = f"{username}.{SOURCE_LAYER_SHORT}"

    cfg = get_layer_configuration(client, layer, log=False)
    for attr in cfg.attributesConfiguration.attributes:
        fmt = FORMATS.get(attr.attributeName)
        if fmt is not None:
            attr.stringFormat = fmt

    update_layer_attributes(client, layer, cfg.attributesConfiguration, log=False)

    cfg2 = get_layer_configuration(client, layer, log=False)
    print(f"{layer} - stringFormat applied:")
    for attr in cfg2.attributesConfiguration.attributes:
        sf = getattr(attr, "stringFormat", None)
        if sf and getattr(sf, "format", None):
            units = f", units={sf.unitsLabel!r}" if sf.unitsLabel else ""
            print(f"  {attr.attributeName:14s} ({attr.type!s:8s}) "
                  f"format={sf.format!r:18s} culture={sf.culture!r}{units}")
