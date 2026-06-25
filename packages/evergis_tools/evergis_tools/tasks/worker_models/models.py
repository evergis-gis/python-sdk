"""Generated StartParameters for EverGIS Job API."""

from typing import Optional, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

# Import existing API models
from evergis_api.schemas import TaskPrototypeDto, SubTaskSettingsDto

class ProvidernameType(str, Enum):
    """Values for providername parameter."""
    OSRM_CAR = "osrm_car"
    OSRM_WALK = "osrm_walk"
    TWOGIS_CAR = "twogis_car"
    TWOGIS_WALK = "twogis_walk"
    SPROUTE_ISOCHRONE_CAR_IN = "sproute_isochrone_car_in"
    SPROUTE_ISOCHRONE_CAR_OUT = "sproute_isochrone_car_out"
    SPROUTE_ISOCHRONE_PEDESTRIAN = "sproute_isochrone_pedestrian"

class ActionType(str, Enum):
    """Values for action parameter."""
    CALL_END = "call_end"
    MARK_READ = "mark_read"
    ADD_MEMBER = "add_member"
    CALL_OFFER = "call_offer"
    CALL_ANSWER = "call_answer"
    CALL_REJECT = "call_reject"
    EDIT_MESSAGE = "edit_message"
    SEND_MESSAGE = "send_message"
    ICE_CANDIDATE = "ice_candidate"
    LEAVE_CHANNEL = "leave_channel"
    REMOVE_MEMBER = "remove_member"
    CREATE_CHANNEL = "create_channel"
    DELETE_CHANNEL = "delete_channel"
    DELETE_MESSAGE = "delete_message"
    UPDATE_CHANNEL = "update_channel"
    SUPPORT_USER_THREADS = "support_user_threads"
    SUPPORT_USER_MESSAGES = "support_user_messages"

class ModelType(str, Enum):
    """Values for model parameter."""
    PRO = "pro"
    SIMPLE = "simple"

class SourceTypeType(str, Enum):
    """Values for source parameter."""
    CSV = "csv"
    GDB = "gdb"
    KML = "kml"
    TAB = "tab"
    GPKG = "gpkg"
    EXCEL = "excel"
    LAYER = "layer"
    SHAPE = "shape"
    GEOJSON = "geojson"
    OTHERFILE = "otherfile"

class TargetTypeType(str, Enum):
    """Values for target parameter."""
    CSV = "csv"
    GPKG = "gpkg"
    EXCEL = "excel"
    LAYER = "layer"
    SHAPE = "shape"
    GEOJSON = "geojson"

class OperationType(str, Enum):
    """Values for operation parameter."""
    CLIP = "Clip"
    WITHIN = "Within"
    INTERSECT = "Intersect"
    SUBTRACTION = "Subtraction"
    SYMDIFFERENCE = "SymDifference"


class LayerReferenceConfig(BaseModel):
    """Configuration for layer reference with name, alias and parent folder."""
    name: str = Field(..., description='Layer name')
    alias: Optional[str] = Field(None, description='Layer alias')
    parentId: Optional[str] = Field(None, description='Parent folder ID')

    class Config:
        populate_by_name = True


class SourceEqlConfig(BaseModel):
    """Configuration for source EQL query."""
    layer_name: Optional[str] = Field(None, alias='layerName', description='Source layer name')
    eql: Optional[str] = Field(None, description='EQL query expression')
    condition: Optional[str] = Field(None, description='Additional condition filter')
    id_attribute: Optional[str] = Field(None, alias='idAttribute', description='ID attribute name')
    geometry_attribute: Optional[str] = Field(None, alias='geometryAttribute', description='Geometry attribute name')

    class Config:
        populate_by_name = True

class BaseStartParameters(BaseModel):
    """Base class for task start parameters."""

    class Config:
        populate_by_name = True

class NetengineOdmatrixStartParameters(BaseStartParameters):
    """Start parameters for netEngine:ODMatrix task."""

    proccessing_type: Optional[str] = Field(None, alias='proccessingType', description='Тип таски')
    source_from_layer: Optional[SourceEqlConfig] = Field(None, alias='sourceFromLayer', description='Источник FROM')
    source_to_layer: Optional[SourceEqlConfig] = Field(None, alias='sourceToLayer', description='Источник TO')
    target_layer: Optional[LayerReferenceConfig] = Field(None, alias='targetLayer', description='Целевой слой')
    transport_type: Optional[str] = Field(None, alias='transportType', description='Transport type')
    id_attribute_name: Optional[str] = Field(None, alias='idAttributeName', description='Имя атрибута идентификатора')
    id_from_attribute_name: Optional[str] = Field(None, alias='idFromAttributeName', description='Имя атрибута исходной точки (from)')
    id_to_attribute_name: Optional[str] = Field(None, alias='idToAttributeName', description='Имя атрибута целевой точки (to)')
    transport_type_attribute_name: Optional[str] = Field(None, alias='transportTypeAttributeName', description='Имя атрибута типа транспорта')
    weight_parameter_attribute_name: Optional[str] = Field(None, alias='weightParameterAttributeName', description='Имя атрибута параметра веса')
    distance_attribute_name: Optional[str] = Field(None, alias='distanceAttributeName', description='Имя атрибута расстояния/метрики')
    attribute_type_mapping: Optional[Any] = Field(None, alias='attributeTypeMapping', description='Смена типа для атрибута')
    default_values: Optional[Any] = Field(None, alias='defaultValues', description='Дефолтные значения для параметра')

