"""List users with a server-side filter, paging through the result.

Uses ``evergis_tools.account.iter_users`` - it fetches as many pages as
needed automatically, so you don't hit the per-request limit on large
catalogs.
"""

from evergis_tools import Client
from evergis_tools.account import iter_users


with Client() as client:
    # 1. Stream every user (paged behind the scenes).
    print("=== all users ===")
    total = 0
    for u in iter_users(client):
        total += 1
        if total <= 5:
            print(f"  {u.username:20s} {u.email or '':40s} roles={list(u.roles or [])}")
    print(f"... ({total} total)")

    # 2. Filter by name pattern + role.
    print("\n=== users in 'staff' role ===")
    for u in iter_users(client, roles=["staff"]):
        print(f"  {u.username:20s} {u.email or ''}")
