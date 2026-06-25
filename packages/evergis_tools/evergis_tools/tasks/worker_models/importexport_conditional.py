"""Conditional StartParameters models for importExport worker."""

from typing import Union, List, Optional, Literal, Dict, Any
from pydantic import Field
from evergis_api.schemas import TaskPrototypeDto
from .models import BaseStartParameters, LayerReferenceConfig, SourceEqlConfig, create_task_prototype

class BaseImportexportStartParameters(BaseStartParameters):
    """Base class for all importExport combinations."""
    pass


class CsvSourceMixin:
    """Mixin for source type fields."""
    source_fileName: Optional[str] = Field(None, description="Имя файла")
    source_coordSourceFields: Optional[List[str]] = Field(None, description="Поля с координатами")
    source_columnDelimiter: Optional[str] = Field(None, description="Символ разделителя")
    source_spatialReference: Optional[int] = Field(None, description="SpatialReference Id.")
    source_isWkt: Optional[bool] = Field(None, description="Геометрия в WKT")
    source_attributeNameRowNumber: Optional[int] = Field(None, description="AttributeNameRowNumber")
    source_aliasRowNumber: Optional[int] = Field(None, description="AliasRowNumber")
    source_firstDataRowNumber: Optional[int] = Field(None, description="FirstDataRowNumber")


class GdbSourceMixin:
    """Mixin for source type fields."""
    source_fileName: Optional[str] = Field(None, description="Имя файла")
    source_layerName: Optional[str] = Field(None, description="Имя слоя")


class KmlSourceMixin:
    """Mixin for source type fields."""
    source_fileName: Optional[str] = Field(None, description="Имя файла")
    source_layerName: Optional[str] = Field(None, description="Имя слоя")


class TabSourceMixin:
    """Mixin for source type fields."""
    source_fileName: Optional[str] = Field(None, description="Имя файла")
    source_layerName: Optional[str] = Field(None, description="Имя слоя")


class GpkgSourceMixin:
    """Mixin for source type fields."""
    source_fileName: Optional[str] = Field(None, description="Имя файла")
    source_layerName: Optional[str] = Field(None, description="Имя слоя")


class ExcelSourceMixin:
    """Mixin for source type fields."""
    source_fileName: Optional[str] = Field(None, description="Имя файла")
    source_attributeNameRowNumber: Optional[int] = Field(None, description="AttributeNameRowNumber")
    source_aliasRowNumber: Optional[int] = Field(None, description="AliasRowNumber")
    source_firstDataRowNumber: Optional[int] = Field(None, description="FirstDataRowNumber")
    source_coordSourceFields: Optional[List[str]] = Field(None, description="Поля с координатами")
    source_spatialReference: Optional[int] = Field(None, description="SpatialReference Id.")
    source_isWkt: Optional[bool] = Field(None, description="Геометрия в WKT")


class LayerSourceMixin:
    """Mixin for source type fields."""
    source_layer: Optional[SourceEqlConfig] = Field(None, description="Имя слоя")


class ShapeSourceMixin:
    """Mixin for source type fields."""
    source_fileName: Optional[str] = Field(None, description="Имя файла")
    source_layerName: Optional[str] = Field(None, description="Имя слоя")


class OtherfileSourceMixin:
    """Mixin for source type fields."""
    source_fileName: Optional[str] = Field(None, description="Имя файла")
    source_layerName: Optional[str] = Field(None, description="Имя слоя")


class CsvTargetMixin:
    """Mixin for target type fields."""
    target_fileName: Optional[str] = Field(None, description="Имя файла")
    target_coordSourceFields: Optional[List[str]] = Field(None, description="Поля с координатами")
    target_columnDelimiter: Optional[str] = Field(None, description="Символ разделителя")
    target_spatialReference: Optional[int] = Field(None, description="SpatialReference Id.")
    target_isWkt: Optional[bool] = Field(None, description="Геометрия в WKT")
    target_attributeNameRowNumber: Optional[int] = Field(None, description="AttributeNameRowNumber")
    target_aliasRowNumber: Optional[int] = Field(None, description="AliasRowNumber")
    target_firstDataRowNumber: Optional[int] = Field(None, description="FirstDataRowNumber")


class GpkgTargetMixin:
    """Mixin for target type fields."""
    target_fileName: Optional[str] = Field(None, description="Имя файла")
    target_layerName: Optional[str] = Field(None, description="Имя слоя")


class ExcelTargetMixin:
    """Mixin for target type fields."""
    target_fileName: Optional[str] = Field(None, description="Имя файла")
    target_attributeNameRowNumber: Optional[int] = Field(None, description="AttributeNameRowNumber")
    target_aliasRowNumber: Optional[int] = Field(None, description="AliasRowNumber")
    target_firstDataRowNumber: Optional[int] = Field(None, description="FirstDataRowNumber")
    target_coordSourceFields: Optional[List[str]] = Field(None, description="Поля с координатами")
    target_spatialReference: Optional[int] = Field(None, description="SpatialReference Id.")
    target_isWkt: Optional[bool] = Field(None, description="Геометрия в WKT")


