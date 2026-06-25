---
title: Async
module: evergis_tools._async
---

# Async

Async versions of EQL functions. Import: `from evergis_tools._async.eql import ...`

## eql_query_to_dataframe (async)

```python
from evergis_tools._async.eql import eql_query_to_dataframe

df = await eql_query_to_dataframe(query, async_client)
```

## eql_query_to_geodataframe (async)

```python
from evergis_tools._async.eql import eql_query_to_geodataframe

gdf = await eql_query_to_geodataframe(query, async_client)
```

Same parameters as sync versions in [[EQL]]. Uses shared helpers internally - no code duplication.

## See Also
- [[EQL]] - Sync versions