class NetengineOdmatrixrestStartParameters(BaseStartParameters):
    """Start parameters for netEngine:ODMatrix-rest task."""

    array_from: Optional[Any] = Field(None, alias='arrayFrom', description='Источник FROM')
    array_to: Optional[Any] = Field(None, alias='arrayTo', description='Источник TO')
    seconds: Optional[bool] = Field(None, description='Seconds')
    epsg_code: Optional[int] = Field(None, alias='epsgCode', description='EpsgCode')
    transport_type: Optional[str] = Field(None, alias='transportType', description='Transport type')

class NetengineAvailabilityareaStartParameters(BaseStartParameters):
    """Start parameters for netEngine:availabilityArea task."""

    proccessing_type: Optional[str] = Field(None, alias='proccessingType', description='Тип таски')
    provider_name: Optional[ProvidernameType] = Field(None, alias='providerName', description='Провайдер зоны доступности')
    source_layer: Optional[SourceEqlConfig] = Field(None, alias='sourceLayer', description='Источник')
    target_layer: Optional[LayerReferenceConfig] = Field(None, alias='targetLayer', description='Целевой слой')
    duration_expression: Optional[str] = Field(None, alias='durationExpression', description='Продолжительность маршрута')
    id_attribute_name: Optional[str] = Field(None, alias='idAttributeName', description='Имя Id атрибута')
    geometry_attribute_name: Optional[str] = Field(None, alias='geometryAttributeName', description='Имя атрибута с геометрией')
    duration_attribute_name: Optional[str] = Field(None, alias='durationAttributeName', description='Имя атрибута продолжительности')
    base_object_id_attribute_name: Optional[str] = Field(None, alias='baseObjectIdAttributeName', description='Имя атрибута с базовым Id')
    route_center_x_attribute_name: Optional[str] = Field(None, alias='routeCenterXAttributeName', description='RouteCenterXAttributeName')
    route_center_y_attribute_name: Optional[str] = Field(None, alias='routeCenterYAttributeName', description='RouteCenterYAttributeName')

class NetengineAvailabilityarearestStartParameters(BaseStartParameters):
    """Start parameters for netEngine:availabilityAreaRest task."""

    provider_name: Optional[ProvidernameType] = Field(None, alias='providerName', description='Название провайдера')
    x: Optional[float] = Field(None, description='Координата X')
    y: Optional[float] = Field(None, description='Координата Y')
    duration: Optional[float] = Field(None, description='Длительность пути')
    sr_in: Optional[int] = Field(None, alias='srIn', description='Sr входных координат')
    sr_out: Optional[int] = Field(None, alias='srOut', description='Sr результирующей геометрии')

class NetengineRouteStartParameters(BaseStartParameters):
    """Start parameters for netEngine:route task."""

    provider_name: Optional[ProvidernameType] = Field(None, alias='providerName', description='Название провайдера')
    x1: Optional[float] = Field(None, description='Стартовая X')
    y1: Optional[float] = Field(None, description='Стартовая Y')
    x2: Optional[float] = Field(None, description='Конечная X')
    y2: Optional[float] = Field(None, description='Конечная Y')
    sr_in: Optional[int] = Field(None, alias='srIn', description='Sr входных координат')
    sr_out: Optional[int] = Field(None, alias='srOut', description='Sr результирующей геометрии')

class NetengineTspStartParameters(BaseStartParameters):
    """Start parameters for netEngine:tsp task."""

    provider_name: Optional[ProvidernameType] = Field(None, alias='providerName', description='Название провайдера')
    sr_in: Optional[int] = Field(None, alias='srIn', description='Sr входных координат')
    sr_out: Optional[int] = Field(None, alias='srOut', description='Sr результирующей геометрии')

class ChatserverworkerMessagingprocessStartParameters(BaseStartParameters):
    """Start parameters for ChatServerWorker:messaging/process task."""

    action: Optional[ActionType] = Field(None, description='Action')
    channel_id: Optional[str] = Field(None, description='Channel ID')
    content: Optional[str] = Field(None, description='Message content')
    context: Optional[Any] = Field(None, description='Context')

class ChatserverworkerMessagingchannelsStartParameters(BaseStartParameters):
    """Start parameters for ChatServerWorker:messaging/channels task."""

    limit: Optional[str] = Field(None, description='Limit')
    offset: Optional[str] = Field(None, description='Offset')

class ChatserverworkerMessagingmessagesStartParameters(BaseStartParameters):
    """Start parameters for ChatServerWorker:messaging/messages task."""

    channel_id: Optional[str] = Field(None, description='Channel ID')
    limit: Optional[str] = Field(None, description='Limit')
    cursor: Optional[str] = Field(None, description='Cursor')

class ChatserverworkerMessagingmessageStartParameters(BaseStartParameters):
    """Start parameters for ChatServerWorker:messaging/message task."""

    message_id: Optional[str] = Field(None, description='Message ID')

class ChatserverworkerMessagingunreadStartParameters(BaseStartParameters):
    """Start parameters for ChatServerWorker:messaging/unread task."""

    pass

class ChatserverworkerAppslistStartParameters(BaseStartParameters):
    """Start parameters for ChatServerWorker:apps/list task."""

    pass

