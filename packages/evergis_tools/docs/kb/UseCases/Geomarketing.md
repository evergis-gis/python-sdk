---
title: Geomarketing Use Cases
---

# Geomarketing Use Cases

Scenarios for using `evergis_tools` in geomarketing and catalog-layer analytics tasks.

> Each scenario is a "function -> role in the chain" table. Function details are on the corresponding KB pages (see [[Home]]).

---

## 1. Store coverage-zone analysis

**Task:** Determine the walking-distance coverage zones of stores and find intersections with residential buildings.

| Function | Role in the scenario |
|---------|-----------------|
| `import_xlsx_to_layer` | Import store addresses from Excel |
| `build_isochrones` | Build 5/10/15-minute walking-distance zones |
| `eql_query_to_geodataframe` | Spatial query: residential buildings within the coverage zones |
| `gdf_to_layer` | Save the analysis result |
| `update_layer_style` | Color zones by travel time |
| `update_layer_card` | Popup with store and population information |

---

## 2. Site selection for a new store

**Task:** Find optimal locations to open a store based on competitors and foot traffic.

| Function | Role in the scenario |
|---------|-----------------|
| `import_csv_to_layer` | Import foot-traffic data |
| `eql_query_to_geodataframe` | Query competitors within 500m of candidate sites |
| `copy_layer_via_eql` | Filter out sites with competitors nearby |
| `create_voronoi_with_attributes` | Build influence zones of existing stores |
| `update_layer_style` | Heatmap by foot traffic |
| `update_layer_card` | Card with location metrics |

---

## 3. Customer-base segmentation by territory

**Task:** Split customers by district and compute metrics for each segment.

| Function | Role in the scenario |
|---------|-----------------|
| `import_xlsx_to_layer` | Import the customer base with addresses |
| `eql_query_to_geodataframe` | Spatial join of customers with city districts |
| `union_layers_via_eql` | Aggregate metrics by district |
| `gdf_to_layer` | Save the segmented data |
| `update_layer_style` | Choropleth by average check per district |
| `update_layer_card` | District statistics: customers, revenue, average check |

---

## 4. Cannibalization analysis between stores

**Task:** Determine the overlap of coverage zones of your own stores.

| Function | Role in the scenario |
|---------|-----------------|
| `eql_query_to_geodataframe` | Select active stores in the network |
| `build_isochrones` | Build a coverage zone for each store |
| `eql_query_to_geodataframe` | Find zone intersections (ST_Intersects) |
| `update_layer_via_eql` | Compute intersection area and cannibalization % |
| `update_layer_style` | Highlight problematic intersections in red |
| `update_layer_card` | Details: which stores overlap, area |

---

## 5. Territory potential assessment

**Task:** Estimate sales potential based on population and infrastructure.

| Function | Role in the scenario |
|---------|-----------------|
| `import_shapefile_to_layer` | Import census data |
| `eql_query_to_geodataframe` | Count POIs (schools, offices) in each district |
| `update_layer_via_eql` | Compute the potential index by formula |
| `copy_layer_via_eql` | Select high-potential districts |
| `update_layer_style` | Gradient from low to high potential |
| `update_layer_card` | Breakdown: population, POI, index |

---

## 6. Network performance monitoring

**Task:** Build a dashboard layer with KPIs for points of sale.

| Function | Role in the scenario |
|---------|-----------------|
| `import_csv_to_layer` | Import monthly sales data |
| `eql_query_to_geodataframe` | Join sales with point geodata |
| `update_layer_via_eql` | Compute plan/actual and deviations |
| `gdf_to_layer` | Publish the KPI layer |
| `update_layer_style` | Color points by plan fulfillment (green/yellow/red) |
| `update_layer_card` | KPIs: plan, actual, %, change vs. previous month |

---

# Analytics and statistics

Scenarios for gathering statistics over existing data in the catalog.

---

## 7. Sales statistics by region

**Task:** Find a sales layer in the catalog and build an aggregated map by region.

