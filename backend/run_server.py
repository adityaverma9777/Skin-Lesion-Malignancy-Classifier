import asyncio
import os
import sys

import uvicorn


def _safe_loop_exception_handler(loop: asyncio.AbstractEventLoop, context: dict) -> None:
    exc = context.get("exception")
    if isinstance(exc, ConnectionResetError) and "WinError 10054" in str(exc):
        # This is a common transient disconnect on Windows; ignore noisy callback tracebacks.
        return
    loop.default_exception_handler(context)


def main() -> None:
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    loop.set_exception_handler(_safe_loop_exception_handler)
    asyncio.set_event_loop(loop)

    config = uvicorn.Config(
        "app:app",
        host=host,
        port=port,
        loop="asyncio",
        log_level="info",
    )
    server = uvicorn.Server(config)
    loop.run_until_complete(server.serve())


if __name__ == "__main__":
    main()