class LayerTargetMixin:
    """Mixin for target type fields."""
    target_layer: Optional[LayerReferenceConfig] = Field(None, description="Имя слоя")
    target_layer_alias: Optional[str] = Field(None, description="Алиас")


class ShapeTargetMixin:
    """Mixin for target type fields."""
    target_fileName: Optional[str] = Field(None, description="Имя файла")
    target_layerName: Optional[str] = Field(None, description="Имя слоя")


class GeojsonTargetMixin:
    """Mixin for target type fields."""
    target_fileName: Optional[str] = Field(None, description="Имя файла")
    target_layerName: Optional[str] = Field(None, description="Имя слоя")


class CsvToCsvStartParameters(BaseImportexportStartParameters, CsvSourceMixin, CsvTargetMixin):
    """StartParameters for csv -> csv combination."""
    source_type: Literal["csv"] = "csv"
    target_type: Literal["csv"] = "csv"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class CsvToGpkgStartParameters(BaseImportexportStartParameters, CsvSourceMixin, GpkgTargetMixin):
    """StartParameters for csv -> gpkg combination."""
    source_type: Literal["csv"] = "csv"
    target_type: Literal["gpkg"] = "gpkg"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class CsvToExcelStartParameters(BaseImportexportStartParameters, CsvSourceMixin, ExcelTargetMixin):
    """StartParameters for csv -> excel combination."""
    source_type: Literal["csv"] = "csv"
    target_type: Literal["excel"] = "excel"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class CsvToLayerStartParameters(BaseImportexportStartParameters, CsvSourceMixin, LayerTargetMixin):
    """StartParameters for csv -> layer combination."""
    source_type: Literal["csv"] = "csv"
    target_type: Literal["layer"] = "layer"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class CsvToShapeStartParameters(BaseImportexportStartParameters, CsvSourceMixin, ShapeTargetMixin):
    """StartParameters for csv -> shape combination."""
    source_type: Literal["csv"] = "csv"
    target_type: Literal["shape"] = "shape"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class CsvToGeojsonStartParameters(BaseImportexportStartParameters, CsvSourceMixin, GeojsonTargetMixin):
    """StartParameters for csv -> geojson combination."""
    source_type: Literal["csv"] = "csv"
    target_type: Literal["geojson"] = "geojson"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class GdbToCsvStartParameters(BaseImportexportStartParameters, GdbSourceMixin, CsvTargetMixin):
    """StartParameters for gdb -> csv combination."""
    source_type: Literal["gdb"] = "gdb"
    target_type: Literal["csv"] = "csv"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class GdbToGpkgStartParameters(BaseImportexportStartParameters, GdbSourceMixin, GpkgTargetMixin):
    """StartParameters for gdb -> gpkg combination."""
    source_type: Literal["gdb"] = "gdb"
    target_type: Literal["gpkg"] = "gpkg"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class GdbToExcelStartParameters(BaseImportexportStartParameters, GdbSourceMixin, ExcelTargetMixin):
    """StartParameters for gdb -> excel combination."""
    source_type: Literal["gdb"] = "gdb"
    target_type: Literal["excel"] = "excel"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class GdbToLayerStartParameters(BaseImportexportStartParameters, GdbSourceMixin, LayerTargetMixin):
    """StartParameters for gdb -> layer combination."""
    source_type: Literal["gdb"] = "gdb"
    target_type: Literal["layer"] = "layer"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class GdbToShapeStartParameters(BaseImportexportStartParameters, GdbSourceMixin, ShapeTargetMixin):
    """StartParameters for gdb -> shape combination."""
    source_type: Literal["gdb"] = "gdb"
    target_type: Literal["shape"] = "shape"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class GdbToGeojsonStartParameters(BaseImportexportStartParameters, GdbSourceMixin, GeojsonTargetMixin):
    """StartParameters for gdb -> geojson combination."""
    source_type: Literal["gdb"] = "gdb"
    target_type: Literal["geojson"] = "geojson"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class KmlToCsvStartParameters(BaseImportexportStartParameters, KmlSourceMixin, CsvTargetMixin):
    """StartParameters for kml -> csv combination."""
    source_type: Literal["kml"] = "kml"
    target_type: Literal["csv"] = "csv"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class KmlToGpkgStartParameters(BaseImportexportStartParameters, KmlSourceMixin, GpkgTargetMixin):
    """StartParameters for kml -> gpkg combination."""
    source_type: Literal["kml"] = "kml"
    target_type: Literal["gpkg"] = "gpkg"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class KmlToExcelStartParameters(BaseImportexportStartParameters, KmlSourceMixin, ExcelTargetMixin):
    """StartParameters for kml -> excel combination."""
    source_type: Literal["kml"] = "kml"
    target_type: Literal["excel"] = "excel"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class KmlToLayerStartParameters(BaseImportexportStartParameters, KmlSourceMixin, LayerTargetMixin):
    """StartParameters for kml -> layer combination."""
    source_type: Literal["kml"] = "kml"
    target_type: Literal["layer"] = "layer"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class KmlToShapeStartParameters(BaseImportexportStartParameters, KmlSourceMixin, ShapeTargetMixin):
    """StartParameters for kml -> shape combination."""
    source_type: Literal["kml"] = "kml"
    target_type: Literal["shape"] = "shape"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class KmlToGeojsonStartParameters(BaseImportexportStartParameters, KmlSourceMixin, GeojsonTargetMixin):
    """StartParameters for kml -> geojson combination."""
    source_type: Literal["kml"] = "kml"
    target_type: Literal["geojson"] = "geojson"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class TabToCsvStartParameters(BaseImportexportStartParameters, TabSourceMixin, CsvTargetMixin):
    """StartParameters for tab -> csv combination."""
    source_type: Literal["tab"] = "tab"
    target_type: Literal["csv"] = "csv"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class TabToGpkgStartParameters(BaseImportexportStartParameters, TabSourceMixin, GpkgTargetMixin):
    """StartParameters for tab -> gpkg combination."""
    source_type: Literal["tab"] = "tab"
    target_type: Literal["gpkg"] = "gpkg"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class TabToExcelStartParameters(BaseImportexportStartParameters, TabSourceMixin, ExcelTargetMixin):
    """StartParameters for tab -> excel combination."""
    source_type: Literal["tab"] = "tab"
    target_type: Literal["excel"] = "excel"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class TabToLayerStartParameters(BaseImportexportStartParameters, TabSourceMixin, LayerTargetMixin):
    """StartParameters for tab -> layer combination."""
    source_type: Literal["tab"] = "tab"
    target_type: Literal["layer"] = "layer"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class TabToShapeStartParameters(BaseImportexportStartParameters, TabSourceMixin, ShapeTargetMixin):
    """StartParameters for tab -> shape combination."""
    source_type: Literal["tab"] = "tab"
    target_type: Literal["shape"] = "shape"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class TabToGeojsonStartParameters(BaseImportexportStartParameters, TabSourceMixin, GeojsonTargetMixin):
    """StartParameters for tab -> geojson combination."""
    source_type: Literal["tab"] = "tab"
    target_type: Literal["geojson"] = "geojson"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class GpkgToCsvStartParameters(BaseImportexportStartParameters, GpkgSourceMixin, CsvTargetMixin):
    """StartParameters for gpkg -> csv combination."""
    source_type: Literal["gpkg"] = "gpkg"
    target_type: Literal["csv"] = "csv"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class GpkgToGpkgStartParameters(BaseImportexportStartParameters, GpkgSourceMixin, GpkgTargetMixin):
    """StartParameters for gpkg -> gpkg combination."""
    source_type: Literal["gpkg"] = "gpkg"
    target_type: Literal["gpkg"] = "gpkg"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class GpkgToExcelStartParameters(BaseImportexportStartParameters, GpkgSourceMixin, ExcelTargetMixin):
    """StartParameters for gpkg -> excel combination."""
    source_type: Literal["gpkg"] = "gpkg"
    target_type: Literal["excel"] = "excel"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class GpkgToLayerStartParameters(BaseImportexportStartParameters, GpkgSourceMixin, LayerTargetMixin):
    """StartParameters for gpkg -> layer combination."""
    source_type: Literal["gpkg"] = "gpkg"
    target_type: Literal["layer"] = "layer"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class GpkgToShapeStartParameters(BaseImportexportStartParameters, GpkgSourceMixin, ShapeTargetMixin):
    """StartParameters for gpkg -> shape combination."""
    source_type: Literal["gpkg"] = "gpkg"
    target_type: Literal["shape"] = "shape"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class GpkgToGeojsonStartParameters(BaseImportexportStartParameters, GpkgSourceMixin, GeojsonTargetMixin):
    """StartParameters for gpkg -> geojson combination."""
    source_type: Literal["gpkg"] = "gpkg"
    target_type: Literal["geojson"] = "geojson"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class ExcelToCsvStartParameters(BaseImportexportStartParameters, ExcelSourceMixin, CsvTargetMixin):
    """StartParameters for excel -> csv combination."""
    source_type: Literal["excel"] = "excel"
    target_type: Literal["csv"] = "csv"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class ExcelToGpkgStartParameters(BaseImportexportStartParameters, ExcelSourceMixin, GpkgTargetMixin):
    """StartParameters for excel -> gpkg combination."""
    source_type: Literal["excel"] = "excel"
    target_type: Literal["gpkg"] = "gpkg"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class ExcelToExcelStartParameters(BaseImportexportStartParameters, ExcelSourceMixin, ExcelTargetMixin):
    """StartParameters for excel -> excel combination."""
    source_type: Literal["excel"] = "excel"
    target_type: Literal["excel"] = "excel"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class ExcelToLayerStartParameters(BaseImportexportStartParameters, ExcelSourceMixin, LayerTargetMixin):
    """StartParameters for excel -> layer combination."""
    source_type: Literal["excel"] = "excel"
    target_type: Literal["layer"] = "layer"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class ExcelToShapeStartParameters(BaseImportexportStartParameters, ExcelSourceMixin, ShapeTargetMixin):
    """StartParameters for excel -> shape combination."""
    source_type: Literal["excel"] = "excel"
    target_type: Literal["shape"] = "shape"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class ExcelToGeojsonStartParameters(BaseImportexportStartParameters, ExcelSourceMixin, GeojsonTargetMixin):
    """StartParameters for excel -> geojson combination."""
    source_type: Literal["excel"] = "excel"
    target_type: Literal["geojson"] = "geojson"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class LayerToCsvStartParameters(BaseImportexportStartParameters, LayerSourceMixin, CsvTargetMixin):
    """StartParameters for layer -> csv combination."""
    source_type: Literal["layer"] = "layer"
    target_type: Literal["csv"] = "csv"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class LayerToGpkgStartParameters(BaseImportexportStartParameters, LayerSourceMixin, GpkgTargetMixin):
    """StartParameters for layer -> gpkg combination."""
    source_type: Literal["layer"] = "layer"
    target_type: Literal["gpkg"] = "gpkg"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class LayerToExcelStartParameters(BaseImportexportStartParameters, LayerSourceMixin, ExcelTargetMixin):
    """StartParameters for layer -> excel combination."""
    source_type: Literal["layer"] = "layer"
    target_type: Literal["excel"] = "excel"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class LayerToLayerStartParameters(BaseImportexportStartParameters, LayerSourceMixin, LayerTargetMixin):
    """StartParameters for layer -> layer combination."""
    source_type: Literal["layer"] = "layer"
    target_type: Literal["layer"] = "layer"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class LayerToShapeStartParameters(BaseImportexportStartParameters, LayerSourceMixin, ShapeTargetMixin):
    """StartParameters for layer -> shape combination."""
    source_type: Literal["layer"] = "layer"
    target_type: Literal["shape"] = "shape"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class LayerToGeojsonStartParameters(BaseImportexportStartParameters, LayerSourceMixin, GeojsonTargetMixin):
    """StartParameters for layer -> geojson combination."""
    source_type: Literal["layer"] = "layer"
    target_type: Literal["geojson"] = "geojson"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class ShapeToCsvStartParameters(BaseImportexportStartParameters, ShapeSourceMixin, CsvTargetMixin):
    """StartParameters for shape -> csv combination."""
    source_type: Literal["shape"] = "shape"
    target_type: Literal["csv"] = "csv"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class ShapeToGpkgStartParameters(BaseImportexportStartParameters, ShapeSourceMixin, GpkgTargetMixin):
    """StartParameters for shape -> gpkg combination."""
    source_type: Literal["shape"] = "shape"
    target_type: Literal["gpkg"] = "gpkg"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class ShapeToExcelStartParameters(BaseImportexportStartParameters, ShapeSourceMixin, ExcelTargetMixin):
    """StartParameters for shape -> excel combination."""
    source_type: Literal["shape"] = "shape"
    target_type: Literal["excel"] = "excel"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class ShapeToLayerStartParameters(BaseImportexportStartParameters, ShapeSourceMixin, LayerTargetMixin):
    """StartParameters for shape -> layer combination."""
    source_type: Literal["shape"] = "shape"
    target_type: Literal["layer"] = "layer"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class ShapeToShapeStartParameters(BaseImportexportStartParameters, ShapeSourceMixin, ShapeTargetMixin):
    """StartParameters for shape -> shape combination."""
    source_type: Literal["shape"] = "shape"
    target_type: Literal["shape"] = "shape"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class ShapeToGeojsonStartParameters(BaseImportexportStartParameters, ShapeSourceMixin, GeojsonTargetMixin):
    """StartParameters for shape -> geojson combination."""
    source_type: Literal["shape"] = "shape"
    target_type: Literal["geojson"] = "geojson"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class OtherfileToCsvStartParameters(BaseImportexportStartParameters, OtherfileSourceMixin, CsvTargetMixin):
    """StartParameters for otherfile -> csv combination."""
    source_type: Literal["otherfile"] = "otherfile"
    target_type: Literal["csv"] = "csv"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class OtherfileToGpkgStartParameters(BaseImportexportStartParameters, OtherfileSourceMixin, GpkgTargetMixin):
    """StartParameters for otherfile -> gpkg combination."""
    source_type: Literal["otherfile"] = "otherfile"
    target_type: Literal["gpkg"] = "gpkg"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class OtherfileToExcelStartParameters(BaseImportexportStartParameters, OtherfileSourceMixin, ExcelTargetMixin):
    """StartParameters for otherfile -> excel combination."""
    source_type: Literal["otherfile"] = "otherfile"
    target_type: Literal["excel"] = "excel"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class OtherfileToLayerStartParameters(BaseImportexportStartParameters, OtherfileSourceMixin, LayerTargetMixin):
    """StartParameters for otherfile -> layer combination."""
    source_type: Literal["otherfile"] = "otherfile"
    target_type: Literal["layer"] = "layer"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class OtherfileToShapeStartParameters(BaseImportexportStartParameters, OtherfileSourceMixin, ShapeTargetMixin):
    """StartParameters for otherfile -> shape combination."""
    source_type: Literal["otherfile"] = "otherfile"
    target_type: Literal["shape"] = "shape"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


