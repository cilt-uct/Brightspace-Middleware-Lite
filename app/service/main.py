import asyncio
import uvicorn
import signal

from app import app as app_fastapi
from core.settings import settings

class Server(uvicorn.Server):
    """ Uvicorn server overrides signals """
    def handle_exit(self, sig: int, frame) -> None:
        return super().handle_exit(sig, frame)

async def shutdown_signal(loop, stop_event):
    """Wait for a signal and then stop the loop"""
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

async def main(workers:int = 4):
    "Run FastAPI"
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    await shutdown_signal(loop, stop_event)

    server = uvicorn.Server(config=uvicorn.Config(app_fastapi,
                                    port=9090, host="0.0.0.0",
                                    root_path=settings.app_prefix,
                                    forwarded_allow_ips="*",
                                    workers=workers,
                                    log_level=settings.log_level,
                                    loop="asyncio"))

    server_task = asyncio.create_task(server.serve())

    # Wait until a stop signal is received
    await stop_event.wait()

    # When a signal is received, shutdown the server
    server.should_exit = True
    await server_task

if __name__ == "__main__":
    # Run applications
    asyncio.run(main())
