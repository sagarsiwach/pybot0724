import asyncio
from production import increase_production_async
from storage import increase_storage_async


async def handle_task(task_type, count, session_manager, add_log):
    """
    Handle specific tasks based on task type.
    """
    if task_type == '1':
        add_log("Starting storage increase process.")
        for i in range(count):
            await increase_storage_async(1, session_manager)
            add_log(f"Storage increased: {i + 1} out of {count} completed")
        add_log("Storage process completed. Returning back to lobby.")
    elif task_type == '2':
        add_log("Starting production increase process.")
        for i in range(count):
            await increase_production_async(1, session_manager)
            add_log(f"Production increased: {i + 1} out of {count} completed")
        add_log("Production process completed. Returning back to lobby.")


async def loop_task_until_escape(task_type, session_manager, add_log):
    """
    Automate looping task until escape key is pressed.
    """
    add_log(f"Starting {task_type} loop process. Press 'Escape' to stop.")
    try:
        while True:
            if task_type == '1':
                await increase_storage_async(1, session_manager)
                add_log("Storage increased.")
            elif task_type == '2':
                await increase_production_async(1, session_manager)
                add_log("Production increased.")
    except asyncio.CancelledError:
        add_log(f"{task_type} loop process stopped. Returning back to lobby.")
