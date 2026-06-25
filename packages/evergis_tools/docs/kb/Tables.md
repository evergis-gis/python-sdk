---
title: Tables
module: evergis_tools.tables
---

# Tables

Materialized views management. Import: `from evergis_tools.tables import ...`

## create_materialized_view
Create materialized view from EQL query.

```python
from evergis_tools.tables import create_materialized_view

result = create_materialized_view(
    client, "john_doe.my_view",
    eql="SELECT city, count(*) as cnt FROM john_doe.objects GROUP BY city",
    override=True,
)
```

## create_materialized_view_from_layer
Create materialized view from existing layer.

```python
from evergis_tools.tables import create_materialized_view_from_layer

result = create_materialized_view_from_layer(
    client, "john_doe.my_view", "john_doe.source_layer",
    override=True,
)
```

> **Note:** Both `create_materialized_view*` raise `ResourceExists` (importable from `evergis_tools`) when a view with this name already exists and `override=False`. See [[Errors]].

## refresh_materialized_view
Refresh (recreate) materialized view with current data.

```python
from evergis_tools.tables import refresh_materialized_view

result = refresh_materialized_view(client, "john_doe.my_view")
```

> Note: No dedicated refresh endpoint - function reads config and recreates with `override=True`.

## Table Column Operations

These functions live in `evergis_tools.tables` next to the materialized view helpers. They raise on errors and return `DetailedTableInfoDc` with the updated table. Table names without a username prefix are normalized automatically.

### add_columns
Add columns to existing table.
```python
from evergis_tools.tables import add_columns
add_columns(client, "john_doe.my_table", [{"name": "new_col", "type": "String"}])
```

### remove_columns
Remove columns from table.
```python
from evergis_tools.tables import remove_columns
remove_columns(client, "john_doe.my_table", ["old_col"])
```

### modify_table_columns
Add and remove columns in a single operation.
```python
from evergis_tools.tables import modify_table_columns
modify_table_columns(client, "john_doe.my_table",
    add_columns=[{"name": "new_col", "type": "String"}],
    remove_columns=["old_col"],
)
```

## See Also
- [[Layers]] - Layer CRUD
- [[EQL]] - EQL queries
