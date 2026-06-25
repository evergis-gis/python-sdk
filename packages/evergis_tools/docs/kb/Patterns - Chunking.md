---
title: Patterns - Chunking
---

# Size-Based Chunking

EverGIS API has request size limits. Always use **size-based** chunking, not count-based.

## How It Works

`chunk_features_by_size()` splits features by JSON payload size in bytes (default 1.2 MB per chunk).

```python
from evergis_tools.features import chunk_features_by_size

chunks = chunk_features_by_size(features, max_chunk_size_bytes=1_200_000)
for chunk in chunks:
    client.layers.create_features(name=layer_name, body=chunk)
```

## Why Not Count-Based

Features have different sizes:
- Point with 3 fields: ~200 bytes
- MultiPolygon with 100 fields: ~50 KB

Count-based chunking (e.g., 1000 features) can produce 200 KB or 50 MB chunks - unpredictable.

## Built-In

`add_gdf_features_to_layer()` uses size-based chunking internally:

```python
add_gdf_features_to_layer(client, gdf, "john_doe.layer", chunk_size_bytes=1_200_000)
```
