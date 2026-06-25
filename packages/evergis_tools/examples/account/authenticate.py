"""Authenticate against EverGIS.

Three ways to provide credentials, in order of preference:

1. ``Client()`` - reads ``EVERGIS_HOST`` / ``EVERGIS_SB_TOKEN`` from the
   environment (or a ``.env`` file in dev). This is the form every other
   example uses.
2. ``Client(base_url=..., sb_token=...)`` - explicit overrides; useful
   when credentials live somewhere other than env vars.
3. Username + password login -> JWT bearer token. Uses the
   ``login_with_credentials`` helper, which calls ``authenticate`` and
   stores the returned JWT on the client for the next calls.
"""

import os

from evergis_api import Client as ApiClient
from evergis_tools import Client
from evergis_tools.account import login_with_credentials


# 1. Implicit: env / .env supplies credentials.
with Client() as client:
    info = client.account.get_user_info()
    print(f"[implicit]    {info.username}")


# 2. Explicit: pass creds directly.
with Client(
    base_url=os.environ["EVERGIS_HOST"],
    sb_token=os.environ["EVERGIS_SB_TOKEN"],
) as explicit:
    print(f"[explicit]    {explicit.account.get_user_info().username}")


# 3. Username/password login -> JWT bearer token.
# Start from the bare API client (no sb_token in env); the helper logs in
# and stores the returned JWT on the client.
with ApiClient(base_url=os.environ["EVERGIS_HOST"]) as bearer_client:
    login_with_credentials(
        bearer_client,
        username=os.environ["EVERGIS_USERNAME"],
        password=os.environ["EVERGIS_PASSWORD"],
    )
    print(f"[bearer]      {bearer_client.account.get_user_info().username}")