class OtherfileToGeojsonStartParameters(BaseImportexportStartParameters, OtherfileSourceMixin, GeojsonTargetMixin):
    """StartParameters for otherfile -> geojson combination."""
    source_type: Literal["otherfile"] = "otherfile"
    target_type: Literal["geojson"] = "geojson"

    # Common fields for all combinations
    attribute_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeMapping', description='Маппинг атрибутов')
    attribute_type_mapping: Optional[Dict[str, Any]] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Dict[str, Any]] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')
    batch_count: Optional[int] = Field(None, alias='batchCount', description='Размер батча для импорта/экспорта')


# Aliases for backward compatibility
ImportexportSourceCsvTargetCsvStartParameters = CsvToCsvStartParameters
ImportexportSourceCsvTargetGpkgStartParameters = CsvToGpkgStartParameters
ImportexportSourceCsvTargetExcelStartParameters = CsvToExcelStartParameters
ImportexportSourceCsvTargetLayerStartParameters = CsvToLayerStartParameters
ImportexportSourceCsvTargetShapeStartParameters = CsvToShapeStartParameters
ImportexportSourceCsvTargetGeojsonStartParameters = CsvToGeojsonStartParameters
ImportexportSourceGdbTargetCsvStartParameters = GdbToCsvStartParameters
ImportexportSourceGdbTargetGpkgStartParameters = GdbToGpkgStartParameters
ImportexportSourceGdbTargetExcelStartParameters = GdbToExcelStartParameters
ImportexportSourceGdbTargetLayerStartParameters = GdbToLayerStartParameters
ImportexportSourceGdbTargetShapeStartParameters = GdbToShapeStartParameters
ImportexportSourceGdbTargetGeojsonStartParameters = GdbToGeojsonStartParameters
ImportexportSourceKmlTargetCsvStartParameters = KmlToCsvStartParameters
ImportexportSourceKmlTargetGpkgStartParameters = KmlToGpkgStartParameters
ImportexportSourceKmlTargetExcelStartParameters = KmlToExcelStartParameters
ImportexportSourceKmlTargetLayerStartParameters = KmlToLayerStartParameters
ImportexportSourceKmlTargetShapeStartParameters = KmlToShapeStartParameters
ImportexportSourceKmlTargetGeojsonStartParameters = KmlToGeojsonStartParameters
ImportexportSourceTabTargetCsvStartParameters = TabToCsvStartParameters
ImportexportSourceTabTargetGpkgStartParameters = TabToGpkgStartParameters
ImportexportSourceTabTargetExcelStartParameters = TabToExcelStartParameters
ImportexportSourceTabTargetLayerStartParameters = TabToLayerStartParameters
ImportexportSourceTabTargetShapeStartParameters = TabToShapeStartParameters
ImportexportSourceTabTargetGeojsonStartParameters = TabToGeojsonStartParameters
ImportexportSourceGpkgTargetCsvStartParameters = GpkgToCsvStartParameters
ImportexportSourceGpkgTargetGpkgStartParameters = GpkgToGpkgStartParameters
ImportexportSourceGpkgTargetExcelStartParameters = GpkgToExcelStartParameters
ImportexportSourceGpkgTargetLayerStartParameters = GpkgToLayerStartParameters
ImportexportSourceGpkgTargetShapeStartParameters = GpkgToShapeStartParameters
ImportexportSourceGpkgTargetGeojsonStartParameters = GpkgToGeojsonStartParameters
ImportexportSourceExcelTargetCsvStartParameters = ExcelToCsvStartParameters
ImportexportSourceExcelTargetGpkgStartParameters = ExcelToGpkgStartParameters
ImportexportSourceExcelTargetExcelStartParameters = ExcelToExcelStartParameters
ImportexportSourceExcelTargetLayerStartParameters = ExcelToLayerStartParameters
ImportexportSourceExcelTargetShapeStartParameters = ExcelToShapeStartParameters
ImportexportSourceExcelTargetGeojsonStartParameters = ExcelToGeojsonStartParameters
ImportexportSourceLayerTargetCsvStartParameters = LayerToCsvStartParameters
ImportexportSourceLayerTargetGpkgStartParameters = LayerToGpkgStartParameters
ImportexportSourceLayerTargetExcelStartParameters = LayerToExcelStartParameters
ImportexportSourceLayerTargetLayerStartParameters = LayerToLayerStartParameters
ImportexportSourceLayerTargetShapeStartParameters = LayerToShapeStartParameters
ImportexportSourceLayerTargetGeojsonStartParameters = LayerToGeojsonStartParameters
ImportexportSourceShapeTargetCsvStartParameters = ShapeToCsvStartParameters
ImportexportSourceShapeTargetGpkgStartParameters = ShapeToGpkgStartParameters
ImportexportSourceShapeTargetExcelStartParameters = ShapeToExcelStartParameters
ImportexportSourceShapeTargetLayerStartParameters = ShapeToLayerStartParameters
ImportexportSourceShapeTargetShapeStartParameters = ShapeToShapeStartParameters
ImportexportSourceShapeTargetGeojsonStartParameters = ShapeToGeojsonStartParameters
ImportexportSourceOtherfileTargetCsvStartParameters = OtherfileToCsvStartParameters
ImportexportSourceOtherfileTargetGpkgStartParameters = OtherfileToGpkgStartParameters
ImportexportSourceOtherfileTargetExcelStartParameters = OtherfileToExcelStartParameters
ImportexportSourceOtherfileTargetLayerStartParameters = OtherfileToLayerStartParameters
ImportexportSourceOtherfileTargetShapeStartParameters = OtherfileToShapeStartParameters
ImportexportSourceOtherfileTargetGeojsonStartParameters = OtherfileToGeojsonStartParameters


