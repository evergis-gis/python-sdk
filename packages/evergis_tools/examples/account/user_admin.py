"""User admin lifecycle: create, partial update, activate/deactivate, remove.

* ``provision_user`` - create + namespace + (optional) roles. Safe to
  re-run: if the user is already there, it just returns the existing
  record.
* ``update_user`` - lets you change a single field; behind the scenes
  it loads the current values and submits the merged body, because the
  API requires a full ``UpdateUserDc``.
* Activate / deactivate / remove - direct ``client.account.*`` calls,
  no wrapper needed.
"""

from evergis_tools import Client
from evergis_tools.account import provision_user, update_user


DEMO_USERNAME = "evg_demo_user"
DEMO_PASSWORD = "DemoPass!1234"


with Client() as client:
    # 1. Create the user (or return the existing one).
    user = provision_user(
        client=client,
        username=DEMO_USERNAME,
        password=DEMO_PASSWORD,
        email="evg_demo_user@example.com",
        first_name="Demo",
        last_name="User",
    )
    print(f"created: {user.username} email={user.email}")

    # 2. Partial update - only the changed fields are passed.
    updated = update_user(
        client,
        DEMO_USERNAME,
        email="evg_demo_user+updated@example.com",
        last_name="Updated",
    )
    print(f"updated: email={updated.email} last_name={updated.last_name}")

    # 3. Deactivate / reactivate (direct API).
    client.account.deactivate_user(username=DEMO_USERNAME)
    print("deactivated")
    client.account.activate_user(username=DEMO_USERNAME)
    print("activated")

    # 4. Remove (direct API).
    client.account.remove_user(username=DEMO_USERNAME)
    print(f"removed {DEMO_USERNAME}")
