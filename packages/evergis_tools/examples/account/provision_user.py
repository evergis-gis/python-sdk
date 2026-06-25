"""Provision a demo user: create the user, set roles, then clean up.

Uses ``evergis_tools.account.provision_user`` (create + namespace + roles)
and ``set_roles`` (set the exact role list). Both helpers are safe to
re-run - if the user already exists, only roles get reconciled.

Requires admin privileges. The demo user is removed at the end.
"""

from evergis_tools import Client
from evergis_tools.account import iter_roles, provision_user, set_roles


DEMO_USERNAME = "evg_demo_user"
DEMO_PASSWORD = "DemoPass!1234"
DEMO_EMAIL = "evg_demo_user@example.com"


with Client() as client:
    # Pick any existing custom role so the example is portable across
    # installations that have different role catalogs.
    sample_role = next(iter_roles(client, with_system=False), None)

    # Create (or fetch) the user.
    user = provision_user(
        client=client,
        username=DEMO_USERNAME,
        password=DEMO_PASSWORD,
        email=DEMO_EMAIL,
        first_name="Demo",
        last_name="User",
    )
    print(f"provisioned {user.username} roles={list(user.roles or [])}")

    if sample_role is not None:
        # ``set_roles`` removes any role that's not in the target set,
        # so include the auto-assigned system roles (the ones starting
        # with "__") to avoid removing them by accident.
        current = set(
            client.account.get_extended_user_info_1(
                username=DEMO_USERNAME
            ).roles
            or []
        )
        system_roles = {r for r in current if r.startswith("__")}
        target = system_roles | {sample_role.name}

        added, removed = set_roles(client, DEMO_USERNAME, target)
        print(
            f"set_roles -> added={sorted(added)} removed={sorted(removed)}"
        )

    # Re-running ``provision_user`` does nothing because the user
    # already exists - it just returns the existing record.
    user_again = provision_user(
        client=client,
        username=DEMO_USERNAME,
        password=DEMO_PASSWORD,
        email=DEMO_EMAIL,
    )
    print(f"second run, same user: {user_again.username}")

    # Cleanup.
    client.account.remove_user(username=DEMO_USERNAME)
    print(f"removed {DEMO_USERNAME}")