ImportexportStartParameters = Union[
    CsvToCsvStartParameters,
    CsvToGpkgStartParameters,
    CsvToExcelStartParameters,
    CsvToLayerStartParameters,
    CsvToShapeStartParameters,
    CsvToGeojsonStartParameters,
    GdbToCsvStartParameters,
    GdbToGpkgStartParameters,
    GdbToExcelStartParameters,
    GdbToLayerStartParameters,
    GdbToShapeStartParameters,
    GdbToGeojsonStartParameters,
    KmlToCsvStartParameters,
    KmlToGpkgStartParameters,
    KmlToExcelStartParameters,
    KmlToLayerStartParameters,
    KmlToShapeStartParameters,
    KmlToGeojsonStartParameters,
    TabToCsvStartParameters,
    TabToGpkgStartParameters,
    TabToExcelStartParameters,
    TabToLayerStartParameters,
    TabToShapeStartParameters,
    TabToGeojsonStartParameters,
    GpkgToCsvStartParameters,
    GpkgToGpkgStartParameters,
    GpkgToExcelStartParameters,
    GpkgToLayerStartParameters,
    GpkgToShapeStartParameters,
    GpkgToGeojsonStartParameters,
    ExcelToCsvStartParameters,
    ExcelToGpkgStartParameters,
    ExcelToExcelStartParameters,
    ExcelToLayerStartParameters,
    ExcelToShapeStartParameters,
    ExcelToGeojsonStartParameters,
    LayerToCsvStartParameters,
    LayerToGpkgStartParameters,
    LayerToExcelStartParameters,
    LayerToLayerStartParameters,
    LayerToShapeStartParameters,
    LayerToGeojsonStartParameters,
    ShapeToCsvStartParameters,
    ShapeToGpkgStartParameters,
    ShapeToExcelStartParameters,
    ShapeToLayerStartParameters,
    ShapeToShapeStartParameters,
    ShapeToGeojsonStartParameters,
    OtherfileToCsvStartParameters,
    OtherfileToGpkgStartParameters,
    OtherfileToExcelStartParameters,
    OtherfileToLayerStartParameters,
    OtherfileToShapeStartParameters,
    OtherfileToGeojsonStartParameters
]