class ChatserverworkerAppsactionStartParameters(BaseStartParameters):
    """Start parameters for ChatServerWorker:apps/action task."""

    app_id: Optional[str] = Field(None, description='App ID')
    action_id: Optional[str] = Field(None, description='Action ID')
    path: Optional[str] = Field(None, description='Endpoint path')
    method: Optional[str] = Field(None, description='HTTP method')
    params: Optional[Any] = Field(None, description='Query params')
    body: Optional[Any] = Field(None, description='Request body')

class ChatserverworkerMessagingiceserversStartParameters(BaseStartParameters):
    """Start parameters for ChatServerWorker:messaging/ice-servers task."""

    pass

class ChatworkerChatprocessStartParameters(BaseStartParameters):
    """Start parameters for ChatWorker:chat/process task."""

    message: Optional[str] = Field(None, description='User Message')
    session_id: Optional[str] = Field(None, description='Session ID')
    context: Optional[Any] = Field(None, description='UI Context')
    model: Optional[ModelType] = Field(None, description='Model')

class ChatworkerChatrestStartParameters(BaseStartParameters):
    """Start parameters for ChatWorker:chat/rest task."""

    message: Optional[str] = Field(None, description='User Message')
    session_id: Optional[str] = Field(None, description='Session ID')
    context: Optional[Any] = Field(None, description='UI Context')
    model: Optional[ModelType] = Field(None, description='Model')

class ChatworkerChathistoryStartParameters(BaseStartParameters):
    """Start parameters for ChatWorker:chat/history task."""

    usr: Optional[str] = Field(None, alias='_usr', description='User ID')
    command: Optional[str] = Field(None, description='Command Filter')
    current_map: Optional[str] = Field(None, description='Map Filter')
    limit: Optional[int] = Field(None, description='Limit')
    offset: Optional[int] = Field(None, description='Offset')

class ChatworkerChathistoryrequestStartParameters(BaseStartParameters):
    """Start parameters for ChatWorker:chat/history/request task."""

    request_ids: Optional[Any] = Field(None, description='Request IDs')

class ChatworkerChatsuggestStartParameters(BaseStartParameters):
    """Start parameters for ChatWorker:chat/suggest task."""

    q: Optional[str] = Field(None, description='Search Query')

class UniversalsearchUniversalsearchsearchresultStartParameters(BaseStartParameters):
    """Start parameters for universalSearch:universalsearch/searchResult task."""

    search_id: Optional[str] = Field(None, alias='searchId', description='SearchId')
    layer: Optional[str] = Field(None, description='Layer')
    limit: Optional[int] = Field(None, description='Limit')
    offset: Optional[int] = Field(None, description='Offset')

class UniversalsearchUniversalsearchStartParameters(BaseStartParameters):
    """Start parameters for universalSearch:UniversalSearch task."""

    source_layers: Optional[SourceEqlConfig] = Field(None, alias='sourceLayers', description='Источник')
    search_limit: Optional[int] = Field(None, alias='searchLimit', description='Search limit')
    attributes: Optional[List[str]] = Field(None, description='Attributes to search')
    search_id: Optional[str] = Field(None, alias='searchId', description='SearchId')
    text_to_search: Optional[str] = Field(None, alias='textToSearch', description='TextToSearch')

class GeocodetaskStartParameters(BaseStartParameters):
    """Start parameters for geocodeTask:geocodeTask task."""

    geocode_provider_name: Optional[str] = Field(None, alias='geocodeProviderName', description='Провайдер')
    source_layer: Optional[SourceEqlConfig] = Field(None, alias='sourceLayer', description='Источник')
    target_layer: Optional[LayerReferenceConfig] = Field(None, alias='targetLayer', description='Целевой слой')
    geocode_from_geometry: Optional[bool] = Field(None, alias='geocodeFromGeometry', description='Геокодирование из геометрии')
    geocode_address_attribute_name: Optional[str] = Field(None, alias='geocodeAddressAttributeName', description='Имя атрибута с адресом для геокодирования')
    geocode_attribute_name: Optional[str] = Field(None, alias='geocodeAttributeName', description='Имя атрибута для результата геокодирования')

class ImportexportImportexportdataschemaStartParameters(BaseStartParameters):
    """Start parameters for importExport:importExport/dataSchema task."""

    source_file_name: Optional[str] = Field(None, alias='source_fileName', description='Имя файла')
    source_coord_source_fields: Optional[List[str]] = Field(None, alias='source_coordSourceFields', description='Поля с координатами')
    source_column_delimiter: Optional[str] = Field(None, alias='source_columnDelimiter', description='Символ разделителя')
    source_spatial_reference: Optional[int] = Field(None, alias='source_spatialReference', description='SpatialReference Id.')
    source_is_wkt: Optional[bool] = Field(None, alias='source_isWkt', description='Геометрия в WKT')
    source_attribute_name_row_number: Optional[int] = Field(None, alias='source_attributeNameRowNumber', description='AttributeNameRowNumber')
    source_alias_row_number: Optional[int] = Field(None, alias='source_aliasRowNumber', description='AliasRowNumber')
    source_first_data_row_number: Optional[int] = Field(None, alias='source_firstDataRowNumber', description='FirstDataRowNumber')

