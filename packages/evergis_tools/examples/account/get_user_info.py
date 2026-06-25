"""Read user info: current user (basic + extended) and lookup by name."""

from evergis_tools import Client


with Client() as client:
    me = client.account.get_user_info()
    print(f"basic:    {me.username}  roles={list(me.roles or [])}")

    extended = client.account.get_extended_user_info()
    print(f"extended: created={extended.dtCreate}  last_login={extended.dtLastLogin}")

    # Look up another user by name (requires permission to see the target).
    other = client.account.get_user_info_1(username=me.username)
    print(f"lookup:   {other.username}  email={other.email}")
