---
title: Quick start
---

# Quick start

In the EverGIS Python sandbox `evergis_tools` is already installed and
your credentials are already in the environment, so a client connects
with no arguments. This recipe checks who you are and lists what you
have in the catalog.

```python
from evergis_tools import Client
from evergis_tools.catalog import iter_resources

with Client() as client:
    # Who am I (the sandbox connects you as your own user).
    me = client.account.get_user_info()
    print(f"You are: {me.username}")

    # Your catalog entries. iter_resources streams every page,
    # so you never deal with paging by hand.
    print("Your resources:")
    for resource in iter_resources(client, owner_filter="My"):
        print(f"  {resource.type:12s} {resource.name}")
```

Notes:

- `Client()` takes no arguments in the sandbox - host and token come
  from the environment. The `with` block closes the connection for you.
- `owner_filter="My"` lists what you own. Use `"Shared"` to also see
  resources shared with you.
- `iter_resources` is a generator: it fetches pages on demand and stops
  when you stop iterating. Pass `parent="username/Folder"` to list
  inside a specific folder instead of the catalog root.

## See also

- [[layer-from-geodataframe|Create a layer from a GeoDataFrame]]
- [[catalog-basics|Find and manage resources]]
