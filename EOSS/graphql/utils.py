import asyncio
from concurrent.futures import ProcessPoolExecutor
from asgiref.sync import async_to_sync, sync_to_async


"""
    - Oftentimes, CPU bound tasks will need to be scheduled for execution in an async event loop. When this
        is this case, it is optimal to run the CPU bound task in a separate process. This ensures both the python
        GIL and async event loop isn't blocked
        
    - To do this, simply import the _proc function and pass it a SYNCHRONOUS function and any parameters
"""

async def _proc(func, *args, debug=False):
    loop = asyncio.get_running_loop()
    result = None

    # --> Run in current process if debugging
    if debug is True:
        return await sync_to_async(func)(*args)

    # --> Run in new process for production
    with ProcessPoolExecutor(max_workers=1) as pool:
        return await loop.run_in_executor(pool, func, *args)