| Function | Role in the scenario |
|---------|-----------------|
| `resolve_resource` | Find the "Sales 2024" layer by name in the catalog |
| `get_layer_schema` | Get the list of fields to build the query |
| `eql_query_to_geodataframe` | Aggregation: SUM(revenue), COUNT(*) GROUP BY region |
| `create_query_layer` | Create a view layer with aggregated data |
| `update_layer_style` | Choropleth: gradient by sales total |
| `update_layer_card` | Region card: revenue, deal count, average check |

---

## 8. Top-10 points by a metric

**Task:** Find and visualize the best/worst points by a metric.

| Function | Role in the scenario |
|---------|-----------------|
| `get_resources` | Find layers matching the pattern "*_metrics" in the project folder |
| `resolve_resource` | Get the ID of the needed layer by name |
| `eql_query_to_geodataframe` | ORDER BY metric DESC LIMIT 10 |
| `create_query_layer` | Virtual layer with the top 10 |
| `update_layer_style` | Marker size proportional to the metric |
| `update_layer_card` | Rank, point name, metric value |

---

## 9. Period comparison (year over year)

**Task:** Compare metrics for the current and previous year.

| Function | Role in the scenario |
|---------|-----------------|
| `resolve_resource` | Find the "Sales" layer |
| `eql_query_to_geodataframe` | Subqueries: 2024 and 2023 data |
| `eql_query_to_geodataframe` | JOIN and compute delta = (curr - prev) / prev * 100 |
| `create_query_layer` | Layer with the change dynamics |
| `update_layer_style` | Green = growth, red = decline (diverging scale) |
| `update_layer_card` | Metrics: 2024, 2023, change % |

---

## 10. Distribution by category

**Task:** Build a breakdown of objects by a categorical field.

| Function | Role in the scenario |
|---------|-----------------|
| `resolve_resource` | Find the "Organizations" layer by name |
| `get_layer_schema` | Determine the category field (purpose, type, etc.) |
| `eql_query_to_geodataframe` | COUNT(*) GROUP BY category |
| `create_query_layer` | Parameterized layer with a category filter |
| `update_layer_eql` | Set the @category parameter for filtering |
| `update_layer_style` | Color by category (match expression) |
| `update_layer_card` | Category, number of objects in it |

---

## 11. Object density by territory

**Task:** Compute the density of points per unit area.

| Function | Role in the scenario |
|---------|-----------------|
| `resolve_resource` | Find the points layer and the territories layer |
| `eql_query_to_geodataframe` | Spatial join: COUNT points in each polygon |
| `eql_query_to_geodataframe` | Compute density = count / ST_Area(geometry) |
| `create_query_layer` | Density layer |
| `update_layer_style` | Density gradient (quantile breaks) |
| `update_layer_card` | Territory, object count, area, density |

---

## 12. Layer summary dashboard

**Task:** Create an informational layer with key metrics.

| Function | Role in the scenario |
|---------|-----------------|
| `get_resources` | Get the list of layers in the "Data" folder |
| `resolve_resource` | Select a layer by name from the list |
| `get_layer_configuration` | Read the layer's current configuration |
| `eql_query_to_geodataframe` | Compute aggregates: min, max, avg, sum, count |
| `update_layer_style` | Conditional coloring by a key metric |
| `update_layer_card` | Mini-dashboard: all aggregates in the card |

---

## Summary of tools used

| Category | Functions |
|-----------|---------|
| **Catalog** | `resolve_resource`, `get_resources`, `get_layer_schema`, `get_layer_configuration` |
| **Import** | `import_xlsx_to_layer`, `import_csv_to_layer`, `import_shapefile_to_layer` |
| **EQL queries** | `eql_query_to_geodataframe` (spatial joins, filtering, aggregation) |
| **Geoprocessing** | `build_isochrones`, `create_voronoi_with_attributes`, `copy_layer_via_eql`, `union_layers_via_eql`, `update_layer_via_eql` |
| **Layer creation** | `gdf_to_layer`, `create_query_layer` |
| **Styling** | `update_layer_style`, `update_layer_card`, `update_layer_eql` |
