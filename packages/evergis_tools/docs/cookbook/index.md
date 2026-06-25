---
title: Cookbook
---

# evergis_tools cookbook

Task-oriented recipes for working in the EverGIS Python sandbox. Each
page is a single, copy-paste-runnable script with a short explanation.
The sandbox already has `evergis_tools` installed and your credentials
in the environment, so every recipe starts with `client = Client()` -
nothing to install or configure.

Looking for the full per-function API reference instead? See the
[KB](../kb/Home.md).

## Recipes

- [[quickstart|Quick start]] - connect, who am I, list my resources
- [[layer-from-geodataframe|Create a layer from a GeoDataFrame]]
- [[layer-from-schema|Create a layer from a schema]]
- [[query-layer-to-geodataframe|Query a layer into a GeoDataFrame]]
- [[import-files|Import a file (gpkg / csv / shapefile / xlsx) into a layer]]
- [[export-layer|Export a layer to a file]]
- [[edit-features|Add, edit and delete features]]
- [[query-layers|Build a query (virtual) layer with EQL]]
- [[geoprocessing|Geoprocessing: buffers, union, validate]]
- [[network-analysis|Network analysis: isochrones, routes, OD-matrix]]
- [[catalog-basics|Find and manage resources, folders and files]]

## Conventions

Recipes create their outputs under a `username/Cookbook` folder with
plain names, so they are easy to find and easy to clean up. See
[Authoring rules](../contributing/cookbook-authoring.md) if you contribute recipes.
