from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum

class Permissions(str, Enum):
    NONE = "none"
    CONFIGURE = "configure"
    WRITE = "write"
    READ = "read"
    READ_CONFIGURE = "read,configure"
    READ_WRITE = "read,write"
    READ_WRITE_CONFIGURE = "read,write,configure"


class RolePermissionDc(BaseModel):
    """Roles permission."""

    permissions: 'Permissions'
    role: str = Field(description="Role name.", min_length=1)

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class AccessControlListDc(BaseModel):
    """Access control list for a security object."""

    data: Optional[List['RolePermissionDc']] = Field(default=None, description="All available permissions list.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class AccessMode(str, Enum):
    SHARED = "Shared"
    PUBLIC = "Public"
    MY = "My"


class WorkerSettingsFieldType(str, Enum):
    INT32 = "Int32"
    INT64 = "Int64"
    DOUBLE = "Double"
    STRING = "String"
    BOOLEAN = "Boolean"
    DATETIME = "DateTime"
    POINT = "Point"
    GEOMETRY = "Geometry"
    POLYLINE = "Polyline"
    MULTIPOLYGON = "MultiPolygon"
    POLYGON = "Polygon"
    MULTIPOINT = "Multipoint"
    INTERGERARRAY = "IntergerArray"
    DOUBLEARRAY = "DoubleArray"
    STRINGARRAY = "StringArray"
    SOURCEEQL = "SourceEql"
    LAYER = "Layer"
    TABLE = "Table"
    FOLDER = "Folder"
    JSON = "Json"
    ATTRIBUTE = "Attribute"
    ATTRIBUTEARRAY = "AttributeArray"


class WorkerSettingsFieldDc(BaseModel):
    """public class WorkerSettingsFieldDc."""

    alias: Optional[str] = Field(default=None, description="Alias.")
    childrenFields: Optional[Dict[str, List['WorkerSettingsFieldDc']]] = Field(default=None, description="ChildrenFields.")
    group: Optional[str] = Field(default=None, description="Group.")
    lookupValues: Optional[Dict[str, str]] = Field(default=None, description="LookupValues.")
    name: Optional[str] = Field(default=None, description="Name.")
    nullable: Optional[bool] = Field(default=None, description="Nullable.")
    type: Optional['WorkerSettingsFieldType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class WorkerMethodType(str, Enum):
    TASK = "Task"
    REST = "Rest"
    BOTH = "Both"


class ActiveWorkerTaskDc(BaseModel):
    """Active worker task data contract."""

    jsonSchema: Optional[Any] = Field(default=None, description="JsonSchema.")
    methodCallType: Optional['WorkerMethodType'] = None
    settingsFields: Optional[List['WorkerSettingsFieldDc']] = Field(default=None, description="SettingsFields.")
    type: Optional[str] = Field(default=None, description="Task type.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ActiveWorkerDc(BaseModel):
    """Active worker data contract."""

    activeWorkerTasks: Optional[List['ActiveWorkerTaskDc']] = Field(default=None, description="Worker tasks.")
    id: Optional[UUID] = Field(default=None, description="Идентификатор.")
    isInError: Optional[bool] = Field(default=None, description="IsInError.")
    isInTimeout: Optional[bool] = Field(default=None, description="IsInTimeout.")
    lastUpdateStatusDate: Optional[datetime] = Field(default=None, description="Last update status date.")
    type: Optional[str] = Field(default=None, description="Worker type.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class DataSourceConnectionType(str, Enum):
    JSON = "Json"
    CSV = "Csv"
    ORC = "Orc"
    PARQUET = "Parquet"
    JDBC = "Jdbc"


class AdditionalDataSourceConnectionDc(BaseModel):
    """Additional data source connection data contract."""

    connectionString: Optional[str] = Field(default=None, description="Connection string.")
    name: Optional[str] = Field(default=None, description="Temp view name.")
    type: Optional['DataSourceConnectionType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class AggregationFunction(str, Enum):
    NONE = "None"
    ARRAY = "Array"
    MIN = "Min"
    MAX = "Max"
    AVG = "Avg"
    SUM = "Sum"
    EXTENT = "Extent"
    H3 = "H3"
    COUNT = "Count"
    TOTALCOUNT = "TotalCount"
    DISTINCTCOUNT = "DistinctCount"
    FIRST = "First"
    LAST = "Last"
    MEDIAN = "Median"
    MOD = "Mod"
    STDDEVIATION = "StdDeviation"
    SUMOFPRODUCT = "SumOfProduct"
    ONLYVALUE = "OnlyValue"
    WEIGHTEDAVG = "WeightedAvg"
    DENSITYINDICATORS = "DensityIndicators"
    DIVIDEDSUM = "DividedSum"


class AggregationDataResultDc(BaseModel):
    """Describes data contract of aggregation result."""

    aggregationAttributeName: str = Field(description="Aggregation attribute name.", min_length=1)
    aggregationFunctionName: 'AggregationFunction'
    attributes: Dict[str, Any] = Field(description="Aggregation groups.")
    value: Any = Field(description="Aggregation result value.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class DataSourceType(str, Enum):
    POSTGRES = "Postgres"
    TRINO = "Trino"
    S3 = "S3"
    GISSERVER = "GisServer"
    SPARK = "Spark"
    ARCHIVE = "Archive"


class DataSourceDc(BaseModel):
    """Data source data contract."""

    acl: Optional['AccessControlListDc'] = None
    alias: Optional[str] = Field(default=None, description="Alias.")
    description: Optional[str] = Field(default=None, description="Description.")
    name: Optional[str] = Field(default=None, description="Name.")
    owner: Optional[str] = Field(default=None, description="Login of the owner.")
    parentId: Optional[str] = Field(default=None, description="Parent id.")
    tags: Optional[List[str]] = Field(default=None, description="Tags.")
    type: Optional['DataSourceType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ArcGisDataSourceDc(DataSourceDc):
    """S3 data source settings."""

    headers: Optional[Dict[str, str]] = Field(default=None, description="Endpoint.")
    params: Optional[Dict[str, str]] = Field(default=None, description="Endpoint.")
    serviceUrl: Optional[str] = Field(default=None, description="Endpoint.")
    type: Optional['DataSourceType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class DataSourceInfoDc(BaseModel):
    """Data source info."""

    acl: Optional['AccessControlListDc'] = None
    alias: Optional[str] = Field(default=None, description="Alias.")
    created: Optional[datetime] = Field(default=None, description="Date and time when the remote connection was created.")
    description: Optional[str] = Field(default=None, description="Description.")
    modified: Optional[datetime] = Field(default=None, description="Date and time when the remote connection was last modified.")
    name: Optional[str] = Field(default=None, description="Name.")
    owner: Optional[str] = Field(default=None, description="Login of the owner.")
    parentId: Optional[str] = Field(default=None, description="Parent id.")
    resourceId: Optional[str] = Field(default=None, description="Resource id.")
    tags: Optional[List[str]] = Field(default=None, description="Tags.")
    type: Optional['DataSourceType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ArcGisDataSourceInfoDc(DataSourceInfoDc):
    """S3 data source info."""

    serviceUrl: Optional[str] = Field(default=None, description="Service url.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class AttributeConfigurationType(str, Enum):
    """Attribute configuration type."""

    DEFAULT = "Default"
    STRING = "String"
    GEOMETRY = "Geometry"
    CALCULATED = "Calculated"


class AttributeSelectorType(str, Enum):
    NONE = "None"
    SELECTFROMHANDBOOK = "SelectFromHandBook"
    SELECTFROMRANGE = "SelectFromRange"
    VIEWHANDBOOK = "ViewHandBook"


class AttributeType(str, Enum):
    UNKNOWN = "Unknown"
    STRING = "String"
    INT32 = "Int32"
    INT64 = "Int64"
    DOUBLE = "Double"
    DATETIME = "DateTime"
    BOOLEAN = "Boolean"
    POINT = "Point"
    LINESTRING = "LineString"
    POLYGON = "Polygon"
    MULTIPOINT = "MultiPoint"
    MULTILINESTRING = "MultiLineString"
    H3INDEX = "H3Index"
    JSON = "Json"
    MULTIPOLYGON = "MultiPolygon"
    GEOMETRYCOLLECTION = "GeometryCollection"


class AttributeIconType(str, Enum):
    UNKNOWN = "Unknown"
    ICON = "Icon"
    PNG = "PNG"
    SVG = "SVG"


class AttributeIconDc(BaseModel):
    """Information about an attribute icon."""

    iconName: Optional[str] = Field(default=None, description="Icon name from EverGIS icon library.")
    resourceId: Optional[str] = Field(default=None, description="Icon resource id.")
    type: Optional['AttributeIconType'] = None
    url: Optional[str] = Field(default=None, description="URL.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class AttributeFormatConfigurationDc(BaseModel):
    """Sets attribute format settings."""

    culture: Optional[str] = Field(default=None, description="Set formatting culture. If not set, default culture is Current. Receive formatted value in different culture. Current culture is culture specified by default on machine (en-US, ru-RU). Invariant is culture-independent culture. Specific cultures: ru-RU, en-US. If specific culture has invalid name 400 error returns.")
    format: Optional[str] = Field(default=None, description="Template to format attribute value. Format numeric: http://docs.microsoft.com/en-us/dotnet/standard/base-types/custom-numeric-format-strings . Format date and time: http://docs.microsoft.com/en-us/dotnet/standard/base-types/custom-date-and-time-format-strings . <para></para> <example> `#,#` - Causes value to be split into groups ``` 1234567890 -> 1 234 567 890 ````.00` - Causes the value to be rounded. ``` 123.446 -> 123.45 ````#,#.00` - Causes value to be split into groups and rounded. ``` 1234567.4563 - > 1 234 567.46 ```</example>")
    rounding: Optional[int] = Field(default=None, description="Rounds digit.")
    scalingFactor: Optional[float] = Field(default=None, description="Sets number scaling factor. In case, source value is 1 000 000 and scaling factor is 0.001 formatted value to be in hundred - 1000.")
    splitDigitGroup: Optional[bool] = Field(default=None, description="Split digit in groups.")
    unitsLabel: Optional[str] = Field(default=None, description="Appends text label to value.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class AttributeConfigurationDc(BaseModel):
    """Configuration of an attribute in a feature layer."""

    attributeName: str = Field(description="The name of the attribute.", min_length=1)
    alias: Optional[str] = Field(default=None, description="Human-friendly name for the attribute.")
    attributeConfigurationType: Optional['AttributeConfigurationType'] = None
    attributeSelectorType: Optional['AttributeSelectorType'] = None
    clientData: Optional[Any] = Field(default=None, description="Client data storage. Storage isn't used by server.")
    columnName: Optional[str] = Field(default=None, description="The name of the column in the data table that holds the attribute values.")
    description: Optional[str] = Field(default=None, description="Description for the attribute.")
    icon: Optional['AttributeIconDc'] = None
    isDisplayed: Optional[bool] = Field(default=None, description="If false, attribute will not be returned in feature query.")
    isEditable: Optional[bool] = Field(default=None, description="If set to false, editing of the attribute value will be prohibited.")
    layerReferenceId: Optional[List[str]] = Field(default=None, description="A set of layer references.")
    referenceId: Optional[str] = Field(default=None, description="Id of table given attribute is referenced.")
    stringFormat: Optional['AttributeFormatConfigurationDc'] = None
    type: Optional['AttributeType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class AttributeDistinctDc(BaseModel):
    """Information about an attribute distinct."""

    count: int = Field(description="Count of this attribute value at table.")
    value: str = Field(description="Attribute value.", min_length=1)

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class AttributeDistinctsDc(BaseModel):
    """Information about an attribute distincts."""

    distincts: List['AttributeDistinctDc'] = Field(description="Attribute distincts.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class StringSubType(str, Enum):
    NONE = "None"
    IMAGE = "Image"
    PKKCODE = "PkkCode"
    ATTACHMENTS = "Attachments"


class StringAttributeConfigurationDc(AttributeConfigurationDc):
    """Information about a string attribute."""

    attributeConfigurationType: Optional['AttributeConfigurationType'] = None
    subType: Optional['StringSubType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class OgcGeometryType(str, Enum):
    UNKNOWN = "Unknown"
    POINT = "Point"
    LINESTRING = "LineString"
    POLYGON = "Polygon"
    MULTIPOINT = "MultiPoint"
    MULTILINESTRING = "MultiLineString"
    MULTIPOLYGON = "MultiPolygon"
    GEOMETRYCOLLECTION = "GeometryCollection"
    CIRCULARSTRING = "CircularString"
    COMPOUNDCURVE = "CompoundCurve"
    CURVEPOLYGON = "CurvePolygon"
    MULTICURVE = "MultiCurve"
    MULTISURFACE = "MultiSurface"
    CURVE = "Curve"
    SURFACE = "Surface"
    POLYHEDRALSURFACE = "PolyhedralSurface"
    TIN = "TIN"


class GeometryAttributeConfigurationDc(AttributeConfigurationDc):
    """Information about a string attribute."""

    attributeConfigurationType: Optional['AttributeConfigurationType'] = None
    cellSize: Optional[float] = Field(default=None, description="Size of H3 index grid.")
    geometryType: Optional['OgcGeometryType'] = None
    srId: Optional[int] = Field(default=None, description="Spatial reference identifier type in geometry type column.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class CalculatedAttributeConfigurationDc(AttributeConfigurationDc):
    """Represents the data contract for a calculated attribute configuration, including aggregation and conditional logic settings."""

    aggregation: Optional['AggregationFunction'] = None
    attributeConfigurationType: Optional['AttributeConfigurationType'] = None
    expression: Optional[str] = Field(default=None, description="String condition.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class AttributesConfigurationDc(BaseModel):
    """Configuration of the attribute set in a feature layer."""

    idAttribute: str = Field(description="The name of the attribute that is used for identifying features.", min_length=1)
    attributes: Optional[List[Union['CalculatedAttributeConfigurationDc', 'GeometryAttributeConfigurationDc', 'StringAttributeConfigurationDc', 'AttributeConfigurationDc']]] = Field(default=None, description="Configuration of the attributes of the layer.")
    geometryAttribute: Optional[str] = Field(default=None, description="The name of the attribute that contains the feature geometry.")
    geometryType: Optional['OgcGeometryType'] = None
    isEditable: Optional[bool] = Field(default=None, description="Sets false if the layer is readonly.")
    layerReferences: Optional[Any] = Field(default=None, description="Configuration of layer references. Isn't used by server.")
    orderAttribute: Optional[str] = Field(default=None, description="Name of the attribute that contains the ordering of the feature.")
    srId: Optional[int] = Field(default=None, description="Geometry spatial reference.")
    tableName: Optional[str] = Field(default=None, description="The name of the table in data source service, that contains the data for this layer.")
    titleAttribute: Optional[str] = Field(default=None, description="The name of the attribute that is used for setting feature name (optional).")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class AuthorizationGrant(str, Enum):
    AUTHORIZATION_CODE = "authorization_code"
    REFRESH_TOKEN = "refresh_token"


class ValueDc(BaseModel):
    """Descriptioned value data contract."""

    description: Optional[str] = Field(default=None, description="Description.")
    value: Optional[Any] = Field(default=None, description="Value.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class AvailiableValuesDc(BaseModel):
    """Availiable values data contract."""

    layerName: Optional[str] = Field(default=None, description="Layer name.")
    values: Optional[Dict[str, List['ValueDc']]] = Field(default=None, description="Dictionary of availiable parameters values.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class BaseResourceInfoDc(BaseModel):
    """Represents the base class for resource information data contracts, providing common properties for derived resource types."""

    name: str = Field(description="Name of the resource including its namespaces (names of the service managers that contain this service).", min_length=1)

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ResourceAclDc(BaseModel):
    """Provides resource and its acl."""

    data: List['RolePermissionDc'] = Field(description="All available permissions list.")
    objectName: str = Field(description="Name of the resource to apply acl.", min_length=1)

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class BatchResourcesAclDc(BaseModel):
    """Provides resources with their acl."""

    layers: Optional[List['ResourceAclDc']] = Field(default=None, description="A set of layers acl.")
    projects: Optional[List['ResourceAclDc']] = Field(default=None, description="A set of projects acl.")
    tables: Optional[List['ResourceAclDc']] = Field(default=None, description="A set of tables acl.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


"""The position at the map."""
PositionDc = Tuple[float, float]


class EnvelopeDc(BaseModel):
    """Envelope geometry."""

    coordinates: List['PositionDc'] = Field(description="Coordinates of the envelope. Always has exactly 2 points: left bottom and right top.")
    srId: Optional[int] = Field(default=None, description="Spatial reference id.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class BulkExtentsDc(BaseModel):
    """Get bulk extents data contract."""

    extents: Optional[Dict[str, 'EnvelopeDc']] = Field(default=None, description="Extent per layer.")
    overall: Optional['EnvelopeDc'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class BulkFilteredFeaturesCountDc(BaseModel):
    """Get bulk filtered features count data contract."""

    counts: Optional[Dict[str, int]] = Field(default=None, description="Extent per layer.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class BulkOperationResultDc(BaseModel):
    """Provides set resources bulk operation status."""

    error: Optional[str] = Field(default=None, description="Error while perform operation.")
    isSuccess: Optional[bool] = Field(default=None, description="Sets true.")
    resourceName: Optional[str] = Field(default=None, description="Name of the resource.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class CatalogResourceType(str, Enum):
    DIRECTORY = "Directory"
    MAP = "Map"
    LAYER = "Layer"
    TABLE = "Table"
    FILE = "File"
    TASKPROTOTYPE = "TaskPrototype"
    DATASOURCE = "DataSource"


class CatalogResourceDc(BaseModel):
    """Resource catalog item."""

    acl: Optional['AccessControlListDc'] = None
    contentType: Optional[str] = Field(default=None, description="Content type.")
    createdAt: Optional[datetime] = Field(default=None, description="Created at.")
    description: Optional[str] = Field(default=None, description="Description of the resource.")
    geometryType: Optional['OgcGeometryType'] = None
    icon: Optional[str] = Field(default=None, description="Resource icon.")
    inheritAcl: Optional[bool] = Field(default=None, description="True if acl inherited from parent.")
    isObservable: Optional[bool] = Field(default=None, description="True if resource is observable.")
    isSymlink: Optional[bool] = Field(default=None, description="Check if resource is symlink.")
    isSystem: Optional[bool] = Field(default=None, description="Check if resource is system.")
    isTemporary: Optional[bool] = Field(default=None, description="Check if resource is temporary.")
    name: Optional[str] = Field(default=None, description="Path to the resource.")
    owner: Optional[str] = Field(default=None, description="Owner of the resource.")
    parentId: Optional[str] = Field(default=None, description="Parent resource id.")
    permissions: Optional['Permissions'] = None
    preview: Optional[str] = Field(default=None, description="Preview.")
    resourceId: Optional[str] = Field(default=None, description="Resource id.")
    schema_: Optional[str] = Field(default=None, alias="schema", description="Table schema.")
    size: Optional[int] = Field(default=None, description="Resource size.")
    srid: Optional[int] = Field(default=None, description="Spatial reference id. Nothing if geometry type is mixed.")
    subtype: Optional[str] = Field(default=None, description="Resource subtype.")
    systemName: Optional[str] = Field(default=None, description="System name.")
    tags: Optional[List[str]] = Field(default=None, description="Resource tags.")
    targetResourceId: Optional[str] = Field(default=None, description="Resource id.")
    type: Optional['CatalogResourceType'] = None
    updatedAt: Optional[datetime] = Field(default=None, description="Updated at.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ClassificationType(str, Enum):
    NONE = "none"
    NATURALBREAKS = "naturalBreaks"
    EQUALINTERVAL = "equalInterval"
    QUANTILE = "quantile"
    UNIQUE = "unique"
    STEP = "step"


class ClassifyAttributeType(str, Enum):
    DECIMAL = "decimal"
    DATETIME = "dateTime"
    TEXT = "text"


class ClassifyResult_Object(BaseModel):
    """Classification result."""

    count: Optional[Any] = Field(default=None, description="Count.")
    value: Optional[Any] = Field(default=None, description="Value.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ClassifyDc(BaseModel):
    """Classification result."""

    classifyResult: List[Any] = Field(description="Classification result.")
    type: str = Field(description="Type.", min_length=1)

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class TileGeometryClippingInfoDc(BaseModel):
    """Tile geometry clipping information data contract."""

    buffer: Optional[int] = Field(default=None, description="Buffer size in tile coordinate space for geometry clippig. Defaults to 256.")
    clipGeometry: Optional[bool] = Field(default=None, description="Control if geometries are clipped or encoded as-is. Defaults to true.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ClippingInfoDc(BaseModel):
    """Tile geometry clipping configuration data contract."""

    scaleItems: Optional[Dict[str, 'TileGeometryClippingInfoDc']] = Field(default=None, description="Tile geometry clipping configuration information by scale.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ColumnDescriptionDc(BaseModel):
    """Description of a table column."""

    name: str = Field(description="Column name.", min_length=1)
    type: 'AttributeType'
    defaultValue: Optional[Any] = Field(default=None, description="Default value, if column is not nullable.")
    hasIndex: Optional[bool] = Field(default=None, description="If sets true, index will be configured.")
    maxLength: Optional[int] = Field(default=None, description="Columns value max length.")
    srId: Optional[int] = Field(default=None, description="Spatial reference identifier type in geometry type column.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ConfigDc(BaseModel):
    """Get configuration information."""

    description: Optional[str] = Field(default=None, description="Gets or sets config description.")
    urlPath: Optional[str] = Field(default=None, description="Gets or sets config url path.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ConflictResolutionStrategy(str, Enum):
    SKIP = "Skip"
    OVERWRITE = "Overwrite"
    GENERATEUNIQUE = "GenerateUnique"
    THROWERROR = "ThrowError"


class ConnectRequestDc(BaseModel):
    """DTO for connection request containing resource connection parameters."""

    accessToken: str = Field(description="Gets or sets the access token for authentication with the repository.")
    repositoryUrl: str = Field(description="Gets or sets the URL of the repository containing the resource.")
    resourceId: str = Field(description="Gets or sets the unique identifier of the resource to connect to.")
    branch: Optional[str] = Field(default=None, description="Gets or sets the optional branch name to use for the repository connection.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ConnectResponseDc(BaseModel):
    """DTO for connection response containing resource connection parameters."""

    branch: Optional[str] = Field(default=None, description="The branch that was connected to.")
    connectedAt: Optional[datetime] = Field(default=None, description="The timestamp when the connection was established.")
    lastCommitSha: Optional[str] = Field(default=None, description="The SHA of the last commit in the connected branch.")
    name: Optional[str] = Field(default=None, description="The name of the storage/repository.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ResourceType(str, Enum):
    UNKNOWN = "Unknown"
    TABLE = "table"
    LAYER = "layer"
    PROJECT = "project"
    FILE = "file"
    FEATURE = "feature"
    TAG = "tag"
    DATASOURCE = "datasource"


class CopyResourceDc(BaseModel):
    """Describes resource to copy."""

    copyAlias: str = Field(description="Resource copy alias.", min_length=1)
    copyName: str = Field(description="Resource copy name.", min_length=1)
    name: str = Field(description="Name of resource to copy.", min_length=1)
    type: 'ResourceType'
    copyDescription: Optional[str] = Field(default=None, description="Resource copy description.")
    copyWith: Optional[List[str]] = Field(default=None, description="Resource's dependencies to copy with.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ErrorDetailsType(str, Enum):
    """Type of the error."""

    RESOURCELIMITEXCEEDED = "ResourceLimitExceeded"
    RESOURCENOTFOUND = "ResourceNotFound"
    INTERNALERROR = "InternalError"
    BADREQUEST = "BadRequest"
    DUPLICATECONTENT = "DuplicateContent"


class ErrorDetailsDc(BaseModel):
    """Resource error details."""

    errorType: Optional['ErrorDetailsType'] = None
    message: Optional[str] = Field(default=None, description="Error message.")
    statusCode: Optional[int] = Field(default=None, description="Copy resource status code.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class CopyResourceResultDc(BaseModel):
    """Describes copy operation result data contract."""

    name: str = Field(description="Name of the resource.", min_length=1)
    type: 'ResourceType'
    copiedResources: Optional[List[str]] = Field(default=None, description="Copied resources.")
    copyName: Optional[str] = Field(default=None, description="Name of resource to copy.")
    errorDetails: Optional['ErrorDetailsDc'] = None
    isSuccess: Optional[bool] = Field(default=None, description="Sets true if copy operation success.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class CreateDirectoryDc(BaseModel):
    """Create directory request."""

    description: Optional[str] = Field(default=None, description="Description of the directory.")
    icon: Optional[str] = Field(default=None, description="Resource icon.")
    inheritAcl: Optional[bool] = Field(default=None, description="True if acl inherited from parent.")
    isSystem: Optional[bool] = Field(default=None, description="Check if resource is system.")
    isTemporary: Optional[bool] = Field(default=None, description="If true root folder will create as temporary.")
    name: Optional[str] = Field(default=None, description="Path to the directory.")
    owner: Optional[str] = Field(default=None, description="Owner.")
    parentId: Optional[str] = Field(default=None, description="Parent resource id.")
    rewrite: Optional[bool] = Field(default=None, description="Rewrite if exists.")
    tags: Optional[List[str]] = Field(default=None, description="A set of tags.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class CreateRoleDc(BaseModel):
    """Data contract for create new role."""

    name: str = Field(description="Role name.", min_length=1)
    alias: Optional[str] = Field(default=None, description="Alias.")
    description: Optional[str] = Field(default=None, description="Description.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class CreateSymbolCategoryDc(BaseModel):
    """Symbol category data contract."""

    name: Optional[str] = Field(default=None, description="Name.")
    parentId: Optional[int] = Field(default=None, description="Parent category id.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class CreateSymbolDc(BaseModel):
    """Symbols."""

    categoryId: Optional[int] = Field(default=None, description="Symbol category id.")
    data: Optional[str] = Field(default=None, description="Symbol data.")
    form: Optional[bool] = Field(default=None, description="Is substrate symbol.")
    geometryType: Optional[str] = Field(default=None, description="Symbol geometry type.")
    name: Optional[str] = Field(default=None, description="Symbol name.")
    type: Optional[str] = Field(default=None, description="Symbol type.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class CreateSymlinkDc(BaseModel):
    """Create symlink."""

    name: str = Field(description="Symlink name.")
    targetResourceId: str = Field(description="Target resource.")
    description: Optional[str] = Field(default=None, description="Description of the file.")
    inheritAcl: Optional[bool] = Field(default=None, description="True if acl inherited from parent.")
    parentId: Optional[str] = Field(default=None, description="Parent resource id.")
    systemName: Optional[str] = Field(default=None, description="System name.")
    tags: Optional[List[str]] = Field(default=None, description="A set of tags.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class CreateUserDc(BaseModel):
    """Data contract for create new user."""

    company: Optional[str] = Field(default=None, description="Gets or sets company.")
    email: Optional[str] = Field(default=None, description="Email.")
    emoji: Optional[str] = Field(default=None, description="Emoji.")
    first_name: Optional[str] = Field(default=None, description="First name.")
    goals: Optional[str] = Field(default=None, description="Additional information or goals.")
    is_active: Optional[bool] = Field(default=None, description="Is active.")
    is_email_confirmed: Optional[bool] = Field(default=None, description="Is active.")
    is_open_last_project: Optional[bool] = Field(default=None, description="Whether to open the last used project when opening a client.")
    is_subscribed: Optional[bool] = Field(default=None, description="Has newsletter subscription.")
    last_name: Optional[str] = Field(default=None, description="Last name.")
    namespace: Optional[str] = Field(default=None, description="Namespace.")
    password: Optional[str] = Field(default=None, description="Password.")
    patronymic: Optional[str] = Field(default=None, description="Patronymic.")
    phone: Optional[str] = Field(default=None, description="Phone number.")
    username: Optional[str] = Field(default=None, description="Username.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class CreateViewFromQueryDc(BaseModel):
    """Create view from query data contract."""

    addGidColumn: Optional[bool] = Field(default=None, description="Add gid column.")
    dropCascade: Optional[bool] = Field(default=None, description="Drop overriding view cascade.")
    eql: Optional[str] = Field(default=None, description="Layer name.")
    gidColumnName: Optional[str] = Field(default=None, description="Gid column name.")
    isMaterialized: Optional[bool] = Field(default=None, description="Is view materialized.")
    override: Optional[bool] = Field(default=None, description="Recreate view if exists.")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="EQL query parameters.")
    viewName: Optional[str] = Field(default=None, description="View name.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class CreateViewFromQueryLayerDc(BaseModel):
    """Create view from query layer data contract."""

    addGidColumn: Optional[bool] = Field(default=None, description="Add gid column.")
    conditions: Optional[List[str]] = Field(default=None, description="Collection of filtering conditions.")
    dataFilterId: Optional[str] = Field(default=None, description="Id of override data filter to apply to the layer.")
    dropCascade: Optional[bool] = Field(default=None, description="Drop overriding view cascade.")
    gidColumnName: Optional[str] = Field(default=None, description="Gid column name.")
    isMaterialized: Optional[bool] = Field(default=None, description="Is view materialized.")
    layerName: Optional[str] = Field(default=None, description="Layer name.")
    override: Optional[bool] = Field(default=None, description="Recreate view if exists.")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters.")
    viewName: Optional[str] = Field(default=None, description="View name.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class CreatedTaskResultDto(BaseModel):
    """Created task result."""

    id: Optional[UUID] = Field(default=None, description="Id.")
    success: Optional[bool] = Field(default=None, description="Success flag.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class TableConfigurationType(str, Enum):
    """Specifies the available types of table configurations that can be used within the application."""

    DEFAULTTABLECONFIGURATION = "DefaultTableConfiguration"
    TILECATALOGTABLECONFIGURATION = "TileCatalogTableConfiguration"
    VIEWCONFIGURATION = "ViewConfiguration"
    MATERIALIZEDVIEWCONFIGURATION = "MaterializedViewConfiguration"
    ROUTETABLECONFIGURATION = "RouteTableConfiguration"


class TableConfigurationBaseDc(BaseModel):
    """Common fields for table configurations."""

    type: 'TableConfigurationType'

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class DefaultTableConfigurationDc(TableConfigurationBaseDc):
    """Configuration of a table for feature layer."""

    dataProvider: Optional[str] = Field(default=None, description="Remote data provider name.")
    schemaName: Optional[str] = Field(default=None, description="Schema name.")
    tableName: Optional[str] = Field(default=None, description="Table name.")
    type: Optional['TableConfigurationType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class DependentResourceDc(BaseModel):
    """Dependent resource description."""

    name: str = Field(description="Name of resource.", min_length=1)
    type: str = Field(description="Type of resource.", min_length=1)

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class RouteTableConfigurationDc(TableConfigurationBaseDc):
    """RouteTableConfigurationDc."""

    type: Optional['TableConfigurationType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class MaterializedViewConfigurationDc(TableConfigurationBaseDc):
    """Configuration of a table for feature layer."""

    eql: Optional[str] = Field(default=None, description="EQL.")
    eqlParameters: Optional[Dict[str, Any]] = Field(default=None, description="EQL parameters.")
    schemaName: Optional[str] = Field(default=None, description="Schema.")
    tableName: Optional[str] = Field(default=None, description="TableName.")
    type: Optional['TableConfigurationType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class TileCatalogTableConfigurationDc(TableConfigurationBaseDc):
    """Configuration of a table for tile catalog layer."""

    type: Optional['TableConfigurationType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ViewConfigurationDc(TableConfigurationBaseDc):
    """Configuration of a table for feature layer."""

    eql: Optional[str] = Field(default=None, description="EQL.")
    eqlParameters: Optional[Dict[str, Any]] = Field(default=None, description="EQL parameters.")
    schemaName: Optional[str] = Field(default=None, description="Schema.")
    tableName: Optional[str] = Field(default=None, description="TableName.")
    type: Optional['TableConfigurationType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class TableInfoDc(BaseModel):
    """Table description."""

    name: str = Field(description="Name of the resource including its namespaces (names of the service managers that contain this service).", min_length=1)
    acl: Optional['AccessControlListDc'] = None
    alias: Optional[str] = Field(default=None, description="Resource alias.")
    changedDate: Optional[datetime] = Field(default=None, description="The date when resource was last modified.")
    configuration: Optional[Union['DefaultTableConfigurationDc', 'MaterializedViewConfigurationDc', 'RouteTableConfigurationDc', 'TileCatalogTableConfigurationDc', 'ViewConfigurationDc']] = Field(default=None, description="Configuration of the table.")
    createdDate: Optional[datetime] = Field(default=None, description="The date when resource was created.")
    description: Optional[str] = Field(default=None, description="Resource description.")
    geometries: Optional[List['OgcGeometryType']] = Field(default=None, description="The geometry of the table.")
    icon: Optional[str] = Field(default=None, description="Base64 encoded image - icon of the resource. Usually shown next to the resource name in lists and legends.", min_length=0, max_length=102400)
    owner: Optional[str] = Field(default=None, description="Resource owner.")
    parentId: Optional[str] = Field(default=None, description="Parent id in resources catalog.")
    permissions: Optional['Permissions'] = None
    resourceId: Optional[str] = Field(default=None, description="Resource id in resources catalog.")
    systemName: Optional[str] = Field(default=None, description="System table name.")
    tags: Optional[List[str]] = Field(default=None, description="Resource tags.")
    type: Optional[str] = Field(default=None, description="The type of the table.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class DetailedTableInfoDc(TableInfoDc):
    """Table description with columns and access control list."""

    columns: Optional[List['ColumnDescriptionDc']] = Field(default=None, description="Description of table columns.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


"""Object identifier"""
ObjectId = int


class EditAttributesInfoDc(BaseModel):
    """Provides attributes edit info."""

    attribute: str = Field(description="Attribute name to edit.", min_length=1)
    editExpression: str = Field(description="Expression to edit.", min_length=1)
    ids: List['ObjectId'] = Field(description="A set of features ids.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class EqlTableDependencyDc(BaseModel):
    """Table dependency data contract."""

    alias: Optional[str] = Field(default=None, description="Alias.")
    name: Optional[str] = Field(default=None, description="Name.")
    schema_: Optional[str] = Field(default=None, alias="schema", description="Schema.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class EqlCteDependencyDc(BaseModel):
    """CTE dependency."""

    name: Optional[str] = Field(default=None, description="Name.")
    tables: Optional[List['EqlTableDependencyDc']] = Field(default=None, description="Tables dependencies.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class EqlDependenciesDc(BaseModel):
    """EQL dependencies."""

    ctes: Optional[List['EqlCteDependencyDc']] = Field(default=None, description="CTE dependencies.")
    tables: Optional[List['EqlTableDependencyDc']] = Field(default=None, description="Tables dependencies.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class EqlRequestDc(BaseModel):
    """EQL requst data contract."""

    query: str = Field(description="EQL query string.", min_length=1)
    additionalDsConnections: Optional[List['AdditionalDataSourceConnectionDc']] = Field(default=None, description="Additional data source connection.")
    columns: Optional[Dict[str, str]] = Field(default=None, description="Columns.")
    ds: Optional[str] = Field(default=None, description="Data source name.")
    geometryField: Optional[str] = Field(default=None, description="Geometry field name.")
    idField: Optional[str] = Field(default=None, description="Id field name.")
    limit: Optional[int] = Field(default=None, description="Limit.")
    offset: Optional[int] = Field(default=None, description="Offset.")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="EQL query parameters.")
    withgeom: Optional[bool] = Field(default=None, description="With geometry.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class EqlResourceReferenceDc(BaseModel):
    """Eql resource reference."""

    name: Optional[str] = Field(default=None, description="Resource name.")
    type: Optional[str] = Field(default=None, description="Resource type.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class EqlResourceReferencesDc(BaseModel):
    """Eql resource references."""

    references: Optional[List['EqlResourceReferenceDc']] = Field(default=None, description="Resources references.")
    tables: Optional[List['EqlTableDependencyDc']] = Field(default=None, description="Tables dependencies.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ExpressionValidationResultDc(BaseModel):
    """Result of the eql expression validation."""

    errors: Optional[List[str]] = Field(default=None, description="If not valid, this field will contain the list of errors in the expression.")
    expression: Optional[str] = Field(default=None, description="The expression that was validated.")
    isValid: Optional[bool] = Field(default=None, description="True if the expression is valid and can be executed on the given layer.")
    returnType: Optional['AttributeType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ExtendedCatalogResourceDc(BaseModel):
    """Extended resource info."""

    acl: Optional['AccessControlListDc'] = None
    contentType: Optional[str] = Field(default=None, description="Content type.")
    createdAt: Optional[datetime] = Field(default=None, description="Created at.")
    description: Optional[str] = Field(default=None, description="Description of the resource.")
    geometryType: Optional['OgcGeometryType'] = None
    icon: Optional[str] = Field(default=None, description="Resource icon.")
    inheritAcl: Optional[bool] = Field(default=None, description="True if acl inherited from parent.")
    isObservable: Optional[bool] = Field(default=None, description="True if resource is observable.")
    isSymlink: Optional[bool] = Field(default=None, description="Check if resource is symlink.")
    isSystem: Optional[bool] = Field(default=None, description="Check if resource is system.")
    isTemporary: Optional[bool] = Field(default=None, description="Check if resource is temporary.")
    name: Optional[str] = Field(default=None, description="Path to the resource.")
    owner: Optional[str] = Field(default=None, description="Owner of the resource.")
    parentId: Optional[str] = Field(default=None, description="Parent resource id.")
    path: Optional[str] = Field(default=None, description="Resource path.")
    permissions: Optional['Permissions'] = None
    preview: Optional[str] = Field(default=None, description="Preview.")
    resourceId: Optional[str] = Field(default=None, description="Resource id.")
    schema_: Optional[str] = Field(default=None, alias="schema", description="Table schema.")
    size: Optional[int] = Field(default=None, description="Resource size.")
    srid: Optional[int] = Field(default=None, description="Spatial reference id. Nothing if geometry type is mixed.")
    subtype: Optional[str] = Field(default=None, description="Resource subtype.")
    systemName: Optional[str] = Field(default=None, description="System name.")
    tags: Optional[List[str]] = Field(default=None, description="Resource tags.")
    targetResourceId: Optional[str] = Field(default=None, description="Resource id.")
    type: Optional['CatalogResourceType'] = None
    updatedAt: Optional[datetime] = Field(default=None, description="Updated at.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ResourceInfoDc(BaseModel):
    """The `ResourceInfoDc` provides information about resource."""

    name: str = Field(description="Name of the resource including its namespaces (names of the service managers that contain this service).", min_length=1)
    acl: Optional['AccessControlListDc'] = None
    alias: Optional[str] = Field(default=None, description="Resource alias.")
    changedDate: Optional[datetime] = Field(default=None, description="The date when resource was last modified.")
    createdDate: Optional[datetime] = Field(default=None, description="The date when resource was created.")
    description: Optional[str] = Field(default=None, description="Resource description.")
    icon: Optional[str] = Field(default=None, description="Base64 encoded image - icon of the resource. Usually shown next to the resource name in lists and legends.", min_length=0, max_length=102400)
    owner: Optional[str] = Field(default=None, description="Resource owner.")
    parentId: Optional[str] = Field(default=None, description="Parent id in resources catalog.")
    permissions: Optional['Permissions'] = None
    resourceId: Optional[str] = Field(default=None, description="Resource id in resources catalog.")
    tags: Optional[List[str]] = Field(default=None, description="Resource tags.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ProjectContentItemDc(BaseModel):
    """Project item description."""

    alias: Optional[str] = Field(default=None, description="Client data storage. Storage isn't used by server.")
    children: Optional[List['ProjectContentItemDc']] = Field(default=None, description="Children items.")
    clientData: Optional[Any] = Field(default=None, description="Specifies name of the item in project.")
    isBasemap: Optional[bool] = Field(default=None, description="If set true, item is basemap.")
    isExpanded: Optional[bool] = Field(default=None, description="Checks if list of children is expanded.")
    isLegendExpanded: Optional[bool] = Field(default=None, description="Checks if legend is expanded.")
    isVisible: Optional[bool] = Field(default=None, description="Indicates if item is visible.")
    layerType: Optional[str] = Field(default=None, description="Layer type.")
    maxScale: Optional[float] = Field(default=None, description="Maximum scale resolution.")
    minScale: Optional[float] = Field(default=None, description="Minimum scale resolution.")
    name: Optional[str] = Field(default=None, description="Item name.")
    opacity: Optional[float] = Field(default=None, description="Opacity level of item.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ProjectConfigurationDc(BaseModel):
    """Project content configuration data contract."""

    clientData: Optional[Any] = Field(default=None, description="Client data storage. Expecting not used by server.")
    config: Optional[Any] = Field(default=None, description="Project configuration.")
    dashboardConfiguration: Optional[Any] = Field(default=None, description="Card configuration. Storage isn't used by server.")
    devConfiguration: Optional[Any] = Field(default=None, description="Developer configuration.")
    editConfiguration: Optional[Any] = Field(default=None, description="Edit configuration. Storage isn't used by server.")
    items: Optional[List['ProjectContentItemDc']] = Field(default=None, description="Project content items configurations.")
    projectInfo: Optional[Any] = Field(default=None, description="Project information. Storage isn't used by server.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ExtendedProjectInfoDc(ResourceInfoDc):
    """Project extended configuration data contract."""

    content: 'ProjectConfigurationDc'

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ProjectConfigurationDcV2(BaseModel):
    """Project content configuration data contract."""

    clientData: Optional[Any] = Field(default=None, description="Client data storage. Expecting not used by server.")
    config: Optional[Any] = Field(default=None, description="Project configuration.")
    dashboardConfiguration: Optional[Any] = Field(default=None, description="Card configuration. Storage isn't used by server.")
    devConfiguration: Optional[Any] = Field(default=None, description="Developer configuration.")
    editConfiguration: Optional[Any] = Field(default=None, description="Edit configuration. Storage isn't used by server.")
    projectInfo: Optional[Any] = Field(default=None, description="Project information. Storage isn't used by server.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ResourceInfoDcV2(BaseModel):
    """The `ResourceInfoDc` provides information about resource."""

    name: str = Field(description="Name of the resource including its namespaces (names of the service managers that contain this service).", min_length=1)
    alias: Optional[str] = Field(default=None, description="Resource alias.")
    changedDate: Optional[datetime] = Field(default=None, description="The date when resource was last modified.")
    createdDate: Optional[datetime] = Field(default=None, description="The date when resource was created.")
    description: Optional[str] = Field(default=None, description="Resource description.")
    icon: Optional[str] = Field(default=None, description="Base64 encoded image - icon of the resource. Usually shown next to the resource name in lists and legends.", min_length=0, max_length=102400)
    owner: Optional[str] = Field(default=None, description="Resource owner.")
    parentId: Optional[str] = Field(default=None, description="Parent id in resources catalog.")
    permissions: Optional['Permissions'] = None
    resourceId: Optional[str] = Field(default=None, description="Resource id in resources catalog.")
    tags: Optional[List[str]] = Field(default=None, description="Resource tags.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ProjectInfoDcV2(ResourceInfoDcV2):
    """A project configuration data contract."""

    pass

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ExtendedProjectInfoDcV2(ProjectInfoDcV2):
    """Project extended configuration data contract."""

    content: 'ProjectConfigurationDcV2'

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ServiceListItemDc(BaseModel):
    """An entry in the service list response."""

    alias: Optional[str] = Field(default=None, description="Alias of the resource.")
    changedDate: Optional[datetime] = Field(default=None, description="The date and time the resource was modified the last time.")
    condition: Optional[str] = Field(default=None, description="Filtering condition for the objects in the service. If no condition set or if no such property is available for the given service type, null is returned.")
    createdDate: Optional[datetime] = Field(default=None, description="The date and time the resource was created.")
    dataSourceType: Optional[str] = Field(default=None, description="Provides data source type info.")
    description: Optional[str] = Field(default=None, description="Description of the resource.")
    envelope: Optional['EnvelopeDc'] = None
    geometryType: Optional['OgcGeometryType'] = None
    maxResolution: Optional[float] = Field(default=None, description="Maximum resolution that this service will be rendered on. If no resolution limits are set for the top-level style of the service, or if no such property is available for this type of the service, 0 is returned.")
    minResolution: Optional[float] = Field(default=None, description="Minimum resolution that this service will be rendered on. If no resolution limits are set for the top-level style of the service, or if no such property is available for this type of the service, 0 is returned.")
    name: Optional[str] = Field(default=None, description="Name of the resource.")
    owner: Optional[str] = Field(default=None, description="System name of the resource owner.")
    ownerName: Optional[str] = Field(default=None, description="User name of the resource owner (human friendly name).")
    permissions: Optional['Permissions'] = None
    tags: Optional[List[str]] = Field(default=None, description="A set of tags.")
    type: Optional[str] = Field(default=None, description="Type of the service.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ExtendedProjectLayersInfo(BaseModel):
    """SPCore.Connectors.Connectors.Base.Models.Projects.ExtendedProjectLayersInfo provides extended project info with included layers info."""

    layersInfo: Optional[List['ServiceListItemDc']] = Field(default=None, description="A collection of layers info.")
    projectInfo: Optional['ExtendedProjectInfoDc'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class SocialNetworkInfoDc(BaseModel):
    """User social network information."""

    providerName: Optional[str] = Field(default=None, description="External provider name.")
    userId: Optional[str] = Field(default=None, description="External user identificator.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ExtendedUserInfoDc(BaseModel):
    """Extended user information."""

    company: Optional[str] = Field(default=None, description="Company.")
    dtCreate: Optional[datetime] = Field(default=None, description="Gets or sets date and time of creation.")
    dtLastLogin: Optional[datetime] = Field(default=None, description="Gets or sets date and time of last log in.")
    dtModify: Optional[datetime] = Field(default=None, description="Gets or sets date and time of last modifing.")
    email: Optional[str] = Field(default=None, description="Email.")
    emoji: Optional[str] = Field(default=None, description="Gets or sets emoji.")
    first_name: Optional[str] = Field(default=None, description="First name.")
    has_profile_photo: Optional[bool] = Field(default=None, description="Photo.")
    idModifyUser: Optional[int] = Field(default=None, description="Gets or sets id of modified user.")
    is_active: Optional[bool] = Field(default=None, description="If the user account is active or not.")
    is_email_confirmed: Optional[bool] = Field(default=None, description="Is email confirmed.")
    is_open_last_project: Optional[bool] = Field(default=None, description="Whether to open the last used project when opening a client.")
    is_password_set: Optional[bool] = Field(default=None, description="Is password set.")
    is_subscribed: Optional[bool] = Field(default=None, description="Has newsletter subscription.")
    last_name: Optional[str] = Field(default=None, description="Last name.")
    location: Optional[str] = Field(default=None, description="Location.")
    namespace: Optional[str] = Field(default=None, description="Namespace.")
    patronymic: Optional[str] = Field(default=None, description="Patronymic.")
    phone: Optional[str] = Field(default=None, description="Phone number.")
    pk: Optional[int] = Field(default=None, description="Primary key.")
    position: Optional[str] = Field(default=None, description="Position.")
    roles: Optional[List[str]] = Field(default=None, description="The roles of the user.")
    social: Optional[List['SocialNetworkInfoDc']] = Field(default=None, description="Information about connected social networks.")
    username: Optional[str] = Field(default=None, description="Username.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ExternalLayerInfoDc(BaseModel):
    """External layer information."""

    abstract: Optional[str] = Field(default=None, description="Abstract.")
    layer: Optional[List['ExternalLayerInfoDc']] = Field(default=None, description="Child layers.")
    name: Optional[str] = Field(default=None, description="Name.")
    title: Optional[str] = Field(default=None, description="Title.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class FailedServiceInfoDc(BaseResourceInfoDc):
    """The `FailedServiceInfoDc` describes Everpoint.Sdk.Layers.Abstractions.Models.FailedServiceInfo data contact."""

    error: Optional[str] = Field(default=None, description="Type of error that occurred during initialization.")
    errorType: Optional[str] = Field(default=None, description="Type of error that occurred during initialization.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class GeometryDc(BaseModel):
    """Geometry data contract."""

    type: 'OgcGeometryType'
    srId: Optional[int] = Field(default=None, description="Spatial reference id.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PolygonDc(GeometryDc):
    """Polygon geometry object definition."""

    coordinates: List[List['PositionDc']] = Field(description="Polygon coordinates.")
    type: Optional['OgcGeometryType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PointDc(GeometryDc):
    """Spatial point geometry object representation."""

    coordinates: 'PositionDc'
    type: Optional['OgcGeometryType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class MultiPolygonDc(GeometryDc):
    """Multipoint geometry object definition."""

    coordinates: List[List[List['PositionDc']]] = Field(description="Multipoint coordinates.")
    type: Optional['OgcGeometryType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class MultiPointDc(GeometryDc):
    """Multipoint geometry object definition."""

    coordinates: List['PositionDc'] = Field(description="Multipoint coordinates.")
    type: Optional['OgcGeometryType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class MultiLineStringDc(GeometryDc):
    """MultiLineString geometry object definition."""

    coordinates: List[List['PositionDc']] = Field(description="Poly coordinates.")
    type: Optional['OgcGeometryType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class LineStringDc(GeometryDc):
    """MultiLineString geometry object definition."""

    coordinates: List['PositionDc'] = Field(description="Poly coordinates.")
    type: Optional['OgcGeometryType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class GeometryCollectionDc(GeometryDc):
    """Multipoint geometry object definition."""

    geometries: List[Union['GeometryCollectionDc', 'LineStringDc', 'MultiLineStringDc', 'MultiPointDc', 'MultiPolygonDc', 'PointDc', 'PolygonDc']] = Field(description="Multipoint coordinates.")
    type: Optional['OgcGeometryType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class FeatureDc(BaseModel):
    """Feature object definition."""

    properties: Dict[str, Any] = Field(description="Feature attributes collection.")
    geometry: Optional[Union['GeometryCollectionDc', 'LineStringDc', 'MultiLineStringDc', 'MultiPointDc', 'MultiPolygonDc', 'PointDc', 'PolygonDc']] = Field(default=None, description="Feature geometry definition.")
    id: Optional[str] = Field(default=None, description="Feature unique identifier.")
    type: Optional[str] = Field(default=None, description="Type.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class FileDto(BaseModel):
    content: Optional[str] = None
    path: Optional[str] = None
    size: Optional[int] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class FileUploadResponse(BaseModel):
    """The result of uploading a file."""

    fileId: Optional[str] = Field(default=None, description="Id of the tile in the session static storage.")
    resourceId: Optional[str] = Field(default=None, description="Resource id.")
    sourceId: Optional[str] = Field(default=None, description="Id of the file source.")
    url: Optional[str] = Field(default=None, description="Url to file.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class QueryGeometryOperationDc(BaseModel):
    """Query geometry operation data contract."""

    buffer: Optional[int] = Field(default=None, description="Buffer size.")
    name: Optional[str] = Field(default=None, description="Function name.")
    parameters: Optional[List[None]] = Field(default=None, description="Additional parameters.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class QueryGeometryDc(BaseModel):
    """Query geometry data contract."""

    geometry: Optional[str] = Field(default=None, description="Geometry in EWKT format.")
    operation: Optional['QueryGeometryOperationDc'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class FilterDc(BaseModel):
    """Provides filter data contract."""

    conditions: Optional[List[str]] = Field(default=None, description="Filter conditions.")
    geometries: Optional[List['QueryGeometryDc']] = Field(default=None, description="Filter query geometries.")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class FilterResponseDc(BaseModel):
    """Server response for the creation of a filter in filter service."""

    id: Optional[str] = Field(default=None, description="Id of the filter.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class GeocodeSuggestResultDc(BaseModel):
    """Geocode suggest result."""

    id: Optional[str] = Field(default=None, description="Source id.")
    label: Optional[str] = Field(default=None, description="Source label.")
    text: Optional[str] = Field(default=None, description="Suggested text.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class GetBulkExtentsDc(BaseModel):
    """Get extent from layer paramaters."""

    conditions: Optional[List[str]] = Field(default=None, description="Filter conditions.")
    geometries: Optional[List['QueryGeometryDc']] = Field(default=None, description="Filter query geometries.")
    layerName: Optional[str] = Field(default=None, description="Full name of the layer.")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class GetBulkFeaturesParametersDc(BaseModel):
    """Get features from layer paramaters."""

    attributes: Optional[List[str]] = Field(default=None, description="Comma separated list of attributes to be returned. If not set, all attributes are returned.")
    conditions: Optional[List[str]] = Field(default=None, description="Collection of filtering conditions.")
    dataFilterId: Optional[str] = Field(default=None, description="Id of override data filter to apply to the layer. If not set, the default filter is used.")
    ewktGeometry: Optional[str] = Field(default=None, description="Click geometry.")
    geometries: Optional[List['QueryGeometryDc']] = Field(default=None, description="Filter query geometries.")
    ids: Optional[List[str]] = Field(default=None, description="Comma separated list of features ids.")
    layerName: Optional[str] = Field(default=None, description="Layer name.")
    limit: Optional[int] = Field(default=None, description="Features limit per response.")
    offset: Optional[int] = Field(default=None, description="Features count have to skip.")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Features filtering query parameters.")
    sort: Optional[List[str]] = Field(default=None, description="Comma separated list of attributes by which to sort the resulting feature list. If the attribute name is preceded with the \"-\" sign, sorting by this attribute will be in descending order.")
    srId: Optional[int] = Field(default=None, description="Spatial reference of returned features.")
    withGeom: Optional[bool] = Field(default=None, description="If set to true, the geometry will not be returned for features.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class GetBulkFilteredFeaturesCountDc(BaseModel):
    """Get features count with layer filter condition data contract."""

    conditions: Optional[List[str]] = Field(default=None, description="Collection of filtering conditions.")
    geometries: Optional[List['QueryGeometryDc']] = Field(default=None, description="Filter query geometries.")
    layerName: Optional[str] = Field(default=None, description="Layer name.")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class GetClassifyDc(BaseModel):
    """Get classified attribute values data contract."""

    attributeName: str = Field(description="Attribute name.", min_length=1)
    layerName: str = Field(description="Layer name.", min_length=1)
    attributeType: Optional['ClassifyAttributeType'] = None
    classes: Optional[int] = Field(default=None, description="The number of classes.")
    conditions: Optional[List[str]] = Field(default=None, description="Collection of filtering conditions.")
    geometries: Optional[List['QueryGeometryDc']] = Field(default=None, description="Filter query geometries.")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters.")
    precision: Optional[int] = Field(default=None, description="Sets required values precision.")
    type: Optional['ClassificationType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class GetFeaturesParametersDc(BaseModel):
    """Get features paramaters."""

    attributes: Optional[List[str]] = Field(default=None, description="Comma separated list of attributes to be returned. If not set, all attributes are returned.")
    conditions: Optional[List[str]] = Field(default=None, description="Collection of filtering conditions.")
    dataFilterId: Optional[str] = Field(default=None, description="Id of override data filter to apply to the layer. If not set, the default filter is used.")
    ewktGeometry: Optional[str] = Field(default=None, description="Click geometry.")
    geometries: Optional[List['QueryGeometryDc']] = Field(default=None, description="Filter query geometries.")
    ids: Optional[List[str]] = Field(default=None, description="Comma separated list of features ids.")
    limit: Optional[int] = Field(default=None, description="Features limit per response.")
    offset: Optional[int] = Field(default=None, description="Features count have to skip.")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Features filtering query parameters.")
    sort: Optional[List[str]] = Field(default=None, description="Comma separated list of attributes by which to sort the resulting feature list. If the attribute name is preceded with the \"-\" sign, sorting by this attribute will be in descending order.")
    srId: Optional[int] = Field(default=None, description="Spatial reference of returned features.")
    withGeom: Optional[bool] = Field(default=None, description="If set to true, the geometry will not be returned for features.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class GetFilteredFeaturesCountDc(BaseModel):
    """Get features count with layer filter condition data contract."""

    conditions: Optional[List[str]] = Field(default=None, description="Collection of filtering conditions.")
    geometries: Optional[List['QueryGeometryDc']] = Field(default=None, description="Filter query geometries.")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class GetStatisticsDc(BaseModel):
    """Get statistics data contract."""

    attributeName: str = Field(description="Attribute name.", min_length=1)
    layerName: str = Field(description="Layer name.", min_length=1)
    conditions: Optional[List[str]] = Field(default=None, description="Collection of filtering conditions.")
    geometries: Optional[List['QueryGeometryDc']] = Field(default=None, description="Filter query geometries.")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters.")
    types: Optional[List['AggregationFunction']] = Field(default=None, description="Type of required statistic function.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class GetSumOfProductDc(BaseModel):
    """Get sum of product data contract."""

    attributes: List[str] = Field(description="Attribute name.")
    layerName: str = Field(description="Layer name.", min_length=1)
    conditions: Optional[List[str]] = Field(default=None, description="Collection of filtering conditions.")
    geometries: Optional[List['QueryGeometryDc']] = Field(default=None, description="Filter query geometries.")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ImportLayerDataSchemaDc(BaseModel):
    """Schema of a layer in an imported file."""

    name: str = Field(description="Name of the layer.", min_length=1)
    attributesConfiguration: Optional['AttributesConfigurationDc'] = None
    children: Optional[List['ImportLayerDataSchemaDc']] = Field(default=None, description="Schema of a inner layers.")
    coordinateFields: Optional[List[str]] = Field(default=None, description="Assumed coordinate fields.")
    objectCount: Optional[int] = Field(default=None, description="Number of objects in the layer.")
    rows: Optional[List['FeatureDc']] = Field(default=None, description="First feature in the layer.")
    type: Optional[str] = Field(default=None, description="Storage type.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ImportDataSchemaDc(BaseModel):
    """Data schema of a file for import."""

    layers: List['ImportLayerDataSchemaDc'] = Field(description="List of layers in the data-set.")
    type: str = Field(description="Importing file type.", min_length=1)

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ImportFileFeaturesCountDc(BaseModel):
    """Get features count data contract."""

    fileId: str = Field(description="Id of the file in the temporary static storage.", min_length=1)
    condition: Optional[str] = Field(default=None, description="Condition.")
    name: Optional[str] = Field(default=None, description="Name of the layer.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class IncreaseResourcesLimitDc(BaseModel):
    """Increase resources limit feedback data contract."""

    dataSource: Optional[int] = Field(default=None, description="Additional data sources count.")
    justification: Optional[str] = Field(default=None, description="Request justification.")
    layer: Optional[int] = Field(default=None, description="Additional layers count.")
    map: Optional[int] = Field(default=None, description="Additional maps count.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class LayerServiceType(str, Enum):
    """Specifies the available types of layer services that can be used within the application."""

    QUERYLAYERSERVICE = "QueryLayerService"
    LINEARLAYERSERVICE = "LinearLayerService"
    MAPBOXLAYERSERVICE = "MapboxLayerService"
    POSTGRESTILELAYERSERVICE = "PostgresTileLayerService"
    PROXYLAYERSERVICE = "ProxyLayerService"
    PYTHONLAYERSERVICE = "PythonLayerService"
    REMOTETILELAYERSERVICE = "RemoteTileLayerService"
    ROUTELAYERSERVICE = "RouteLayerService"


class LayerUpdateInfoDc(BaseModel):
    """Information about layer update. Includes ids of modified features and their bbox."""

    layerServiceName: str = Field(description="Updated layer service name.", min_length=1)
    boundingBox: Optional['EnvelopeDc'] = None
    createdIds: Optional[List[str]] = Field(default=None, description="Array of created ids.")
    deletedIds: Optional[List[str]] = Field(default=None, description="Array of deleted ids.")
    updatedIds: Optional[List[str]] = Field(default=None, description="Array of updated ids.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ServiceConfigurationBaseDc(BaseModel):
    """Common fields for service configurations."""

    layerType: 'LayerServiceType'
    name: str = Field(description="Name of the service.", min_length=1)
    alias: Optional[str] = Field(default=None, description="Human friendly name of the service.")
    cardConfiguration: Optional[Any] = Field(default=None, description="Card configuration. Storage isn't used by server.")
    clientData: Optional[Any] = Field(default=None, description="Client data storage. Storage isn't used by server.")
    copyrightText: Optional[str] = Field(default=None, description="Copyright text.")
    description: Optional[str] = Field(default=None, description="Description of the service.")
    editConfiguration: Optional[Any] = Field(default=None, description="Edit configuration. Storage isn't used by server.")
    icon: Optional[str] = Field(default=None, description="Base64 encoded image - icon of the resource.", min_length=0, max_length=102400)
    owner: Optional[str] = Field(default=None, description="If the owner user is set, a configuration will be created for that user. Administrator permissions are required to perform this operation.")
    parentId: Optional[str] = Field(default=None, description="Parent resource id.")
    tags: Optional[List[str]] = Field(default=None, description="A set of layer tags.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class LinearServiceConfigurationDc(ServiceConfigurationBaseDc):
    """Linear service configuration Dc."""

    attributesConfiguration: 'AttributesConfigurationDc'
    clientStyle: Optional[Any] = Field(default=None, description="Client style data storage. Storage isn't used by server.")
    condition: Optional[str] = Field(default=None, description="Condition to filter returned features.")
    layerType: Optional['LayerServiceType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ResourceSubTypeFilter(str, Enum):
    """Resources types filter."""

    REMOTETILESERVICE = "RemoteTileService"
    PROXYSERVICE = "ProxyService"
    QUERYLAYERSERVICE = "QueryLayerService"
    TILECATALOGTABLE = "TileCatalogTable"


class TagsFilterDc(BaseModel):
    """Tags filter."""

    tags: Optional[List[str]] = Field(default=None, description="Tags set.")
    useAnd: Optional[bool] = Field(default=None, description="AND vs OR. The AND operator displays a record if all the conditions are TRUE. The OR operator displays a record if any of the conditions are TRUE.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ResourceTypeFilter(str, Enum):
    """Resources types filter."""

    MAP = "Map"
    LAYER = "Layer"
    TABLE = "Table"
    RASTERCATALOG = "RasterCatalog"
    PROXYSERVICE = "ProxyService"
    REMOTETILESERVICE = "RemoteTileService"
    FILE = "File"
    DATASOURCE = "DataSource"
    TASKPROTOTYPE = "TaskPrototype"
    DIRECTORY = "Directory"


class ListResourcesDc(BaseModel):
    """Search resources."""

    aclFilter: Optional[Dict[str, 'Permissions']] = Field(default=None, description="Filter by set of roles permissions.")
    filter: Optional[str] = Field(default=None, description="Text filer support sql like symbols for example start with 'text*', contains 'text', end with '*text'.")
    geometryTypes: Optional[List['OgcGeometryType']] = Field(default=None, description="Geometry types filter.")
    orderBy: Optional[List[str]] = Field(default=None, description="Order by result.")
    ownerFilter: Optional['AccessMode'] = None
    parentId: Optional[str] = Field(default=None, description="Parent id.")
    resourceTypes: Optional[List['CatalogResourceType']] = Field(default=None, description="Resources types filter.")
    searchMode: Optional[bool] = Field(default=None, description="Search mode.")
    subtypes: Optional[List['ResourceSubTypeFilter']] = Field(default=None, description="Resources subtypes filter.")
    systemNames: Optional[List[str]] = Field(default=None, description="System names filter.")
    tagsFilter: Optional['TagsFilterDc'] = None
    types: Optional[List['ResourceTypeFilter']] = Field(default=None, description="Resources types filter.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class LodInfo(BaseModel):
    """Tile LOD structure."""

    level: Optional[int] = Field(default=None, description="Level of tile set.")
    resolution: Optional[float] = Field(default=None, description="Resolution for level.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class LoginDc(BaseModel):
    """Login data contract."""

    password: str = Field(description="Password.", min_length=1)
    username: str = Field(description="Login.", min_length=1)

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class LoginResultDc(BaseModel):
    """Token data contract."""

    redirectUrl: Optional[str] = Field(default=None, description="Redirect url.")
    refreshToken: Optional[str] = Field(default=None, description="Refresh token.")
    token: Optional[str] = Field(default=None, description="JWT.")
    username: Optional[str] = Field(default=None, description="User name.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class MapTableInfoDc(BaseModel):
    """SPCore.Connectors.Connectors.Base.Models.Data.MapTableInfoDc provides information to create datasource and maps it to exists database table. SPCore.Connectors.Connectors.Base.Models.Data.MapTableInfoDc.Name can be materialized view or view."""

    name: str = Field(description="Name of the data source.", min_length=1)
    owner: str = Field(description="Owner of the data source.", min_length=1)
    acl: Optional['AccessControlListDc'] = None
    alias: Optional[str] = Field(default=None, description="Alias of the data source.")
    description: Optional[str] = Field(default=None, description="Description of the data source.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class MosRuDataSourceDc(DataSourceDc):
    """MosRu data source."""

    accessToken: Optional[str] = Field(default=None, description="Access token.")
    serviceUrl: Optional[str] = Field(default=None, description="Endpoint.")
    type: Optional['DataSourceType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class MosRuDataSourceInfoDc(DataSourceInfoDc):
    """MosRu data source info."""

    accessToken: Optional[str] = Field(default=None, description="Access token.")
    serviceUrl: Optional[str] = Field(default=None, description="Service url.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class MoveResourceDc(BaseModel):
    """Move resource dto."""

    inheritAcl: Optional[bool] = Field(default=None, description="Inherit acl from parents.")
    newName: Optional[str] = Field(default=None, description="Name of target resource.")
    rewrite: Optional[bool] = Field(default=None, description="Rewrite removes the conflicting target resource and preserves the ResourceId of the moved resource.")
    targetResource: Optional[str] = Field(default=None, description="Target resource to copy.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class NamespaceInfoDc(BaseModel):
    """Information about a namespace ."""

    acl: Optional['AccessControlListDc'] = None
    created: Optional[datetime] = Field(default=None, description="Date when the namespace was created.")
    name: Optional[str] = Field(default=None, description="Name of the namespace.")
    owner: Optional[str] = Field(default=None, description="Owner of the namespace.")
    schema_: Optional[str] = Field(default=None, alias="schema", description="Db schema for the namespace.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class RasterBandMetaDc(BaseModel):
    """RasterBandMetaDc."""

    bandType: Optional[str] = Field(default=None, description="BandType.")
    bucketCount: Optional[int] = Field(default=None, description="BucketCount.")
    colorMax: Optional[float] = Field(default=None, description="ColorMax.")
    colorMin: Optional[float] = Field(default=None, description="ColorMin.")
    dataHistogram: Optional[Dict[str, int]] = Field(default=None, description="Data histogram.")
    dataSterSize: Optional[float] = Field(default=None, description="Data step size converted to range 0-255.")
    histValueMax: Optional[float] = Field(default=None, description="HistValueMax.")
    histValueMin: Optional[float] = Field(default=None, description="HistValueMin.")
    histogram: Optional[List[int]] = Field(default=None, description="Histogram.")
    mean: Optional[float] = Field(default=None, description="Statistic mean.")
    stddev: Optional[float] = Field(default=None, description="Statistic STDDEV.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class RasterMetaDc(BaseModel):
    """RasterMetaDc."""

    bandCount: Optional[int] = Field(default=None, description="BandCount.")
    bands: Optional[List['RasterBandMetaDc']] = Field(default=None, description="Bands.")
    boundingBox: Optional[List[float]] = Field(default=None, description="BoundingBox.")
    height: Optional[int] = Field(default=None, description="Height.")
    layerName: Optional[str] = Field(default=None, description="Layer name.")
    rasterSizeInBytes: Optional[int] = Field(default=None, description="Raster size in bytes.")
    srId: Optional[int] = Field(default=None, description="Spatial reference.")
    width: Optional[int] = Field(default=None, description="Width.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class NetCdfMetaDc(RasterMetaDc):
    """RasterMetaDc."""

    dimExtraValues: Optional[Dict[str, List[str]]] = Field(default=None, description="Extra dimensions values.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class Operation(BaseModel):
    from_: Optional[str] = Field(default=None, alias="from")
    op: Optional[str] = None
    path: Optional[str] = None
    value: Optional[Any] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PagedFeaturesListDc(BaseModel):
    """Features list definition."""

    features: Optional[List['FeatureDc']] = Field(default=None, description="Features.")
    limit: Optional[int] = Field(default=None, description="Maximum number of the items that the Items parameter may contain.")
    offset: Optional[int] = Field(default=None, description="The first index of the item in the list that is returned in the Items parameter.")
    totalCount: Optional[int] = Field(default=None, description="Total number of items that the list contains, e.g. if the paging is not applied.")
    type: Optional[str] = Field(default=None, description="Type.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PagedBulkFeaturesListDc(BaseModel):
    """Features list definition."""

    error: Optional[str] = Field(default=None, description="Error text.")
    featureCollection: Optional['PagedFeaturesListDc'] = None
    hasError: Optional[bool] = Field(default=None, description="Has error.")
    layerName: Optional[str] = Field(default=None, description="Layer name.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PagedList_ConfigDc(BaseModel):
    items: Optional[List['ConfigDc']] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    totalCount: Optional[int] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class SparkDataSourceInfoDc(DataSourceInfoDc):
    """Postgres data source info."""

    endpoint: Optional[str] = Field(default=None, description="Endpoint.")
    token: Optional[str] = Field(default=None, description="Bearer token.")
    username: Optional[str] = Field(default=None, description="User name.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class S3DataSourceInfoDc(DataSourceInfoDc):
    """S3 data source info."""

    accessKey: Optional[str] = Field(default=None, description="Access key.")
    endpoint: Optional[str] = Field(default=None, description="Endpoint.")
    region: Optional[str] = Field(default=None, description="Region.")
    secretKey: Optional[str] = Field(default=None, description="Secret key.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PostgresDataSourceInfoDc(DataSourceInfoDc):
    """Postgres data source info."""

    database: Optional[str] = Field(default=None, description="Database.")
    host: Optional[str] = Field(default=None, description="Host.")
    password: Optional[str] = Field(default=None, description="Password.")
    port: Optional[int] = Field(default=None, description="Port.")
    schema_: Optional[str] = Field(default=None, alias="schema", description="Schema.")
    userName: Optional[str] = Field(default=None, description="UserName.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PagedList_DataSourceInfoDc(BaseModel):
    items: Optional[List[Union['ArcGisDataSourceInfoDc', 'MosRuDataSourceInfoDc', 'PostgresDataSourceInfoDc', 'S3DataSourceInfoDc', 'SparkDataSourceInfoDc']]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    totalCount: Optional[int] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PagedList_ExtendedUserInfoDc(BaseModel):
    items: Optional[List['ExtendedUserInfoDc']] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    totalCount: Optional[int] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PagedList_FeatureDc(BaseModel):
    items: Optional[List['FeatureDc']] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    totalCount: Optional[int] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class QueryHistoryDc(BaseModel):
    """Query history data contract."""

    dt: Optional[datetime] = Field(default=None, description="Date and time of request.")
    elapsedMilliseconds: Optional[int] = Field(default=None, description="Date and time of request started.")
    owner: Optional[str] = Field(default=None, description="Request owner.")
    request: Optional['EqlRequestDc'] = None
    rowsCount: Optional[int] = Field(default=None, description="Returned rows.")
    rowsTotalCount: Optional[int] = Field(default=None, description="Total rows count.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PagedList_QueryHistoryDc(BaseModel):
    items: Optional[List['QueryHistoryDc']] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    totalCount: Optional[int] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class QueryTokenDc(BaseModel):
    dtCreate: Optional[datetime] = None
    isActive: Optional[bool] = None
    token: Optional[str] = None
    username: Optional[str] = None
    validBefore: Optional[datetime] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PagedList_QueryTokenDc(BaseModel):
    items: Optional[List['QueryTokenDc']] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    totalCount: Optional[int] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class RoleInfoDc(BaseModel):
    """Short role information."""

    alias: Optional[str] = Field(default=None, description="Alias.")
    dtCreate: Optional[datetime] = Field(default=None, description="Gets or sets date and time of creation.")
    dtModify: Optional[datetime] = Field(default=None, description="Gets or sets date and time of last modifing.")
    idModifyUser: Optional[int] = Field(default=None, description="Gets or sets id of modified user.")
    name: Optional[str] = Field(default=None, description="Username.")
    users: Optional[List[str]] = Field(default=None, description="The number of users in the role.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PagedList_RoleInfoDc(BaseModel):
    items: Optional[List['RoleInfoDc']] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    totalCount: Optional[int] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class SymbolCategoryInfoDc(BaseModel):
    """Symbol category data contract."""

    id: Optional[int] = Field(default=None, description="Id.")
    name: Optional[str] = Field(default=None, description="Name.")
    parentId: Optional[int] = Field(default=None, description="Parent category id.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PagedList_SymbolCategoryInfoDc(BaseModel):
    items: Optional[List['SymbolCategoryInfoDc']] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    totalCount: Optional[int] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class SymbolInfoDc(BaseModel):
    """Symbols."""

    categoryId: Optional[int] = Field(default=None, description="Symbol category id.")
    data: Optional[str] = Field(default=None, description="Symbol data.")
    form: Optional[bool] = Field(default=None, description="Is substrate symbol.")
    geometryType: Optional[str] = Field(default=None, description="Symbol geometry type.")
    id: Optional[int] = Field(default=None, description="Primary key.")
    name: Optional[str] = Field(default=None, description="Symbol name.")
    type: Optional[str] = Field(default=None, description="Symbol type.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PagedList_SymbolInfoDc(BaseModel):
    items: Optional[List['SymbolInfoDc']] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    totalCount: Optional[int] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class UserInfoDc(BaseModel):
    """Short user information."""

    email: Optional[str] = Field(default=None, description="Email.")
    first_name: Optional[str] = Field(default=None, description="First name.")
    has_profile_photo: Optional[bool] = Field(default=None, description="Photo.")
    is_active: Optional[bool] = Field(default=None, description="If the user account is active or not.")
    is_open_last_project: Optional[bool] = Field(default=None, description="Whether to open the last used project when opening a client.")
    is_subscribed: Optional[bool] = Field(default=None, description="Has newsletter subscription.")
    last_name: Optional[str] = Field(default=None, description="Last name.")
    namespace: Optional[str] = Field(default=None, description="Namespace.")
    patronymic: Optional[str] = Field(default=None, description="Patronymic.")
    phone: Optional[str] = Field(default=None, description="Phone number.")
    roles: Optional[List[str]] = Field(default=None, description="The roles of the user.")
    username: Optional[str] = Field(default=None, description="Username.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PagedList_UserInfoDc(BaseModel):
    items: Optional[List['UserInfoDc']] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    totalCount: Optional[int] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PagedResourcesListDc(BaseModel):
    """Paged resources list."""

    items: Optional[List['CatalogResourceDc']] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    totalCount: Optional[int] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PagedTagsListDc(BaseModel):
    """Paged resources list."""

    items: Optional[List[str]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    totalCount: Optional[int] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PatchResourceDc(BaseModel):
    """Patch resource request."""

    description: Optional[str] = Field(default=None, description="Description of the directory.")
    icon: Optional[str] = Field(default=None, description="Resource icon.")
    inheritAcl: Optional[bool] = Field(default=None, description="True if acl inherited from parent.")
    name: Optional[str] = Field(default=None, description="Description of the directory.")
    tags: Optional[List[str]] = Field(default=None, description="A set of tags.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PbfSchema(str, Enum):
    """Influences the y direction of the tile coordinates. The global-mercator (aka Spherical Mercator) profile is assumed."""

    XYZ = "xyz"
    TMS = "tms"


class ProxyServiceConfigurationDc(ServiceConfigurationBaseDc):
    """Configuration for the proxy service."""

    geometryType: Optional['OgcGeometryType'] = None
    layerType: Optional['LayerServiceType'] = None
    layers: Optional[List[str]] = Field(default=None, description="Names of layers to include in proxy layer (can be numbers).")
    resourceId: Optional[str] = Field(default=None, description="Resource id.")
    sourceType: Optional[str] = Field(default=None, description="Source system type, e.g. \"ArcGIS\".")
    sourceUrl: Optional[str] = Field(default=None, description="Source url path. Like http://sampleserver1.arcgisonline.com/ArcGIS/rest/services/Specialty/SuperTuesdaySample/MapServer.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PbfServiceConfigurationDc(ProxyServiceConfigurationDc):
    """Configuration for the mapbox PBF/MVT service."""

    layerType: Optional['LayerServiceType'] = None
    schema_: Optional['PbfSchema'] = Field(default=None, alias="schema")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ProxyLayerLegendItemDc(BaseModel):
    """Data contract for legend item."""

    image: str = Field(description="Image of item encoded in Base64 string.", min_length=1)
    label: str = Field(description="Text label of legend item.", min_length=1)

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ProxyInnerLayerLegendDc(BaseModel):
    """Data contract for inner layer Legend."""

    items: List['ProxyLayerLegendItemDc'] = Field(description="Legend items.")
    layerId: str = Field(description="Layer id.", min_length=1)
    layerName: str = Field(description="Layer name.", min_length=1)

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ProxyLayerLegendDc(BaseModel):
    """Data contract for layer legend."""

    layers: List['ProxyInnerLayerLegendDc'] = Field(description="Inner layers legends.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PostgresTileCatalogServiceConfigurationDc(ServiceConfigurationBaseDc):
    """Configuration of a postgres tile catalog service."""

    attributesConfiguration: 'AttributesConfigurationDc'
    clientStyle: Optional[Any] = Field(default=None, description="Client style data storage. Storage isn't used by server.")
    condition: Optional[str] = Field(default=None, description="Condition to filter returned features.")
    isCogLayer: Optional[bool] = Field(default=None, description="IsCogLayer.")
    layerType: Optional['LayerServiceType'] = None
    maxLodLevel: Optional[int] = Field(default=None, description="Max lod level.")
    minLodLevel: Optional[int] = Field(default=None, description="Min lod level.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class RouteServiceConfigurationDc(ServiceConfigurationBaseDc):
    """Route service configuration Dc."""

    attributesConfiguration: 'AttributesConfigurationDc'
    clientStyle: Optional[Any] = Field(default=None, description="Client style data storage. Storage isn't used by server.")
    condition: Optional[str] = Field(default=None, description="Condition to filter returned features.")
    layerType: Optional['LayerServiceType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PythonServiceMethodDc(BaseModel):
    """Description python script method."""

    fileName: Optional[str] = Field(default=None, description="Python script file name.")
    methodName: Optional[str] = Field(default=None, description="Python script method name.")
    parameters: Optional[Any] = Field(default=None, description="Python script default parameters.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PythonServiceConfigurationDc(ProxyServiceConfigurationDc):
    """Configuration for the python service."""

    featuresQuery: Optional['PythonServiceMethodDc'] = None
    layerDefinitionQuery: Optional['PythonServiceMethodDc'] = None
    layerType: Optional['LayerServiceType'] = None
    pythonResourceId: Optional[str] = Field(default=None, description="PythonResourceId.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class QueryLayerServiceEqlParameterQueryValueConfigurationDc(BaseModel):
    """EQL value from query configuration parameter data contract."""

    additionalDsConnections: Optional[List['AdditionalDataSourceConnectionDc']] = Field(default=None, description="Additional data source connection.")
    ds: Optional[str] = Field(default=None, description="Query text.")
    isCached: Optional[bool] = Field(default=None, description="Is values cached.")
    isSingleValue: Optional[bool] = Field(default=None, description="Use only first value, not array.")
    query: Optional[str] = Field(default=None, description="Query text.")
    valueColumn: Optional[str] = Field(default=None, description="Name of the column containing the value.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class QueryLayerServiceEqlParameterConfigurationDc(BaseModel):
    """EQL parameter configuration data contract."""

    additionalDsConnections: Optional[List['AdditionalDataSourceConnectionDc']] = Field(default=None, description="Additional data source connection.")
    alias: Optional[str] = Field(default=None, description="Parameter alias.")
    availableValues: Optional[List[None]] = Field(default=None, description="Available values.")
    default: Optional[Any] = Field(default=None, description="Default value.")
    description: Optional[str] = Field(default=None, description="Description.")
    descriptionColumn: Optional[str] = Field(default=None, description="Name of the column containing the description.")
    ds: Optional[str] = Field(default=None, description="Data source name.")
    isArray: Optional[bool] = Field(default=None, description="Is array type.")
    query: Optional[str] = Field(default=None, description="Query text.")
    queryValue: Optional['QueryLayerServiceEqlParameterQueryValueConfigurationDc'] = None
    type: Optional['AttributeType'] = None
    valueColumn: Optional[str] = Field(default=None, description="Name of the column containing the value.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class SimplifyType(str, Enum):
    BASIC = "Basic"
    PRESERVETOPOLOGY = "PreserveTopology"
    VW = "VW"


class SimplifyInfoItemDc(BaseModel):
    """Simplify configuration information."""

    simplifyPreserveCollapsed: Optional[bool] = Field(default=None, description="The \"preserve collapsed\" flag will retain objects that would otherwise be too small given the tolerance.")
    simplifyTolerance: Optional[float] = Field(default=None, description="Tolerance.")
    simplifyType: Optional['SimplifyType'] = None
    snapCellSize: Optional[float] = Field(default=None, description="Snap grid cell size.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class SimplifyInfoDc(BaseModel):
    """Simplify configuration information."""

    scaleItems: Optional[Dict[str, 'SimplifyInfoItemDc']] = Field(default=None, description="Snap grid cell size by scale.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class QueryLayerServiceConfigurationDc(ServiceConfigurationBaseDc):
    """Configuration of a postgres feature layer service."""

    additionalDsConnections: Optional[List['AdditionalDataSourceConnectionDc']] = Field(default=None, description="Additional data source connection.")
    attributesConfiguration: Optional['AttributesConfigurationDc'] = None
    clientStyle: Optional[Any] = Field(default=None, description="Client style data storage. Storage isn't used by server.")
    clipping: Optional['ClippingInfoDc'] = None
    condition: Optional[str] = Field(default=None, description="Condition to filter returned features.")
    createTable: Optional[bool] = Field(default=None, description="Create a table to use if it doesn't exists.")
    ds: Optional[str] = Field(default=None, description="Data source name.")
    eql: Optional[str] = Field(default=None, description="EQL query.")
    eqlParameters: Optional[Dict[str, 'QueryLayerServiceEqlParameterConfigurationDc']] = Field(default=None, description="EQL parameters.")
    geometryType: Optional['OgcGeometryType'] = None
    layerType: Optional['LayerServiceType'] = None
    queryId: Optional[str] = Field(default=None, description="Saved query id.")
    simplify: Optional['SimplifyInfoDc'] = None
    srId: Optional[int] = Field(default=None, description="Spatial reference identifier type in geometry type column.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class TileInfoDc(BaseModel):
    """Tile info structure."""

    height: int = Field(description="Height of each tile in pixels.")
    lods: List['LodInfo'] = Field(description="List of levels of detail that define the tiling schema.")
    width: int = Field(description="Height of each tile in pixels.")
    boundingRectangle: Optional[List[float]] = Field(default=None, description="Bounding rectangle of the schema.")
    dpi: Optional[int] = Field(default=None, description="The dpi of the tiling schema.")
    format: Optional[str] = Field(default=None, description="Image format.")
    origin: Optional[List[float]] = Field(default=None, description="The zero point of the coordinates from which tiles are counted.")
    reversedY: Optional[bool] = Field(default=None, description="If true, positive side of 'Y' coordinate, will be in the reverse side.")
    srId: Optional[int] = Field(default=None, description="Spatial reference.")
    tilesSubDomains: Optional[List[str]] = Field(default=None, description="A list of subdomains.<example>a,b,c</example>. Subdomains are used to distribute tile requests across multiple servers. <example> http://{subDomain}.evergis/{x}/{y}/{z}.png</example>.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class RemoteTileServiceConfigurationDc(ServiceConfigurationBaseDc):
    """Configuration for the remote tile service."""

    urlFormat: str = Field(description="SourceBatch url mask. Like http://{0}.website.ru/{1}/{2}/{3}.png Where: {0} - SubDomains, {1} - Z, {2} - X, {3} - Y.", min_length=1)
    RequestTimeout: Optional[int] = None
    allowDirectAccess: Optional[bool] = Field(default=None, description="Allows the client to receive tiles directly from the source server.")
    cacheExpire: Optional[int] = Field(default=None, description="Amount of time cache expire in seconds.")
    layerType: Optional['LayerServiceType'] = None
    subDomains: Optional[List[str]] = Field(default=None, description="Subdomains. To get tiles from different servers. Will be inserted into the UrlFormat {0}.")
    tileCacheLimit: Optional[int] = Field(default=None, description="Max tile count for caching.")
    tileInfo: Optional['TileInfoDc'] = None
    useProxyHttpClient: Optional[bool] = Field(default=None, description="Use proxy HttpClient.")
    useRedisCache: Optional[bool] = Field(default=None, description="If set true cache tiles in redis cache.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ServiceInfoDc(BaseResourceInfoDc):
    """The `ServiceInfoDc` provides information about the service."""

    acl: Optional['AccessControlListDc'] = None
    categories: Optional[List[str]] = Field(default=None, description="The category of the service.")
    changedDate: Optional[datetime] = Field(default=None, description="The date when resource was last modified.")
    configuration: Optional[Union['PbfServiceConfigurationDc', 'PythonServiceConfigurationDc', 'LinearServiceConfigurationDc', 'PostgresTileCatalogServiceConfigurationDc', 'QueryLayerServiceConfigurationDc', 'RemoteTileServiceConfigurationDc', 'RouteServiceConfigurationDc', 'ProxyServiceConfigurationDc']] = Field(default=None, description="Configuration of the service.")
    createdDate: Optional[datetime] = Field(default=None, description="The date when resource was created.")
    permissions: Optional['Permissions'] = None
    resourceId: Optional[str] = Field(default=None, description="Resource id in resources catalog.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ProxyServiceInfoDc(ServiceInfoDc):
    """Service info for a Proxy service."""

    layers: List[str] = Field(description="Names of layers to include in proxy layer (can be numbers).")
    sourceType: str = Field(description="Source system type, e.g. \"ArcGIS\".", min_length=1)
    sourceUrl: str = Field(description="Source url path. Like http://sampleserver1.arcgisonline.com/ArcGIS/rest/services/Specialty/SuperTuesdaySample/MapServer.", min_length=1)
    legend: Optional['ProxyLayerLegendDc'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PbfServiceInfoDc(ProxyServiceInfoDc):
    """Service info for a mapbox service."""

    schema_: 'PbfSchema' = Field(alias="schema")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PolicyType(str, Enum):
    """Type of the authorization policy."""

    UNKNOWN = "Unknown"
    CREATETABLE = "CreateTable"
    CREATELAYER = "CreateLayer"
    CREATEPROJECT = "CreateProject"
    MAXFEATURESINONETABLE = "MaxFeaturesInOneTable"
    MAXOBJECTSTOEXPORT = "MaxObjectsToExport"
    MAXUPLOADCONTENTSIZE = "MaxUploadContentSize"
    MAXEQLQUERYPARAMETERSVALUES = "MaxEqlQueryParametersValues"


class PolicyDc(BaseModel):
    type: 'PolicyType'
    value: int
    role: Optional[str] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PostgresDataSourceDc(DataSourceDc):
    """Postgres connection data source connection."""

    database: Optional[str] = Field(default=None, description="Database.")
    host: Optional[str] = Field(default=None, description="Host.")
    password: Optional[str] = Field(default=None, description="Password.")
    port: Optional[int] = Field(default=None, description="Port.")
    schema_: Optional[str] = Field(default=None, alias="schema", description="Schema.")
    type: Optional['DataSourceType'] = None
    userName: Optional[str] = Field(default=None, description="UserName.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PublishLayerInfoDc(BaseModel):
    """Represents the information required to publish a layer service, including its metadata, configuration, and access control settings."""

    configuration: Union['PbfServiceConfigurationDc', 'PythonServiceConfigurationDc', 'LinearServiceConfigurationDc', 'PostgresTileCatalogServiceConfigurationDc', 'QueryLayerServiceConfigurationDc', 'RemoteTileServiceConfigurationDc', 'RouteServiceConfigurationDc', 'ProxyServiceConfigurationDc'] = Field(description="Configuration of the service.")
    acl: Optional['AccessControlListDc'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PullResponse(BaseModel):
    commitSha: Optional[str] = None
    files: Optional[List['FileDto']] = None
    pulledAt: Optional[datetime] = None
    syncVersion: Optional[int] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PushRequestDc(BaseModel):
    """Push request data transfer object."""

    commitMessage: str = Field(description="Commit message.")
    resourceId: str = Field(description="Resource id to push.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PushResponse(BaseModel):
    changesCount: Optional[int] = None
    commitSha: Optional[str] = None
    pushedAt: Optional[datetime] = None
    syncVersion: Optional[int] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PythonServiceInfoDc(ProxyServiceInfoDc):
    """Service info for a mapbox service."""

    pass

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class PythonTaskMethodConfiguration(BaseModel):
    """TaskMethodConfiguration."""

    error: Optional[str] = Field(default=None, description="Gets or sets method init error.")
    fileName: Optional[str] = Field(default=None, description="Gets or sets script file name.")
    methodName: Optional[str] = Field(default=None, description="Gets or sets method.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class QueryLayerServiceInfoDc(ServiceInfoDc):
    """Service info for a feature layer service."""

    dataSourceType: Optional[str] = Field(default=None, description="Provides data source type.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class RefreshTokenDc(BaseModel):
    """Refresh token request data contract."""

    refreshToken: Optional[str] = Field(default=None, description="Refresh token.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class RegisterClientRequestDc(BaseModel):
    """Create client data contract."""

    client_name: str = Field(description="Name of the client.", min_length=1)
    redirect_uri: str = Field(description="Redirect uri.", min_length=1)
    client_uri: Optional[str] = Field(default=None, description="Client uri.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class RegisterClientResponseDc(BaseModel):
    """Create client response dc."""

    client_id: Optional[UUID] = Field(default=None, description="Client id.")
    client_name: Optional[str] = Field(default=None, description="Client name.")
    secret: Optional[str] = Field(default=None, description="Client secret.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class RegisterUserDc(BaseModel):
    """Data contract for register new user."""

    company: Optional[str] = Field(default=None, description="Gets or sets company.")
    email: Optional[str] = Field(default=None, description="Email.")
    first_name: Optional[str] = Field(default=None, description="First name.")
    goals: Optional[str] = Field(default=None, description="Additional information or goals.")
    is_subscribed: Optional[bool] = Field(default=None, description="Has newsletter subscription.")
    last_name: Optional[str] = Field(default=None, description="Last name.")
    password: Optional[str] = Field(default=None, description="Password.")
    patronymic: Optional[str] = Field(default=None, description="Patronymic.")
    phone: Optional[str] = Field(default=None, description="Phone number.")
    username: Optional[str] = Field(default=None, description="Username.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class RemoteTaskStatus(str, Enum):
    INIT = "Init"
    PROCESS = "Process"
    COMPLETED = "Completed"
    INTERRUPTED = "Interrupted"
    ERROR = "Error"
    TIMEOUT = "Timeout"
    WAITING = "Waiting"
    INQUEUE = "InQueue"
    UNKNOWN = "Unknown"


class RemoteTileServiceInfoDc(ServiceInfoDc):
    """Service info for a tile service."""

    sourceServers: Optional[List[str]] = Field(default=None, description="SourceBatch servers, what can be placed at source url mask, instead {s}.")
    sourceUrlMask: Optional[str] = Field(default=None, description="Mask for getting tiles in default form www.{s}.tiles.com/{z}/{x}/{y}.png.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ResourceDependenciesDc(BaseModel):
    """The `ResourceDependenciesDc` describes resource dependencies."""

    dependencies: List['DependentResourceDc'] = Field(description="A collection of resource dependencies.")
    name: str = Field(description="Resource name.", min_length=1)

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ResourceParentDc(BaseModel):
    """Resource parent."""

    name: Optional[str] = Field(default=None, description="Resource name.")
    path: Optional[str] = Field(default=None, description="Resource path.")
    resourceId: Optional[str] = Field(default=None, description="Resource id.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ResponseType(str, Enum):
    CODE = "code"
    TOKEN = "token"


class RollbackRequestDc(BaseModel):
    """Rollback request data transfer object."""

    resourceId: str = Field(description="Resource id to rollback.")
    targetVersion: int = Field(description="Target version rollback to.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class RollbackResponse(BaseModel):
    newCommitSha: Optional[str] = None
    rolledBackAt: Optional[datetime] = None
    rolledBackToVersion: Optional[int] = None
    syncVersion: Optional[int] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class S3DataSourceDc(DataSourceDc):
    """S3 data source settings."""

    accessKey: Optional[str] = Field(default=None, description="Access key.")
    endpoint: Optional[str] = Field(default=None, description="Endpoint.")
    port: Optional[int] = Field(default=None, description="Port.")
    region: Optional[str] = Field(default=None, description="Region.")
    secretKey: Optional[str] = Field(default=None, description="Secret key.")
    type: Optional['DataSourceType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class TaskDto(BaseModel):
    """TaskDto."""

    ended: Optional[datetime] = Field(default=None, description="Ended.")
    forceExecution: Optional[bool] = Field(default=None, description="ForceExecution.")
    id: Optional[UUID] = Field(default=None, description="Id.")
    started: Optional[datetime] = Field(default=None, description="Started.")
    status: Optional['RemoteTaskStatus'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class SearchResultsDto_TaskDto(BaseModel):
    """SearchResults."""

    count: Optional[int] = Field(default=None, description="Count.")
    results: Optional[List['TaskDto']] = Field(default=None, description="Results.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class SubTaskSettingsDto(BaseModel):
    """SubTaskSettingsDto."""

    description: Optional[str] = Field(default=None, description="Description.")
    order: Optional[int] = Field(default=None, description="Order.")
    startParameters: Optional[Any] = Field(default=None, description="StartParameters.")
    type: Optional[str] = Field(default=None, description="Type.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class TaskPrototypeDto(BaseModel):
    """TaskPrototypeDto."""

    createdAt: Optional[datetime] = Field(default=None, description="CreatedAt.")
    delayDate: Optional[datetime] = Field(default=None, description="DelayDate.")
    description: Optional[str] = Field(default=None, description="Description.")
    enabled: Optional[bool] = Field(default=None, description="Enabled.")
    id: Optional[UUID] = Field(default=None, description="Id.")
    lastTaskFinish: Optional[datetime] = Field(default=None, description="Last task finish.")
    lastTaskStatus: Optional['RemoteTaskStatus'] = None
    schedule: Optional[str] = Field(default=None, description="Schedule.")
    startIfPreviousError: Optional[bool] = Field(default=None, description="StartIfPreviousError.")
    startIfPreviousNotFinished: Optional[bool] = Field(default=None, description="StartIfPreviousNotFinished.")
    subTaskSettings: Optional[List['SubTaskSettingsDto']] = Field(default=None, description="SubTaskSettings.")
    tasksCount: Optional[int] = Field(default=None, description="Tasks count.")
    user: Optional[str] = Field(default=None, description="User.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class SearchResultsDto_TaskPrototypeDto(BaseModel):
    """SearchResults."""

    count: Optional[int] = Field(default=None, description="Count.")
    results: Optional[List['TaskPrototypeDto']] = Field(default=None, description="Results.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class SearchedUserDc(BaseModel):
    """Suggest user information."""

    ownRole: Optional[str] = Field(default=None, description="Own user role.")
    photo: Optional[str] = Field(default=None, description="Photo.")
    username: Optional[str] = Field(default=None, description="Username.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class SparkDataSourceDc(DataSourceDc):
    """Postgres connection data source connection."""

    endpoint: Optional[str] = Field(default=None, description="Endpoint.")
    token: Optional[str] = Field(default=None, description="Bearer token.")
    type: Optional['DataSourceType'] = None
    userName: Optional[str] = Field(default=None, description="User name.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class SrInfo(BaseModel):
    """Spatial reference information data contract."""

    authName: Optional[str] = Field(default=None, description="Auth name.")
    code: Optional[int] = Field(default=None, description="Code.")
    name: Optional[str] = Field(default=None, description="Name.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class StatisticsResult_Object(BaseModel):
    """Statistics result."""

    type: Optional['AggregationFunction'] = None
    value: Optional[Any] = Field(default=None, description="Value.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class StatisticsDc(BaseModel):
    """Statistics result."""

    statisticsResult: List[Any] = Field(description="Statistics result.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class StatusResponseDc(BaseModel):
    """Represents the current status of a connected storage."""

    branch: Optional[str] = Field(default=None, description="Branch.")
    connectedAt: Optional[datetime] = Field(default=None, description="Connection timestamp.")
    lastCommitSha: Optional[str] = Field(default=None, description="Last commit sha.")
    lastSyncAt: Optional[datetime] = Field(default=None, description="Last sync timestamp.")
    latestVersion: Optional[int] = Field(default=None, description="Latest repository version.")
    repositoryUrl: Optional[str] = Field(default=None, description="Repository url.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class SubTasksDto(BaseModel):
    """SubTasksDto."""

    ended: Optional[datetime] = Field(default=None, description="Ended.")
    errorMessage: Optional[str] = Field(default=None, description="ErrorMessage.")
    id: Optional[UUID] = Field(default=None, description="Id.")
    max: Optional[int] = Field(default=None, description="Max.")
    order: Optional[int] = Field(default=None, description="Order.")
    process: Optional[int] = Field(default=None, description="Process.")
    results: Optional[Dict[str, Any]] = Field(default=None, description="Results.")
    started: Optional[datetime] = Field(default=None, description="Started.")
    status: Optional['RemoteTaskStatus'] = None
    type: Optional[str] = Field(default=None, description="Type.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class TaskResourceSubType(str, Enum):
    """TaskPrototypeSubType."""

    SPTASK = "SpTask"
    PYTHONTASK = "PythonTask"


class TaskConfigurationDc(BaseModel):
    """TaskConfigurationDc."""

    defaultConfiguration: Optional[Any] = Field(default=None, description="DefaultConfiguration.")
    description: Optional[str] = Field(default=None, description="Description.")
    importMethod: Optional[str] = Field(default=None, description="ImportMethods.")
    taskResourceSubType: Optional['TaskResourceSubType'] = None
    taskType: Optional[str] = Field(default=None, description="TaskType.")
    uiConfiguration: Optional[Any] = Field(default=None, description="User ui configuration.")
    userConfiguration: Optional[Any] = Field(default=None, description="UserConfiguration.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class TaskResourceCreateDto(BaseModel):
    """TaskResourceCreateDto."""

    description: Optional[str] = Field(default=None, description="Description.")
    importMethod: Optional[str] = Field(default=None, description="Import method.")
    name: Optional[str] = Field(default=None, description="Name.")
    parentId: Optional[str] = Field(default=None, description="ParentId.")
    subType: Optional['TaskResourceSubType'] = None
    systemName: Optional[str] = Field(default=None, description="SystemName.")
    tags: Optional[List[str]] = Field(default=None, description="Tags.")
    taskType: Optional[str] = Field(default=None, description="Task type.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class TaskResourceUpdateDto(BaseModel):
    """Represents the base class for updating task resource configurations, providing essential properties for task resource updates."""

    configuration: Optional[Any] = Field(default=None, description="Configurations.")
    uiConfiguration: Optional[Any] = Field(default=None, description="User ui configuration.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class TileCatalogServiceInfoDc(ServiceInfoDc):
    """Service info for a tile catalog layer service."""

    tileInfo: 'TileInfoDc'

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class TokenRequestDc(BaseModel):
    """Access token request."""

    client_id: UUID = Field(description="Client id.")
    client_secret: str = Field(description="Client secret.", min_length=1)
    code: str = Field(description="Authorization code.", min_length=1)
    grant_type: 'AuthorizationGrant'

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class TokenResponseDc(BaseModel):
    """Token response."""

    access_token: Optional[str] = Field(default=None, description="Access token.")
    expires_in: Optional[datetime] = Field(default=None, description="Expires date.")
    refresh_token: Optional[str] = Field(default=None, description="Refresh token.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class UpdateFeatureDc(BaseModel):
    """Feature object definition for updating."""

    attributes: Optional[Dict[str, Any]] = Field(default=None, description="Feature attributes collection.")
    geometry: Optional[Union['GeometryCollectionDc', 'LineStringDc', 'MultiLineStringDc', 'MultiPointDc', 'MultiPolygonDc', 'PointDc', 'PolygonDc']] = Field(default=None, description="Feature geometry definition.")
    id: Optional[str] = Field(default=None, description="Feature unique identifier.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class UpdateRoleDc(BaseModel):
    """Update role data contract."""

    name: str = Field(description="Role name.", min_length=1)
    old_name: str = Field(description="Previous role name.", min_length=1)
    alias: Optional[str] = Field(default=None, description="Alias.")
    description: Optional[str] = Field(default=None, description="Description.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class UpdateSymbolCategoryDc(BaseModel):
    """Symbol category data contract."""

    name: Optional[str] = Field(default=None, description="Name.")
    parentId: Optional[int] = Field(default=None, description="Parent category id.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class UpdateSymbolDc(BaseModel):
    """Symbols."""

    categoryId: Optional[int] = Field(default=None, description="Symbol category id.")
    data: Optional[str] = Field(default=None, description="Symbol data.")
    form: Optional[bool] = Field(default=None, description="Is substrate symbol.")
    geometryType: Optional[str] = Field(default=None, description="Symbol geometry type.")
    name: Optional[str] = Field(default=None, description="Symbol name.")
    type: Optional[str] = Field(default=None, description="Symbol type.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class UpdateTableDc(TableInfoDc):
    """Table description with columns what must be added and deleted."""

    columnsAdd: Optional[List['ColumnDescriptionDc']] = Field(default=None, description="Description of table columns what must be added.")
    columnsDelete: Optional[List[str]] = Field(default=None, description="Table columns what must be deleted.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class UpdateTaskPrototypeDto(BaseModel):
    """UpdateTaskPrototypeDto."""

    delayDate: Optional[datetime] = Field(default=None, description="DelayDate.")
    enabled: Optional[bool] = Field(default=None, description="Enabled.")
    schedule: Optional[str] = Field(default=None, description="Schedule.")
    startIfPreviousError: Optional[bool] = Field(default=None, description="StartIfPreviousError.")
    startIfPreviousNotFinished: Optional[bool] = Field(default=None, description="StartIfPreviousNotFinished.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class UpdateUserDc(BaseModel):
    """Update user data contract."""

    company: Optional[str] = Field(default=None, description="Gets or sets company.")
    email: Optional[str] = Field(default=None, description="Email.")
    emoji: Optional[str] = Field(default=None, description="Emoji.")
    first_name: Optional[str] = Field(default=None, description="First name.")
    goals: Optional[str] = Field(default=None, description="Additional information or goals.")
    is_active: Optional[bool] = Field(default=None, description="Is active.")
    is_email_confirmed: Optional[bool] = Field(default=None, description="Is active.")
    is_open_last_project: Optional[bool] = Field(default=None, description="Whether to open the last used project when opening a client.")
    is_subscribed: Optional[bool] = Field(default=None, description="Has newsletter subscription.")
    last_name: Optional[str] = Field(default=None, description="Last name.")
    location: Optional[str] = Field(default=None, description="Gets or sets location.")
    namespace: Optional[str] = Field(default=None, description="Namespace.")
    password: Optional[str] = Field(default=None, description="Password.")
    patronymic: Optional[str] = Field(default=None, description="Patronymic.")
    phone: Optional[str] = Field(default=None, description="Phone number.")
    position: Optional[str] = Field(default=None, description="Gets or sets position.")
    username: Optional[str] = Field(default=None, description="Username.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class UsedProjectDc(BaseModel):
    """Set used project."""

    name: str = Field(description="Used project name.", min_length=1)
    updated: Optional[datetime] = Field(default=None, description="Last project update date and time.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class UserOrRoleDc(BaseModel):
    """User or role data contract."""

    aclRole: Optional[str] = Field(default=None, description="User own role.")
    isRole: Optional[bool] = Field(default=None, description="true if item is role otherwise false.")
    name: Optional[str] = Field(default=None, description="Name.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class VersionDto(BaseModel):
    commitSha: Optional[str] = None
    createdAt: Optional[datetime] = None
    message: Optional[str] = None
    versionNumber: Optional[int] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class VersionsResponse(BaseModel):
    versions: Optional[List['VersionDto']] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class WmsDataSourceDc(DataSourceDc):
    """S3 data source settings."""

    headers: Optional[Dict[str, str]] = Field(default=None, description="Endpoint.")
    params: Optional[Dict[str, str]] = Field(default=None, description="Endpoint.")
    serviceUrl: Optional[str] = Field(default=None, description="Endpoint.")
    type: Optional['DataSourceType'] = None

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class WorkerStartMethodDto(BaseModel):
    """Worker post method params."""

    methodType: str = Field(description="Method type.")
    workerType: str = Field(description="Worker type.")
    data: Optional[Any] = Field(default=None, description="Method input parameters.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class WorkspaceLimitsDc(BaseModel):
    """Workspace limits data contract."""

    currentProjectCount: Optional[int] = Field(default=None, description="Current project count.")
    currentServiceCount: Optional[int] = Field(default=None, description="Current service count.")
    currentTableCount: Optional[int] = Field(default=None, description="Current table count.")
    maxEqlQueryParametersValues: Optional[int] = Field(default=None, description="Maximum number of rows that a user can quering by eql parameter query.")
    maxFeaturesInOneTable: Optional[int] = Field(default=None, description="Max features count in one table in workspace.")
    maxObjectsToExport: Optional[int] = Field(default=None, description="Max objects to export.")
    maxProjectsCount: Optional[int] = Field(default=None, description="Max projects count in workspace.")
    maxServicesCount: Optional[int] = Field(default=None, description="Max services count in workspace.")
    maxTablesCount: Optional[int] = Field(default=None, description="Max tables count in workspace.")
    maxUploadContentSize: Optional[int] = Field(default=None, description="Max upload file size.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


class ZipExtractRequestDc(BaseModel):
    """Zip extraction request."""

    resourceId: str = Field(description="Zip resource id.")
    conflictStrategy: Optional['ConflictResolutionStrategy'] = None
    deleteZipAfterExtraction: Optional[bool] = Field(default=None, description="If true delete archive after extraction.")
    extractNestedArchives: Optional[bool] = Field(default=None, description="Is true extract nested archives.")
    targetParentId: Optional[str] = Field(default=None, description="Target parent resource id.")

    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True,
    )


# Update forward references
ProjectContentItemDc.model_rebuild()
WorkerSettingsFieldDc.model_rebuild()
GeometryCollectionDc.model_rebuild()
ImportLayerDataSchemaDc.model_rebuild()
ExternalLayerInfoDc.model_rebuild()