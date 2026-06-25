"""Run a SELECT EQL query with a filter and get a pandas DataFrame.

``eql_query_to_dataframe`` returns attributes only (no geometry).
The example fetches Moscow divisions whose names start with the
Cyrillic letter ``'С'``,
sorted alphabetically.

Reads from the seed layer ``{SAMPLE_DATA_OWNER}.evg_overture_districts``
populated by ``python -m evergis_tutorial_setup themes shared --force``.
"""

import os
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_dataframe


QUERY = """
SELECT name, subtype
FROM {SAMPLE_DATA_OWNER}.evg_overture_districts
WHERE name LIKE 'С%'
ORDER BY name
LIMIT 10
"""


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    df = eql_query_to_dataframe(QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username), client)

    print(f"rows: {len(df)}")
    print(df.to_string(index=False))
