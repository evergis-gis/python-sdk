"""List roles with server-side filter / paging.

Uses ``evergis_tools.account.iter_roles``. ``with_system=True`` includes
built-in roles; ``user_filter`` restricts to roles whose members match
the given user-name pattern.
"""

from evergis_tools import Client
from evergis_tools.account import iter_roles


with Client() as client:
    print("=== custom roles only ===")
    for r in iter_roles(client, with_system=False):
        print(f"  {r.name:30s} alias={r.alias or '':30s} users={len(r.users or [])}")

    print("\n=== including system roles ===")
    total = sum(1 for _ in iter_roles(client, with_system=True))
    print(f"  total: {total}")
