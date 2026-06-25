"""Example of creating a geoProcessing:buffer task prototype."""

from __future__ import annotations

from evergis_tools.tasks import TaskManager, TaskWaitOptions, create_progress_callback
from evergis_tools import Client
from evergis_tools.tasks.worker_models import (
    GeoprocessingBufferStartParameters,
    create_task_prototype,
    SourceEqlConfig,
    LayerReferenceConfig,
)

# Connection settings
client = Client()
username = client.account.get_user_info().username

def build_buffer_prototype() -> dict:
    """Return a dict with TaskPrototypeDto for building buffers."""
    start_parameters = GeoprocessingBufferStartParameters(
        proccessing_type="buffer",
        source_layer=SourceEqlConfig(layerName=f"{username}.realty3"),
        target_layer=LayerReferenceConfig(name=f"{username}.realty3_buffer2"),
        radii=["100", "250"],
        attribute_to_copy=["type", "price", "area"],
        base_object_id_attribute_name="id",
        rad_attribute_name="radius",
    )

    prototype = create_task_prototype(
        "geoProcessing:buffer",
        start_parameters=start_parameters.model_dump(by_alias=True, exclude_none=True),
        enabled=True,
        start_if_previous_error=True,
        start_if_previous_not_finished=False,
        order=0,
    )
    return prototype


if __name__ == "__main__":
    prototype = build_buffer_prototype()
    print(prototype.model_dump_json(indent=2, by_alias=True))
    
    task_manager = TaskManager(client)

    # Create progress callback using the utility
    progress_callback = create_progress_callback(check_interval=2.0)

    wait_for_completion = True
    # Wait options
    wait_options = TaskWaitOptions(
        timeout=300,
        check_interval=2,
        progress_callback=progress_callback
    ) if wait_for_completion else None

    # Run the task through TaskManager
    result = task_manager.create_and_run(
        task=prototype,
        wait_for_completion=wait_for_completion,
        wait_options=wait_options
    )
