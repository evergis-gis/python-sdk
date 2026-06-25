# evergis-api

Low-level EverGIS API client, generated from the platform's OpenAPI (swagger)
spec. Ships both a synchronous `Client` and an asynchronous `AsyncClient`.

Most code should use the higher-level [`evergis-tools`](../evergis_tools)
instead; reach for `evergis-api` directly only when you need full control over
the wire calls.

The generated code lives in `evergis_api/_generated/` and **must not be edited
by hand** - it is overwritten on every regeneration. The contract snapshot it
was built from is `spec.json` next to this README.

## Install

Not on a package index yet - install from git:

```bash
pip install "git+https://github.com/evergis-gis/python-sdk.git#subdirectory=packages/evergis_api"
```

> Once published this becomes `pip install evergis-api`.

Editable, from a checkout:

```bash
uv pip install -e packages/evergis_api
```

## Quick start

The raw client takes the host and token explicitly (unlike `evergis-tools`'
`Client()`, which reads them from the environment):

```python
from evergis_api import Client

with Client(base_url="https://your-host", sb_token="...") as client:
    me = client.account.get_user_info()
    print(me.username)
```

Async:

```python
from evergis_api import AsyncClient

async with AsyncClient(base_url="https://your-host", sb_token="...") as client:
    me = await client.account.get_user_info()
```

Calls are grouped by area on the client: `client.catalog`, `client.layers`,
`client.eql`, `client.account`, `client.tables`, and so on. Request/response
models and `ApiClientError` are importable from `evergis_api` /
`evergis_api.schemas`.

## License

Apache License 2.0. Copyright 2026 Everpoint.
