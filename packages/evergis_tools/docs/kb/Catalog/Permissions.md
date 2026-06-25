---
title: Catalog - Permissions
module: evergis_tools.catalog.permissions
---

# Permissions

Import: `from evergis_tools.catalog import get_permissions, set_permissions, add_permission, remove_permission`

All functions accept either `resource_id` or `resource_path` (keyword-only, mutually exclusive).

---

## get_permissions
Get current ACL for a resource.

```python
from evergis_tools.catalog import get_permissions

acl = get_permissions(client, resource_path="john_doe/Projects/Layer")
for entry in acl.data:
    print(f"{entry.role}: {entry.permissions}")
```

**Key params:** `client`, `resource_id=None`, `resource_path=None`, `log=True`

**Returns:** `AccessControlListDc` - with `.data: List[RolePermissionDc]`.

---

## set_permissions
Replace **all** permissions on a resource.

```python
from evergis_tools.catalog import set_permissions

set_permissions(
    client,
    {"admin": "read,write,configure", "viewer": "read"},
    resource_path="john_doe/Projects/Layer",
)
```

**Key params:** `client`, `permissions: Dict[str, str|PermissionLevel]`, `resource_id=None`, `resource_path=None`, `log=True`

**Returns:** `bool`

> **Warning:** Replaces ALL existing permissions - not additive. Use `add_permission` to modify a single role.

**Permission values:** `"none"`, `"read"`, `"write"`, `"configure"`, `"read,write"`, `"read,configure"`, `"read,write,configure"`

---

## add_permission
Add or update permission for a single role without affecting others.

```python
from evergis_tools.catalog import add_permission

add_permission(client, "editor", "read,write",
    resource_path="john_doe/Projects/Layer")
```

**Key params:** `client`, `role: str`, `permission: str|PermissionLevel`, `resource_id=None`, `resource_path=None`, `log=True`

**Returns:** `bool`

---

## remove_permission
Remove a role from resource ACL.

```python
from evergis_tools.catalog import remove_permission

remove_permission(client, "viewer", resource_path="john_doe/Projects/Layer")
```

**Key params:** `client`, `role: str`, `resource_id=None`, `resource_path=None`, `log=True`

**Returns:** `bool`

> **Warning:** Raises `ValueError` if role not found in current permissions.

---

## See Also
- [[Catalog/Resources|Resources]] - Resolve resource identifiers
- [[Catalog/Catalog|Catalog]] - Overview
