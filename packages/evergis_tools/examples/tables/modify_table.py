from evergis_tools import modify_table_columns

from evergis_tools import Client
client = Client()
username = client.account.get_user_info().username

table_name = f"{username}.voronoi_test2"
res= modify_table_columns(
    client=client,
    table_name=table_name,
    add_columns=[
        {"name":"value2","type":"Double"},
        {"name":"name2","type":"String"}
    ],
    remove_columns=["value2"]
)
print (res)