---
title: Validation
module: evergis_tools.validation
---

# Validation

Input validation utilities. Import: `from evergis_tools.validation import ...`

## validate_feature_properties
Validate feature properties dict against required fields.

```python
from evergis_tools.validation import validate_feature_properties

is_valid = validate_feature_properties(properties, required_fields=["name", "value"])
```

## validate_pagination_params
Validate pagination parameters.

```python
from evergis_tools.validation import validate_pagination_params

is_valid = validate_pagination_params(page=1, limit=100)
```

Also re-exports all geometry validators from [[Geometry]].

## to_safe_field_name
Normalize an arbitrary field name into a safe identifier: transliterate Cyrillic to Latin, strip diacritics, convert to snake_case, replace invalid characters with underscores, collapse and strip underscores. Re-exported at the package root.

```python
from evergis_tools import to_safe_field_name

safe = to_safe_field_name("Название Поля")
# 'nazvanie_polya'
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `name` | required | Original field name (coerced to `str` if not already) |
| `max_length` | `None` | Truncate result to this length; `None` means unlimited |
| `ensure_unique` | `False` | Disambiguate against `existing_names` by appending `_1`, `_2`, ... |
| `existing_names` | `None` | Set of already-used names; required when `ensure_unique=True` |
| `to_snake_case` | `True` | Convert camelCase/PascalCase to snake_case |
| `allow_numbers_start` | `False` | When `False`, prefix `f_` if the result starts with a non-letter |

**Returns:** `str` - the safe field name.

**Raises:** `ValueError` if `ensure_unique=True` but `existing_names` is `None`.

```python
from evergis_tools import to_safe_field_name

to_safe_field_name("fieldName")                       # 'field_name'
to_safe_field_name("123field")                        # 'f_123field'
to_safe_field_name("Very-Long Field Name!", max_length=10)  # 'very_long_'
to_safe_field_name(
    "fieldName", ensure_unique=True, existing_names={"field_name"}
)                                                     # 'field_name_1'
```

> **Note:** When the cleaned result is empty it falls back to `DEFAULT_FIELD_NAME` (from `evergis_tools._config`). Superscript/subscript digits are converted to regular digits before cleaning.

## See Also
- [[Geometry]] - Geometry validators
- [[Attributes]] - Field validation
