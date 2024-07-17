import asyncio
from production import increase_production_async, increase_storage_async

async def handle_task(task_type, count, cookies, add_log):
    if task_type == '1':
        add_log("Starting storage increase process.")
        for i in range(count):
            await increase_storage_async(1, cookies)
            add_log(f"Storage increased: {i + 1} out of {count} completed")
        add_log("Storage process completed. Returning back to lobby.")
    elif task_type == '2':
        add_log("Starting production increase process.")
        for i in range(count):
            await increase_production_async(1, cookies)
            add_log(f"Production increased: {i + 1} out of {count} completed")
        add_log("Production process completed. Returning back to lobby.")