def create_importexport_start_parameters(
    source_type: str,
    target_type: str,
    **kwargs
) -> ImportexportStartParameters:
    """Factory function to create appropriate StartParameters based on types."""

    combination_map = {
        ("csv", "csv"): CsvToCsvStartParameters,
        ("csv", "gpkg"): CsvToGpkgStartParameters,
        ("csv", "excel"): CsvToExcelStartParameters,
        ("csv", "layer"): CsvToLayerStartParameters,
        ("csv", "shape"): CsvToShapeStartParameters,
        ("csv", "geojson"): CsvToGeojsonStartParameters,
        ("gdb", "csv"): GdbToCsvStartParameters,
        ("gdb", "gpkg"): GdbToGpkgStartParameters,
        ("gdb", "excel"): GdbToExcelStartParameters,
        ("gdb", "layer"): GdbToLayerStartParameters,
        ("gdb", "shape"): GdbToShapeStartParameters,
        ("gdb", "geojson"): GdbToGeojsonStartParameters,
        ("kml", "csv"): KmlToCsvStartParameters,
        ("kml", "gpkg"): KmlToGpkgStartParameters,
        ("kml", "excel"): KmlToExcelStartParameters,
        ("kml", "layer"): KmlToLayerStartParameters,
        ("kml", "shape"): KmlToShapeStartParameters,
        ("kml", "geojson"): KmlToGeojsonStartParameters,
        ("tab", "csv"): TabToCsvStartParameters,
        ("tab", "gpkg"): TabToGpkgStartParameters,
        ("tab", "excel"): TabToExcelStartParameters,
        ("tab", "layer"): TabToLayerStartParameters,
        ("tab", "shape"): TabToShapeStartParameters,
        ("tab", "geojson"): TabToGeojsonStartParameters,
        ("gpkg", "csv"): GpkgToCsvStartParameters,
        ("gpkg", "gpkg"): GpkgToGpkgStartParameters,
        ("gpkg", "excel"): GpkgToExcelStartParameters,
        ("gpkg", "layer"): GpkgToLayerStartParameters,
        ("gpkg", "shape"): GpkgToShapeStartParameters,
        ("gpkg", "geojson"): GpkgToGeojsonStartParameters,
        ("excel", "csv"): ExcelToCsvStartParameters,
        ("excel", "gpkg"): ExcelToGpkgStartParameters,
        ("excel", "excel"): ExcelToExcelStartParameters,
        ("excel", "layer"): ExcelToLayerStartParameters,
        ("excel", "shape"): ExcelToShapeStartParameters,
        ("excel", "geojson"): ExcelToGeojsonStartParameters,
        ("layer", "csv"): LayerToCsvStartParameters,
        ("layer", "gpkg"): LayerToGpkgStartParameters,
        ("layer", "excel"): LayerToExcelStartParameters,
        ("layer", "layer"): LayerToLayerStartParameters,
        ("layer", "shape"): LayerToShapeStartParameters,
        ("layer", "geojson"): LayerToGeojsonStartParameters,
        ("shape", "csv"): ShapeToCsvStartParameters,
        ("shape", "gpkg"): ShapeToGpkgStartParameters,
        ("shape", "excel"): ShapeToExcelStartParameters,
        ("shape", "layer"): ShapeToLayerStartParameters,
        ("shape", "shape"): ShapeToShapeStartParameters,
        ("shape", "geojson"): ShapeToGeojsonStartParameters,
        ("otherfile", "csv"): OtherfileToCsvStartParameters,
        ("otherfile", "gpkg"): OtherfileToGpkgStartParameters,
        ("otherfile", "excel"): OtherfileToExcelStartParameters,
        ("otherfile", "layer"): OtherfileToLayerStartParameters,
        ("otherfile", "shape"): OtherfileToShapeStartParameters,
        ("otherfile", "geojson"): OtherfileToGeojsonStartParameters
    }

    model_class = combination_map.get((source_type, target_type))
    if not model_class:
        available = list(combination_map.keys())
        raise ValueError(f"Unsupported combination: {source_type} -> {target_type}. Available: {available}")

    return model_class(**kwargs)