class GeoprocessingGeoprocessingschemaStartParameters(BaseStartParameters):
    """Start parameters for geoProcessing:geoprocessing/schema task."""

    proccessing_type: Optional[str] = Field(None, alias='proccessingType', description='Тип таски')
    source_layer: Optional[SourceEqlConfig] = Field(None, alias='sourceLayer', description='Источник')
    target_layer: Optional[LayerReferenceConfig] = Field(None, alias='targetLayer', description='Целевой слой')
    rad_attribute_name: Optional[str] = Field(None, alias='radAttributeName', description='Имя атрибута для размера буфера')
    base_object_id_attribute_name: Optional[str] = Field(None, alias='baseObjectIdAttributeName', description='Имя атрибута для id исходной фичи')
    radii: Optional[List[str]] = Field(None, description='Радиусы для построения буффера')
    attribute_radii: Optional[List[str]] = Field(None, alias='attributeRadii', description='Радиусы из атрибутов для построения буффера')
    attribute_to_copy: Optional[List[str]] = Field(None, alias='attributeToCopy', description='Атрибуты для копирования в целевой слой')
    materialized_view: Optional[bool] = Field(None, alias='materializedView', description='Материализовать View источника для сложных EQL')

class GeoprocessingBufferStartParameters(BaseStartParameters):
    """Start parameters for geoProcessing:buffer task."""

    proccessing_type: Optional[str] = Field(None, alias='proccessingType', description='Тип таски')
    source_layer: Optional[SourceEqlConfig] = Field(None, alias='sourceLayer', description='Источник')
    target_layer: Optional[LayerReferenceConfig] = Field(None, alias='targetLayer', description='Целевой слой')
    rad_attribute_name: Optional[str] = Field(None, alias='radAttributeName', description='Имя атрибута для размера буфера')
    base_object_id_attribute_name: Optional[str] = Field(None, alias='baseObjectIdAttributeName', description='Имя атрибута для id исходной фичи')
    radii: Optional[List[str]] = Field(None, description='Радиусы для построения буффера')
    attribute_radii: Optional[List[str]] = Field(None, alias='attributeRadii', description='Радиусы из атрибутов для построения буффера')
    attribute_to_copy: Optional[List[str]] = Field(None, alias='attributeToCopy', description='Атрибуты для копирования в целевой слой')
    materialized_view: Optional[bool] = Field(None, alias='materializedView', description='Материализовать View источника для сложных EQL')

class GeoprocessingCopyStartParameters(BaseStartParameters):
    """Start parameters for geoProcessing:copy task."""

    proccessing_type: Optional[str] = Field(None, alias='proccessingType', description='Тип таски')
    source_layer: Optional[SourceEqlConfig] = Field(None, alias='sourceLayer', description='Источник')
    target_layer: Optional[LayerReferenceConfig] = Field(None, alias='targetLayer', description='Целевой слой')
    columns_mapping: Optional[Any] = Field(None, alias='columnsMapping', description='Маппинг исходного атрибута на целевой')
    materialized_view: Optional[bool] = Field(None, alias='materializedView', description='Материализовать View источника для сложных EQL')

class GeoprocessingUpdateStartParameters(BaseStartParameters):
    """Start parameters for geoProcessing:update task."""

    proccessing_type: Optional[str] = Field(None, alias='proccessingType', description='Тип таски')
    source_layer: Optional[SourceEqlConfig] = Field(None, alias='sourceLayer', description='Источник')
    target_layer: Optional[LayerReferenceConfig] = Field(None, alias='targetLayer', description='Целевой слой')
    materialized_view: Optional[bool] = Field(None, alias='materializedView', description='Материализовать View источника для сложных EQL')

class GeoprocessingDeleteStartParameters(BaseStartParameters):
    """Start parameters for geoProcessing:delete task."""

    proccessing_type: Optional[str] = Field(None, alias='proccessingType', description='Тип таски')
    source_layer: Optional[SourceEqlConfig] = Field(None, alias='sourceLayer', description='Источник')
    target_layer: Optional[LayerReferenceConfig] = Field(None, alias='targetLayer', description='Целевой слой')
    materialized_view: Optional[bool] = Field(None, alias='materializedView', description='Материализовать View источника для сложных EQL')

class GeoprocessingOverlayStartParameters(BaseStartParameters):
    """Start parameters for geoProcessing:overlay task."""

    proccessing_type: Optional[str] = Field(None, alias='proccessingType', description='Тип таски')
    source_layer: Optional[SourceEqlConfig] = Field(None, alias='sourceLayer', description='Источник')
    target_layer: Optional[LayerReferenceConfig] = Field(None, alias='targetLayer', description='Целевой слой')
    overlay_layer: Optional[SourceEqlConfig] = Field(None, alias='overlayLayer', description='Overlay слой')
    attributes_to_copy: Optional[List[str]] = Field(None, alias='attributesToCopy', description='Атрибуты, которые нужно скопировать в результирующий слой')
    operation: Optional[OperationType] = Field(None, description='Тип операции')
    materialized_view: Optional[bool] = Field(None, alias='materializedView', description='Материализовать View источника для сложных EQL')

