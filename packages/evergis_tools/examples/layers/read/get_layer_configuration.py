# -*- coding: utf-8 -*-
"""Example: Get layer configuration details."""

from evergis_tools import Client
from evergis_tools.layers import get_layer_configuration

# Load environment variables
# Initialize client
client = Client()
username = client.account.get_user_info().username

# Layer to inspect (change to your layer name)
layer_name = f"{username}.my_layer"

print(f"Getting configuration for layer: {layer_name}")
print("=" * 60)

try:
    config = get_layer_configuration(client, layer_name)

    # Basic info
    print("\n[Basic Info]")
    print(f"  Name: {config.name}")
    print(f"  Alias: {config.alias}")
    print(f"  Description: {config.description or '(none)'}")
    print(f"  Geometry Type: {config.geometryType}")
    print(f"  SRID: {config.srId}")
    print(f"  Create Table: {config.createTable}")

    # EQL Query
    print("\n[EQL Query]")
    if config.eql:
        eql_preview = config.eql[:200] + "..." if len(config.eql) > 200 else config.eql
        print(f"  {eql_preview}")
    else:
        print("  (none)")

    # EQL Parameters
    print("\n[EQL Parameters]")
    if config.eqlParameters:
        for key, value in config.eqlParameters.items():
            print(f"  {key}: {value}")
    else:
        print("  (none)")

    # Attributes Configuration
    print("\n[Attributes Configuration]")
    if config.attributesConfiguration:
        attrs = config.attributesConfiguration
        print(f"  ID Attribute: {attrs.idAttribute}")
        print(f"  Geometry Attribute: {attrs.geometryAttribute}")
        print(f"  Table Name: {attrs.tableName}")
        if attrs.attributes:
            print(f"  Attributes ({len(attrs.attributes)}):")
            for attr in attrs.attributes[:10]:  # Show first 10
                print(f"    - {attr.attributeName} ({attr.type}): {attr.alias or '(no alias)'}")
            if len(attrs.attributes) > 10:
                print(f"    ... and {len(attrs.attributes) - 10} more")
    else:
        print("  (none)")

    # Client Style
    print("\n[Client Style]")
    if config.clientStyle:
        items = config.clientStyle.get("items", [])
        print(f"  Items: {len(items)}")
        for i, item in enumerate(items):
            print(f"    [{i}] Type: {item.get('type')}")
    else:
        print("  (none)")

    # Card Configuration
    print("\n[Card Configuration]")
    if config.cardConfiguration:
        header = config.cardConfiguration.get("header", {})
        print(f"  Header Template: {header.get('templateName', '(none)')}")
        children = config.cardConfiguration.get("children", [])
        print(f"  Main Sections: {len(children)}")
        data_sources = config.cardConfiguration.get("dataSources", [])
        print(f"  Data Sources: {len(data_sources)}")
        for ds in data_sources:
            print(f"    - {ds.get('name')}: {ds.get('layerName')}")
    else:
        print("  (none)")

    # Edit Configuration
    print("\n[Edit Configuration]")
    if config.editConfiguration:
        children = config.editConfiguration.get("children", [])
        print(f"  Has Edit Form: Yes ({len(children)} top-level sections)")
    else:
        print("  (none)")

    # Export full configuration to JSON (optional)
    print("\n[Export to JSON]")
    output_file = f"{layer_name.replace('.', '_')}_config.json"
    # Uncomment to save:
    # with open(output_file, "w", encoding="utf-8") as f:
    #     json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)
    # print(f"  Saved to: {output_file}")
    print(f"  (Uncomment code to save to {output_file})")

except Exception as e:
    print(f"Error: {e}")

print("\n[OK] Done")
