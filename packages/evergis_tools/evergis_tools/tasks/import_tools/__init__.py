"""
Module for importing data into EverGIS.

Provides tools for:
- Fetching the data schema via the REST API (CSV, XLSX, Shapefile, GPKG, FGDB)
- Importing CSV / XLSX / Shapefile / GPKG / FGDB files into layers
- The ``build_attribute_mappings_from_schema`` helper for building
  ``attribute_mapping`` / ``attribute_type_mapping`` from a
  ``get_*_data_schema_rest`` response without hardcoding it in every example.
"""

from .get_info import (
    build_attribute_mappings_from_schema,
    get_csv_data_schema_rest,
    get_fgdb_data_schema_rest,
    get_gpkg_data_schema_rest,
    get_shapefile_data_schema_rest,
    get_xlsx_data_schema_rest,
)
from .csv_import_to_layer import import_csv_to_layer
from .fgdb_import_to_layer import import_fgdb_to_layer
from .gpkg_import_to_layer import import_gpkg_to_layer
from .shapefile_import_to_layer import import_shapefile_to_layer
from .xlsx_import_to_layer import import_xlsx_to_layer

__all__ = [
    "build_attribute_mappings_from_schema",
    "get_csv_data_schema_rest",
    "get_fgdb_data_schema_rest",
    "get_gpkg_data_schema_rest",
    "get_shapefile_data_schema_rest",
    "get_xlsx_data_schema_rest",
    "import_csv_to_layer",
    "import_fgdb_to_layer",
    "import_gpkg_to_layer",
    "import_shapefile_to_layer",
    "import_xlsx_to_layer",
]