class GeoprocessingUnionStartParameters(BaseStartParameters):
    """Start parameters for geoProcessing:union task."""

    proccessing_type: Optional[str] = Field(None, alias='proccessingType', description='Тип таски')
    source_layer: Optional[SourceEqlConfig] = Field(None, alias='sourceLayer', description='Источник')
    target_layer: Optional[LayerReferenceConfig] = Field(None, alias='targetLayer', description='Целевой слой')
    group_attribute: Optional[str] = Field(None, alias='groupAttribute', description='Атрибут группировки')
    materialized_view: Optional[bool] = Field(None, alias='materializedView', description='Материализовать View источника для сложных EQL')

class GeoprocessingValidategeometryStartParameters(BaseStartParameters):
    """Start parameters for geoProcessing:validateGeometry task."""

    proccessing_type: Optional[str] = Field(None, alias='proccessingType', description='Тип таски')
    source_layer: Optional[SourceEqlConfig] = Field(None, alias='sourceLayer', description='Источник')
    target_layer: Optional[LayerReferenceConfig] = Field(None, alias='targetLayer', description='Целевой слой')
    base_object_id_attribute_name: Optional[str] = Field(None, alias='baseObjectIdAttributeName', description='Имя атрибута для id исходной фичи')
    invalid_reason_column: Optional[str] = Field(None, alias='invalidReasonColumn', description='Имя атрибута для результата валидации')
    materialized_view: Optional[bool] = Field(None, alias='materializedView', description='Материализовать View источника для сложных EQL')

class GeoprocessingFixgeometryStartParameters(BaseStartParameters):
    """Start parameters for geoProcessing:fixGeometry task."""

    proccessing_type: Optional[str] = Field(None, alias='proccessingType', description='Тип таски')
    target_layer: Optional[LayerReferenceConfig] = Field(None, alias='targetLayer', description='Целевой слой')

class EqlhelpworkerEqlhelpsuggestStartParameters(BaseStartParameters):
    """Start parameters for EqlHelpWorker:eql-help/suggest task."""

    query: Optional[str] = Field(None, description='Search query')
    lang: Optional[str] = Field(None, description='Language (ru/en)')
    limit: Optional[str] = Field(None, description='Max results')

class EqlhelpworkerEqlhelpfunctionsStartParameters(BaseStartParameters):
    """Start parameters for EqlHelpWorker:eql-help/functions task."""

    lang: Optional[str] = Field(None, description='Language (ru/en)')
    offset: Optional[str] = Field(None, description='Offset')
    limit: Optional[str] = Field(None, description='Limit')

class PythonservicePythonrunnerprepareStartParameters(BaseStartParameters):
    """Start parameters for pythonService:pythonrunner/prepare task."""

    resource_id: Optional[str] = Field(None, alias='ResourceId', description='ResourceId')
    is_notebook: Optional[bool] = Field(None, alias='isNotebook', description='Is notebook flag')

class PythonservicePythonrunnerstopStartParameters(BaseStartParameters):
    """Start parameters for pythonService:pythonrunner/stop task."""

    resource_id: Optional[str] = Field(None, alias='ResourceId', description='ResourceId')
    is_notebook: Optional[bool] = Field(None, alias='isNotebook', description='Is notebook flag')

class PythonservicePythonrunnerstatsStartParameters(BaseStartParameters):
    """Start parameters for pythonService:pythonrunner/stats task."""

    resource_id: Optional[str] = Field(None, alias='ResourceId', description='ResourceId')
    is_notebook: Optional[bool] = Field(None, alias='isNotebook', description='Is notebook flag')

class PythonservicePythonrunnerapprovealiveStartParameters(BaseStartParameters):
    """Start parameters for pythonService:pythonrunner/approveAlive task."""

    resource_id: Optional[str] = Field(None, alias='ResourceId', description='ResourceId')
    is_notebook: Optional[bool] = Field(None, alias='isNotebook', description='Is notebook flag')

class PythonservicePythonrunnerrunStartParameters(BaseStartParameters):
    """Start parameters for pythonService:pythonrunner/run task."""

    resource_id: Optional[str] = Field(None, alias='ResourceId', description='ResourceId')
    file_name: Optional[str] = Field(None, alias='fileName', description='Имя файла')
    method_name: Optional[str] = Field(None, alias='methodName', description='Имя метода')

class PythonservicePythonrunnerrunnotebookStartParameters(BaseStartParameters):
    """Start parameters for pythonService:pythonrunner/run-notebook task."""

    resource_id: Optional[str] = Field(None, alias='ResourceId', description='ResourceId')

class PythonservicePythonrunnerdetailsStartParameters(BaseStartParameters):
    """Start parameters for pythonService:pythonrunner/details task."""

    resource_id: Optional[Any] = Field(None, alias='ResourceId', description='ResourceId')

class PythonservicePythonrunneralldetailsStartParameters(BaseStartParameters):
    """Start parameters for pythonService:pythonrunner/all-details task."""

    resource_id: Optional[Any] = Field(None, alias='ResourceId', description='ResourceId')

