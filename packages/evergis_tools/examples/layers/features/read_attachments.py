"""Read and parse the Attachments column of a layer.

The seed stations layer carries a ``photos`` column with
``subType=Attachments`` (declared in the ``features`` theme). Values
land in the database as a JSON array; ``attachments_from_json`` turns
each item into a typed ``Attachment`` instance so the caller works
with real fields instead of raw dicts.

For the reverse direction (writing attachments back into a layer)
see ``edit_features.py`` / ``edit_features_with_geo.py``.
"""

from evergis_tools import Client, attachments_from_json
from evergis_tools.features import query_layer_to_df


SOURCE_LAYER_SHORT = "evg_stations"


with Client() as client:
    username = client.account.get_user_info().username
    source = f"{username}.{SOURCE_LAYER_SHORT}"

    df = query_layer_to_df(
        client, source,
        attributes=["gid", "code", "photos"],
        sort=["gid"],
    )
    print(f"layer: {source}  rows={len(df)}")
    for _, row in df.iterrows():
        photos = attachments_from_json(row["photos"])
        print(f"  gid={row['gid']}  code={row['code']!r}  photos={len(photos)}")
        for a in photos:
            kind = "URL" if a.isExternal else "catalog"
            print(f"    [{kind}] {a.name} ({a.mimeType}) -> {a.link[:60]}")
