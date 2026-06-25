"""List every tag the user has set on their catalog resources.

``iter_tags`` is a paged generator over ``catalog.get_tags`` - it
returns the tags **across the whole user-visible catalog**, not just
inside a folder. Useful for tag-autocomplete UI or to take stock of
which tags are in use overall.
"""

from evergis_tools import Client
from evergis_tools.catalog import iter_tags


with Client() as client:
    print("=== all tags ===")
    total = 0
    for tag in iter_tags(client):
        total += 1
        if total <= 10:
            print(f"  {tag}")
    print(f"... ({total} total)")

    # Server-side substring filter.
    print("\n=== tags containing 'demo' ===")
    for tag in iter_tags(client, filter="demo"):
        print(f"  {tag}")