def create_start_parameters(task_type: str, **kwargs) -> BaseStartParameters:
    """
    Factory function to create start parameters based on task type.

    Args:
        task_type: Type of the task (format: "mainType:subType")
        **kwargs: Parameters for the specific task type

    Returns:
        Appropriate start parameters model
    """
    models_map = {
        "netEngine:ODMatrix": NetengineOdmatrixStartParameters,
        "netEngine:ODMatrix-rest": NetengineOdmatrixrestStartParameters,
        "netEngine:availabilityArea": NetengineAvailabilityareaStartParameters,
        "netEngine:availabilityAreaRest": NetengineAvailabilityarearestStartParameters,
        "netEngine:route": NetengineRouteStartParameters,
        "netEngine:tsp": NetengineTspStartParameters,
        "ChatServerWorker:messaging/process": ChatserverworkerMessagingprocessStartParameters,
        "ChatServerWorker:messaging/channels": ChatserverworkerMessagingchannelsStartParameters,
        "ChatServerWorker:messaging/messages": ChatserverworkerMessagingmessagesStartParameters,
        "ChatServerWorker:messaging/message": ChatserverworkerMessagingmessageStartParameters,
        "ChatServerWorker:messaging/unread": ChatserverworkerMessagingunreadStartParameters,
        "ChatServerWorker:apps/list": ChatserverworkerAppslistStartParameters,
        "ChatServerWorker:apps/action": ChatserverworkerAppsactionStartParameters,
        "ChatServerWorker:messaging/ice-servers": ChatserverworkerMessagingiceserversStartParameters,
        "ChatWorker:chat/process": ChatworkerChatprocessStartParameters,
        "ChatWorker:chat/rest": ChatworkerChatrestStartParameters,
        "ChatWorker:chat/history": ChatworkerChathistoryStartParameters,
        "ChatWorker:chat/history/request": ChatworkerChathistoryrequestStartParameters,
        "ChatWorker:chat/suggest": ChatworkerChatsuggestStartParameters,
        "universalSearch:universalsearch/searchResult": UniversalsearchUniversalsearchsearchresultStartParameters,
        "universalSearch:UniversalSearch": UniversalsearchUniversalsearchStartParameters,
        "geocodeTask:geocodeTask": GeocodetaskStartParameters,
        "importExport:importExport/dataSchema": ImportexportImportexportdataschemaStartParameters,
        # "importExport:importExport": Use conditional models instead
        "geoProcessing:geoprocessing/schema": GeoprocessingGeoprocessingschemaStartParameters,
        "geoProcessing:buffer": GeoprocessingBufferStartParameters,
        "geoProcessing:copy": GeoprocessingCopyStartParameters,
        "geoProcessing:update": GeoprocessingUpdateStartParameters,
        "geoProcessing:delete": GeoprocessingDeleteStartParameters,
        "geoProcessing:overlay": GeoprocessingOverlayStartParameters,
        "geoProcessing:union": GeoprocessingUnionStartParameters,
        "geoProcessing:validateGeometry": GeoprocessingValidategeometryStartParameters,
        "geoProcessing:fixGeometry": GeoprocessingFixgeometryStartParameters,
        "EqlHelpWorker:eql-help/suggest": EqlhelpworkerEqlhelpsuggestStartParameters,
        "EqlHelpWorker:eql-help/functions": EqlhelpworkerEqlhelpfunctionsStartParameters,
        "pythonService:pythonrunner/prepare": PythonservicePythonrunnerprepareStartParameters,
        "pythonService:pythonrunner/stop": PythonservicePythonrunnerstopStartParameters,
        "pythonService:pythonrunner/stats": PythonservicePythonrunnerstatsStartParameters,
        "pythonService:pythonrunner/approveAlive": PythonservicePythonrunnerapprovealiveStartParameters,
        "pythonService:pythonrunner/run": PythonservicePythonrunnerrunStartParameters,
        "pythonService:pythonrunner/run-notebook": PythonservicePythonrunnerrunnotebookStartParameters,
        "pythonService:pythonrunner/details": PythonservicePythonrunnerdetailsStartParameters,
        "pythonService:pythonrunner/all-details": PythonservicePythonrunneralldetailsStartParameters,
    }

    model_class = models_map.get(task_type)
    if not model_class:
        raise ValueError(f"Unknown task type: {task_type}")

    return model_class(**kwargs)

def create_task_prototype(
    task_type: str,
    start_parameters: BaseStartParameters,
    delay_date: Optional[datetime] = None,
    enabled: Optional[bool] = None,
    schedule: Optional[str] = None,
    start_if_previous_error: Optional[bool] = None,
    start_if_previous_not_finished: Optional[bool] = None,
    order: Optional[int] = None,
    description: Optional[str] = None
) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for task execution.
    
    Note: task_type can be in format "mainType:subType", but only mainType is used.
    """
    # Extract mainType from task_type (format: mainType or mainType:subType)
    main_type = task_type.split(':', 1)[0]
    
    sub_task = SubTaskSettingsDto(
        order=order,
        type=main_type,
        startParameters=start_parameters
    )
    
    return TaskPrototypeDto(
        delayDate=delay_date,
        enabled=enabled,
        schedule=schedule,
        startIfPreviousError=start_if_previous_error,
        startIfPreviousNotFinished=start_if_previous_not_finished,
        description=description,
        subTaskSettings=[sub_task]
    )

def create_netengine_odmatrix_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for netEngine:ODMatrix task."""
    start_params = NetengineOdmatrixStartParameters(**params)
    return create_task_prototype(
        task_type="netEngine",
        start_parameters=start_params
    )