def create_importexport_job(
    source_type: str,
    target_type: str,
    **kwargs
) -> TaskPrototypeDto:
    """Create importExport job with conditional parameters."""

    start_params = create_importexport_start_parameters(
        source_type=source_type,
        target_type=target_type,
        **kwargs
    )

    return create_task_prototype(
        task_type="importExport",
        start_parameters=start_params
    )


__all__ = [
    "BaseImportexportStartParameters",
    "CsvToCsvStartParameters",
    "ImportexportSourceCsvTargetCsvStartParameters",
    "CsvToGpkgStartParameters",
    "ImportexportSourceCsvTargetGpkgStartParameters",
    "CsvToExcelStartParameters",
    "ImportexportSourceCsvTargetExcelStartParameters",
    "CsvToLayerStartParameters",
    "ImportexportSourceCsvTargetLayerStartParameters",
    "CsvToShapeStartParameters",
    "ImportexportSourceCsvTargetShapeStartParameters",
    "CsvToGeojsonStartParameters",
    "ImportexportSourceCsvTargetGeojsonStartParameters",
    "GdbToCsvStartParameters",
    "ImportexportSourceGdbTargetCsvStartParameters",
    "GdbToGpkgStartParameters",
    "ImportexportSourceGdbTargetGpkgStartParameters",
    "GdbToExcelStartParameters",
    "ImportexportSourceGdbTargetExcelStartParameters",
    "GdbToLayerStartParameters",
    "ImportexportSourceGdbTargetLayerStartParameters",
    "GdbToShapeStartParameters",
    "ImportexportSourceGdbTargetShapeStartParameters",
    "GdbToGeojsonStartParameters",
    "ImportexportSourceGdbTargetGeojsonStartParameters",
    "KmlToCsvStartParameters",
    "ImportexportSourceKmlTargetCsvStartParameters",
    "KmlToGpkgStartParameters",
    "ImportexportSourceKmlTargetGpkgStartParameters",
    "KmlToExcelStartParameters",
    "ImportexportSourceKmlTargetExcelStartParameters",
    "KmlToLayerStartParameters",
    "ImportexportSourceKmlTargetLayerStartParameters",
    "KmlToShapeStartParameters",
    "ImportexportSourceKmlTargetShapeStartParameters",
    "KmlToGeojsonStartParameters",
    "ImportexportSourceKmlTargetGeojsonStartParameters",
    "TabToCsvStartParameters",
    "ImportexportSourceTabTargetCsvStartParameters",
    "TabToGpkgStartParameters",
    "ImportexportSourceTabTargetGpkgStartParameters",
    "TabToExcelStartParameters",
    "ImportexportSourceTabTargetExcelStartParameters",
    "TabToLayerStartParameters",
    "ImportexportSourceTabTargetLayerStartParameters",
    "TabToShapeStartParameters",
    "ImportexportSourceTabTargetShapeStartParameters",
    "TabToGeojsonStartParameters",
    "ImportexportSourceTabTargetGeojsonStartParameters",
    "GpkgToCsvStartParameters",
    "ImportexportSourceGpkgTargetCsvStartParameters",
    "GpkgToGpkgStartParameters",
    "ImportexportSourceGpkgTargetGpkgStartParameters",
    "GpkgToExcelStartParameters",
    "ImportexportSourceGpkgTargetExcelStartParameters",
    "GpkgToLayerStartParameters",
    "ImportexportSourceGpkgTargetLayerStartParameters",
    "GpkgToShapeStartParameters",
    "ImportexportSourceGpkgTargetShapeStartParameters",
    "GpkgToGeojsonStartParameters",
    "ImportexportSourceGpkgTargetGeojsonStartParameters",
    "ExcelToCsvStartParameters",
    "ImportexportSourceExcelTargetCsvStartParameters",
    "ExcelToGpkgStartParameters",
    "ImportexportSourceExcelTargetGpkgStartParameters",
    "ExcelToExcelStartParameters",
    "ImportexportSourceExcelTargetExcelStartParameters",
    "ExcelToLayerStartParameters",
    "ImportexportSourceExcelTargetLayerStartParameters",
    "ExcelToShapeStartParameters",
    "ImportexportSourceExcelTargetShapeStartParameters",
    "ExcelToGeojsonStartParameters",
    "ImportexportSourceExcelTargetGeojsonStartParameters",
    "LayerToCsvStartParameters",
    "ImportexportSourceLayerTargetCsvStartParameters",
    "LayerToGpkgStartParameters",
    "ImportexportSourceLayerTargetGpkgStartParameters",
    "LayerToExcelStartParameters",
    "ImportexportSourceLayerTargetExcelStartParameters",
    "LayerToLayerStartParameters",
    "ImportexportSourceLayerTargetLayerStartParameters",
    "LayerToShapeStartParameters",
    "ImportexportSourceLayerTargetShapeStartParameters",
    "LayerToGeojsonStartParameters",
    "ImportexportSourceLayerTargetGeojsonStartParameters",
    "ShapeToCsvStartParameters",
    "ImportexportSourceShapeTargetCsvStartParameters",
    "ShapeToGpkgStartParameters",
    "ImportexportSourceShapeTargetGpkgStartParameters",
    "ShapeToExcelStartParameters",
    "ImportexportSourceShapeTargetExcelStartParameters",
    "ShapeToLayerStartParameters",
    "ImportexportSourceShapeTargetLayerStartParameters",
    "ShapeToShapeStartParameters",
    "ImportexportSourceShapeTargetShapeStartParameters",
    "ShapeToGeojsonStartParameters",
    "ImportexportSourceShapeTargetGeojsonStartParameters",
    "OtherfileToCsvStartParameters",
    "ImportexportSourceOtherfileTargetCsvStartParameters",
    "OtherfileToGpkgStartParameters",
    "ImportexportSourceOtherfileTargetGpkgStartParameters",
    "OtherfileToExcelStartParameters",
    "ImportexportSourceOtherfileTargetExcelStartParameters",
    "OtherfileToLayerStartParameters",
    "ImportexportSourceOtherfileTargetLayerStartParameters",
    "OtherfileToShapeStartParameters",
    "ImportexportSourceOtherfileTargetShapeStartParameters",
    "OtherfileToGeojsonStartParameters",
    "ImportexportSourceOtherfileTargetGeojsonStartParameters",
    "ImportexportStartParameters",
    "create_importexport_start_parameters",
    "create_importexport_job",
]
