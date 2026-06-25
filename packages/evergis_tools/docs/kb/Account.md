---
title: Account
module: evergis_tools.account
---

# Account

Auth, user provisioning, and role sync on top of `evergis_api.AccountClient`. Import: `from evergis_tools.account import ...`

`Client()` reads credentials from the environment (`EVERGIS_HOST`, `EVERGIS_SB_TOKEN`), so the examples below construct it with no arguments.

## Auth

### login_with_credentials
Authenticate by username/password and attach the bearer token to the client.

```python
from evergis_api import Client
from evergis_tools.account import login_with_credentials

client = Client(base_url="https://api.example.com")
result = login_with_credentials(client, "alice", "s3cret")
# subsequent calls on `client` are authenticated automatically
print(result.token, result.refreshToken)
```

**Key params:** `client`, `username`, `password`.

**Returns:** `LoginResultDc` - full server response (`token`, `refreshToken`, `redirectUrl`, `username`). Persist `refreshToken` if you need long-lived sessions.

## Users

### iter_users
Stream every user matching the filter, paging through the API automatically.

```python
from evergis_tools.account import iter_users

for user in iter_users(client, filter="al%", roles=["editor"]):
    print(user.username, user.email)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | Authenticated `evergis_api.Client` |
| `filter` | `None` | SQL-like name filter (`%`, `_` wildcards) |
| `order_by` | `None` | Server-side ordering property |
| `users` | `None` | Restrict to specific usernames |
| `roles` | `None` | Restrict to users having any of these roles |
| `page_size` | `1000` | Items per request |

**Returns:** `Iterator[UserInfoDc]` - lazy generator; pages are fetched on demand.

### provision_user
Onboard a user: create + (optional) namespace + role assignment. Safe to re-run.

```python
from evergis_tools.account import provision_user

user = provision_user(
    client,
    username="bob",
    password="initial-pass",
    email="bob@example.com",
    first_name="Bob",
    last_name="Marley",
    roles=["editor", "viewer"],
    with_namespace=True,
)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | Authenticated `evergis_api.Client` |
| `username` | required | Login |
| `password` | required | Initial password |
| `email` | required | Contact email |
| `first_name` | `""` | Profile first name |
| `last_name` | `""` | Profile last name |
| `roles` | `None` | Roles to assign; `None` leaves membership alone |
| `with_namespace` | `True` | Pass `createNamespace=True` to `create_user` |
| `is_active` | `True` | Mark the new user as active |
| `is_email_confirmed` | `True` | Skip the email-confirmation flow |

**Returns:** `UserInfoDc` for the resulting user.

> **Note:** If the user already exists, the existing record is returned and only roles are reconciled (via `set_roles`, and only when `roles is not None`); other fields are left untouched.

### set_roles
Make `username` have **exactly** `roles` and nothing else (declarative sync).

```python
from evergis_tools.account import set_roles

added, removed = set_roles(client, "bob", ["editor", "viewer"])
print("added:", added, "removed:", removed)
```

**Key params:** `client`, `username`, `roles` (any iterable of strings).

**Returns:** `tuple[set[str], set[str]]` - `(added, removed)` for visibility.

> **Warning:** Strict equality - any role currently assigned but not in `roles` will be removed, including auto-managed system roles (typically `__`-prefixed). To only grant a role, call `client.account.add_to_role` directly, or include the existing system roles in the desired set.

### update_user
Partial update for an existing user - fetches current state and merges only the provided fields.

```python
from evergis_tools.account import update_user

user = update_user(
    client, "bob",
    email="bob.new@example.com",
    company="Acme",
    is_active=True,
)
```

**Key params:** `client`, `username`, `**fields` (any field accepted by `UpdateUserDc`: `email`, `first_name`, `last_name`, `patronymic`, `phone`, `company`, `position`, `location`, `is_active`, `is_email_confirmed`, `is_subscribed`, `is_open_last_project`, `namespace`, `emoji`, `goals`, `password`).

**Returns:** `UserInfoDc` after the update.

> **Note:** The underlying `account.update_user` endpoint expects a full `UpdateUserDc` body - sending only the changed field would blank out the rest. This helper handles the merge.

## Roles

### iter_roles
Stream every role matching the filter, paging through the API automatically.

```python
from evergis_tools.account import iter_roles

for role in iter_roles(client, filter="edit%", with_system=False):
    print(role.name, role.alias)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | Authenticated `evergis_api.Client` |
| `filter` | `None` | SQL-like role-name filter (`%`, `_` wildcards) |
| `user_filter` | `None` | Restrict to roles whose members match this username pattern |
| `order_by` | `None` | Server-side ordering property |
| `with_system` | `None` | Include built-in/system roles |
| `page_size` | `1000` | Items per request |

**Returns:** `Iterator[RoleInfoDc]` - lazy generator; pages are fetched on demand.

### create_role
Create a new role.

```python
from evergis_tools.account import create_role

role = create_role(
    client, "editor",
    alias="Editor",
    description="Can edit layers and features",
)
```

**Key params:** `client`, `name` (system name, used by `add_to_role`), `alias`, `description`.

**Returns:** `RoleInfoDc` for the created role.

> **Note:** Raises `ResourceExists` (importable from `evergis_tools`) if a role with this name already exists. See [[Errors]].

### update_role
Partial update for an existing role - preserves the current `alias` and submits a merged body.

```python
from evergis_tools.account import update_role

role = update_role(
    client, "editor",
    alias="Senior Editor",
    description="Can edit layers, features, and maps",
)
# rename:
role = update_role(client, "editor", name="senior_editor")
```

**Key params:** `client`, `name` (current role name), `**fields` (any field accepted by `UpdateRoleDc`: `name` for rename, `alias`, `description`).

**Returns:** `RoleInfoDc` for the updated role.

> **Note:** `description` is not returned by the role-listing endpoint, so it cannot be auto-preserved - pass `description=` explicitly if you want to set or change it.

> **Warning:** Raises `ValueError` if no role with the given name exists.

## Key Behaviors

- **Auto-paging.** `iter_users` and `iter_roles` page until the server returns fewer items than `page_size`; safe to iterate over arbitrarily large user/role sets.
- **Idempotent provisioning.** `provision_user` re-runs cleanly: if the user already exists, only roles are reconciled and the existing record is returned.
- **Declarative role sync.** `set_roles` issues `add_to_role` / `remove_from_role` only for the diff between current and target sets - cheap to call repeatedly.
- **Merge-on-update.** `update_user` and `update_role` fetch the current entity and merge the provided fields, working around server endpoints that expect a full body.

## See Also
- [[Catalog/Permissions|Permissions]] - grant role-based access to catalog resources