def create_netengine_odmatrixrest_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for netEngine:ODMatrix-rest task."""
    start_params = NetengineOdmatrixrestStartParameters(**params)
    return create_task_prototype(
        task_type="netEngine",
        start_parameters=start_params
    )

def create_netengine_availabilityarea_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for netEngine:availabilityArea task."""
    start_params = NetengineAvailabilityareaStartParameters(**params)
    return create_task_prototype(
        task_type="netEngine",
        start_parameters=start_params
    )

def create_netengine_availabilityarearest_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for netEngine:availabilityAreaRest task."""
    start_params = NetengineAvailabilityarearestStartParameters(**params)
    return create_task_prototype(
        task_type="netEngine",
        start_parameters=start_params
    )

def create_netengine_route_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for netEngine:route task."""
    start_params = NetengineRouteStartParameters(**params)
    return create_task_prototype(
        task_type="netEngine",
        start_parameters=start_params
    )

def create_netengine_tsp_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for netEngine:tsp task."""
    start_params = NetengineTspStartParameters(**params)
    return create_task_prototype(
        task_type="netEngine",
        start_parameters=start_params
    )

def create_chatserverworker_messagingprocess_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for ChatServerWorker:messaging/process task."""
    start_params = ChatserverworkerMessagingprocessStartParameters(**params)
    return create_task_prototype(
        task_type="ChatServerWorker",
        start_parameters=start_params
    )

def create_chatserverworker_messagingchannels_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for ChatServerWorker:messaging/channels task."""
    start_params = ChatserverworkerMessagingchannelsStartParameters(**params)
    return create_task_prototype(
        task_type="ChatServerWorker",
        start_parameters=start_params
    )

def create_chatserverworker_messagingmessages_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for ChatServerWorker:messaging/messages task."""
    start_params = ChatserverworkerMessagingmessagesStartParameters(**params)
    return create_task_prototype(
        task_type="ChatServerWorker",
        start_parameters=start_params
    )

def create_chatserverworker_messagingmessage_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for ChatServerWorker:messaging/message task."""
    start_params = ChatserverworkerMessagingmessageStartParameters(**params)
    return create_task_prototype(
        task_type="ChatServerWorker",
        start_parameters=start_params
    )

def create_chatserverworker_messagingunread_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for ChatServerWorker:messaging/unread task."""
    start_params = ChatserverworkerMessagingunreadStartParameters(**params)
    return create_task_prototype(
        task_type="ChatServerWorker",
        start_parameters=start_params
    )

def create_chatserverworker_appslist_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for ChatServerWorker:apps/list task."""
    start_params = ChatserverworkerAppslistStartParameters(**params)
    return create_task_prototype(
        task_type="ChatServerWorker",
        start_parameters=start_params
    )

def create_chatserverworker_appsaction_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for ChatServerWorker:apps/action task."""
    start_params = ChatserverworkerAppsactionStartParameters(**params)
    return create_task_prototype(
        task_type="ChatServerWorker",
        start_parameters=start_params
    )

def create_chatserverworker_messagingiceservers_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for ChatServerWorker:messaging/ice-servers task."""
    start_params = ChatserverworkerMessagingiceserversStartParameters(**params)
    return create_task_prototype(
        task_type="ChatServerWorker",
        start_parameters=start_params
    )

def create_chatworker_chatprocess_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for ChatWorker:chat/process task."""
    start_params = ChatworkerChatprocessStartParameters(**params)
    return create_task_prototype(
        task_type="ChatWorker",
        start_parameters=start_params
    )

def create_chatworker_chatrest_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for ChatWorker:chat/rest task."""
    start_params = ChatworkerChatrestStartParameters(**params)
    return create_task_prototype(
        task_type="ChatWorker",
        start_parameters=start_params
    )

def create_chatworker_chathistory_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for ChatWorker:chat/history task."""
    start_params = ChatworkerChathistoryStartParameters(**params)
    return create_task_prototype(
        task_type="ChatWorker",
        start_parameters=start_params
    )

def create_chatworker_chathistoryrequest_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for ChatWorker:chat/history/request task."""
    start_params = ChatworkerChathistoryrequestStartParameters(**params)
    return create_task_prototype(
        task_type="ChatWorker",
        start_parameters=start_params
    )

def create_chatworker_chatsuggest_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for ChatWorker:chat/suggest task."""
    start_params = ChatworkerChatsuggestStartParameters(**params)
    return create_task_prototype(
        task_type="ChatWorker",
        start_parameters=start_params
    )

def create_universalsearch_universalsearchsearchresult_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for universalSearch:universalsearch/searchResult task."""
    start_params = UniversalsearchUniversalsearchsearchresultStartParameters(**params)
    return create_task_prototype(
        task_type="universalSearch",
        start_parameters=start_params
    )

def create_universalsearch_universalsearch_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for universalSearch:UniversalSearch task."""
    start_params = UniversalsearchUniversalsearchStartParameters(**params)
    return create_task_prototype(
        task_type="universalSearch",
        start_parameters=start_params
    )

def create_geocodetask_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for geocodeTask:geocodeTask task."""
    start_params = GeocodetaskStartParameters(**params)
    return create_task_prototype(
        task_type="geocodeTask",
        start_parameters=start_params
    )

def create_importexport_importexportdataschema_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for importExport:importExport/dataSchema task."""
    start_params = ImportexportImportexportdataschemaStartParameters(**params)
    return create_task_prototype(
        task_type="importExport",
        start_parameters=start_params
    )

