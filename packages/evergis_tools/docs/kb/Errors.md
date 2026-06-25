---
title: Errors
module: evergis_tools
---

# Errors

Typed exceptions and status-code predicates for EverGIS API errors.
Import: `from evergis_tools import ResourceExists, is_conflict, ...`

The autogen client raises `ApiClientError` (from
`evergis_api._generated.exceptions`), which already carries `status_code`,
`url`, `response_text` and `response_json`. The types below are thin
subclasses plus predicates so callers can branch on the HTTP status code
instead of matching the server's message text.

---

## Exception types

All three subclass `ApiClientError`, so existing `except ApiClientError`
blocks keep catching them.

### ResourceExists
HTTP 409 - the target system name or alias is already taken.

Raised by the create wrappers (`gdf_to_layer`, `create_layer_from_schema`,
`create_query_layer`, `create_map`) when publishing hits a 409. The v3
catalog enforces unique paths (`owner/folder/alias`), so a create can
conflict on the **alias** even when `overwrite=True` already freed the
system name. `str(exc)` leads with which alias and folder collided,
followed by the raw HTTP detail in brackets; the original `ApiClientError`
is chained as `__cause__`.

```python
from evergis_tools import Client, ResourceExists, create_layer_from_schema

with Client() as client:
    try:
        create_layer_from_schema(
            client, schema=MySchema, layer_name="cities",
            layer_alias="Cities", parent_path="john_doe/Projects/Data",
        )
    except ResourceExists as exc:
        print(f"name or alias taken: {exc}")
```

### ResourceNotFound
HTTP 404 - resource missing at the requested path. Recognized by
`is_not_found`.

### ApiTransientError
5xx - a server-side error. Recognized by `is_transient`; provided so retry
logic can target transient failures.

---

## Predicates

Each takes any exception and returns `bool`. They match both the typed
subclass and a plain `ApiClientError` with the matching `status_code`, so
they work whoever raised the error.

### is_not_found
True for an HTTP 404.

```python
from evergis_tools import is_not_found

try:
    cfg = get_layer_configuration(client, "john_doe.cities")
except Exception as exc:
    if is_not_found(exc):
        cfg = None
    else:
        raise
```

### is_conflict
True for an HTTP 409 (conflict / already exists).

### is_transient
True for an HTTP 5xx (status code in the 500-599 range).

```python
from evergis_tools import is_transient

for attempt in range(3):
    try:
        result = gdf_to_layer(client, gdf, "john_doe.cities")
        break
    except Exception as exc:
        if is_transient(exc) and attempt < 2:
            continue
        raise
```

**Returns:** `bool` for every predicate.

> **Note:** Pair these with `evergis_tools._http.silence_status_codes(*codes)`
> for probe calls that intentionally trigger a 404/409 and should not log an
> error.

---

## See Also
- [[Layers/Create]] - create functions that raise `ResourceExists`
- [[Catalog/Maps]] - `create_map` raises `ResourceExists` on collision
- [[Catalog/Resources]] - resolution helpers
