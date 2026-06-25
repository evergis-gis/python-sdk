---
title: PydanticUtils
module: evergis_tools.pydantic_utils
---

# PydanticUtils

Pydantic model and layer schema utilities. Import: `from evergis_tools.pydantic_utils import ...`

## get_model_field_info
Extract field information from Pydantic model.

```python
from evergis_tools.pydantic_utils import get_model_field_info

info = get_model_field_info(MyModel)
# {'field_name': {'type': str, 'required': True, 'default': None, ...}}
```

## validate_layer_against_model
Validate JSON layer definition against Pydantic model.

```python
from evergis_tools.pydantic_utils import validate_layer_against_model

result = validate_layer_against_model(layer_json, MyModel)
```

## create_attribute_mappings
Create attribute mappings using Pydantic model types.

```python
from evergis_tools.pydantic_utils import create_attribute_mappings

source_map, target_map = create_attribute_mappings(layer_json, MyModel)
```

## create_mappings_from_pydantic
Auto-create field mappings from Pydantic model.

```python
from evergis_tools.pydantic_utils import create_mappings_from_pydantic

source_map, target_map = create_mappings_from_pydantic(MyModel, exclude_geometry=True)
```

## get_matching_fields
Get fields present in both JSON definition and Pydantic model.

```python
from evergis_tools.pydantic_utils import get_matching_fields

common = get_matching_fields(layer_json, MyModel)
```

## create_mappings_from_json
Create mappings from JSON layer definition.

```python
from evergis_tools.pydantic_utils import create_mappings_from_json

source_map, target_map = create_mappings_from_json(layer_json, MyModel)
```

## get_model_by_name
Find Pydantic model by name from a list.

```python
from evergis_tools.pydantic_utils import get_model_by_name

model = get_model_by_name("MyModel", [MyModel, OtherModel])
```

## create_mappings_from_json_auto
Auto-create mappings using best matching model.

```python
from evergis_tools.pydantic_utils import create_mappings_from_json_auto

model, source_map, target_map = create_mappings_from_json_auto(layer_json, [MyModel, OtherModel])
```

## See Also
- [[Layers]] - Layer creation from Pydantic schema
- [[Attributes]] - Type conversion
