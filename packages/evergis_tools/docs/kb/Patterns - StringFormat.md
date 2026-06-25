---
title: Patterns - StringFormat
---

# StringFormat (Attribute Formatting)

`stringFormat` is a field on the base `AttributeConfigurationDc` - available for **all** attribute types (numbers, dates, strings).

## Setting Format

```python
from evergis_api.schemas import AttributeFormatConfigurationDc
from evergis_tools.layers import get_layer_configuration, update_layer_configuration

config = get_layer_configuration(client, "john_doe.my_layer")

for attr in config.attributesConfiguration.attributes:
    if attr.attributeName == "price":
        attr.stringFormat = AttributeFormatConfigurationDc(
            format="#,#",
            splitDigitGroup=True,
            rounding=0,
            unitsLabel=" руб.",
            culture="ru-RU",
        )

update_layer_configuration(client, "john_doe.my_layer", config)
```

## Format Examples

| Use Case | format | Other params |
|----------|--------|-------------|
| Thousands separator | `#,#` | `splitDigitGroup=True` |
| 2 decimals | `#,#.00` | `rounding=2` |
| Currency | `#,#` | `unitsLabel=" руб."`, `culture="ru-RU"` |
| Percent | `0.0%` | |
| Date (Russian) | `dd.MM.yyyy` | `culture="ru-RU"` |
| Scale to thousands | | `scalingFactor=0.001`, `unitsLabel=" тыс."` |

## AttributeFormatConfigurationDc Fields

- `format: str` - .NET format string
- `culture: str` - Locale (`"ru-RU"`, `"en-US"`)
- `splitDigitGroup: bool` - Thousands separator
- `rounding: int` - Decimal places
- `scalingFactor: float` - Multiply value before display
- `unitsLabel: str` - Append text label