def create_importexport_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for importExport:importExport task.

    DEPRECATED: Use create_importexport_job from importexport_conditional.py instead.
    This function provides conditional models for different source/target combinations.
    """
    # Import here to avoid circular dependency
    from .importexport_conditional import create_importexport_job as create_conditional_job
    return create_conditional_job(**params)

def create_geoprocessing_geoprocessingschema_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for geoProcessing:geoprocessing/schema task."""
    start_params = GeoprocessingGeoprocessingschemaStartParameters(**params)
    return create_task_prototype(
        task_type="geoProcessing",
        start_parameters=start_params
    )

def create_geoprocessing_buffer_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for geoProcessing:buffer task."""
    start_params = GeoprocessingBufferStartParameters(**params)
    return create_task_prototype(
        task_type="geoProcessing",
        start_parameters=start_params
    )

def create_geoprocessing_copy_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for geoProcessing:copy task."""
    start_params = GeoprocessingCopyStartParameters(**params)
    return create_task_prototype(
        task_type="geoProcessing",
        start_parameters=start_params
    )

def create_geoprocessing_update_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for geoProcessing:update task."""
    start_params = GeoprocessingUpdateStartParameters(**params)
    return create_task_prototype(
        task_type="geoProcessing",
        start_parameters=start_params
    )

def create_geoprocessing_delete_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for geoProcessing:delete task."""
    start_params = GeoprocessingDeleteStartParameters(**params)
    return create_task_prototype(
        task_type="geoProcessing",
        start_parameters=start_params
    )

def create_geoprocessing_overlay_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for geoProcessing:overlay task."""
    start_params = GeoprocessingOverlayStartParameters(**params)
    return create_task_prototype(
        task_type="geoProcessing",
        start_parameters=start_params
    )

def create_geoprocessing_union_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for geoProcessing:union task."""
    start_params = GeoprocessingUnionStartParameters(**params)
    return create_task_prototype(
        task_type="geoProcessing",
        start_parameters=start_params
    )

def create_geoprocessing_validategeometry_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for geoProcessing:validateGeometry task."""
    start_params = GeoprocessingValidategeometryStartParameters(**params)
    return create_task_prototype(
        task_type="geoProcessing",
        start_parameters=start_params
    )

def create_geoprocessing_fixgeometry_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for geoProcessing:fixGeometry task."""
    start_params = GeoprocessingFixgeometryStartParameters(**params)
    return create_task_prototype(
        task_type="geoProcessing",
        start_parameters=start_params
    )

def create_eqlhelpworker_eqlhelpsuggest_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for EqlHelpWorker:eql-help/suggest task."""
    start_params = EqlhelpworkerEqlhelpsuggestStartParameters(**params)
    return create_task_prototype(
        task_type="EqlHelpWorker",
        start_parameters=start_params
    )

def create_eqlhelpworker_eqlhelpfunctions_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for EqlHelpWorker:eql-help/functions task."""
    start_params = EqlhelpworkerEqlhelpfunctionsStartParameters(**params)
    return create_task_prototype(
        task_type="EqlHelpWorker",
        start_parameters=start_params
    )

def create_pythonservice_pythonrunnerprepare_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for pythonService:pythonrunner/prepare task."""
    start_params = PythonservicePythonrunnerprepareStartParameters(**params)
    return create_task_prototype(
        task_type="pythonService",
        start_parameters=start_params
    )

def create_pythonservice_pythonrunnerstop_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for pythonService:pythonrunner/stop task."""
    start_params = PythonservicePythonrunnerstopStartParameters(**params)
    return create_task_prototype(
        task_type="pythonService",
        start_parameters=start_params
    )

def create_pythonservice_pythonrunnerstats_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for pythonService:pythonrunner/stats task."""
    start_params = PythonservicePythonrunnerstatsStartParameters(**params)
    return create_task_prototype(
        task_type="pythonService",
        start_parameters=start_params
    )

def create_pythonservice_pythonrunnerapprovealive_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for pythonService:pythonrunner/approveAlive task."""
    start_params = PythonservicePythonrunnerapprovealiveStartParameters(**params)
    return create_task_prototype(
        task_type="pythonService",
        start_parameters=start_params
    )

def create_pythonservice_pythonrunnerrun_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for pythonService:pythonrunner/run task."""
    start_params = PythonservicePythonrunnerrunStartParameters(**params)
    return create_task_prototype(
        task_type="pythonService",
        start_parameters=start_params
    )

def create_pythonservice_pythonrunnerrunnotebook_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for pythonService:pythonrunner/run-notebook task."""
    start_params = PythonservicePythonrunnerrunnotebookStartParameters(**params)
    return create_task_prototype(
        task_type="pythonService",
        start_parameters=start_params
    )

def create_pythonservice_pythonrunnerdetails_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for pythonService:pythonrunner/details task."""
    start_params = PythonservicePythonrunnerdetailsStartParameters(**params)
    return create_task_prototype(
        task_type="pythonService",
        start_parameters=start_params
    )

def create_pythonservice_pythonrunneralldetails_job(**params) -> TaskPrototypeDto:
    """Create TaskPrototypeDto for pythonService:pythonrunner/all-details task."""
    start_params = PythonservicePythonrunneralldetailsStartParameters(**params)
    return create_task_prototype(
        task_type="pythonService",
        start_parameters=start_params
    )
