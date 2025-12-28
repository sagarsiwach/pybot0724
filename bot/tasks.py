import asyncio
from .production import increase_production_async
from .storage import increase_storage_async


async def handle_task(task_type, count, session_manager, add_log):
    """
    Handle specific tasks based on task type.
    """
    # Get cookies once and reuse them
    cookies = await session_manager.get_cookies()
    
    if task_type == '1':
        add_log("Starting storage increase process.")
        await increase_storage_async(
            session_manager.username,
            session_manager.password,
            count,
            session_manager.conn,
            cookies=cookies  # Reuse existing session
        )
        add_log("Storage process completed. Returning back to lobby.")
    elif task_type == '2':
        add_log("Starting production increase process.")
        await increase_production_async(
            session_manager.username,
            session_manager.password,
            count,
            session_manager.conn,
            cookies=cookies  # Reuse existing session
        )
        add_log("Production process completed. Returning back to lobby.")


async def loop_task_until_escape(task_type, session_manager, add_log):
    """
    Automate looping task until escape key is pressed.
    """
    add_log(f"Starting {task_type} loop process. Press 'Escape' to stop.")
    
    # Get cookies once and reuse them for all iterations
    cookies = await session_manager.get_cookies()
    
    try:
        while True:
            if task_type == '1':
                await increase_storage_async(
                    session_manager.username,
                    session_manager.password,
                    1,  # Single loop iteration
                    session_manager.conn,
                    cookies=cookies  # Reuse existing session
                )
                add_log("Storage increased.")
            elif task_type == '2':
                await increase_production_async(
                    session_manager.username,
                    session_manager.password,
                    1,  # Single loop iteration
                    session_manager.conn,
                    cookies=cookies  # Reuse existing session
                )
                add_log("Production increased.")
    except asyncio.CancelledError:
        add_log(f"{task_type} loop process stopped. Returning back to lobby.")
