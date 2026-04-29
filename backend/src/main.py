import asyncio
import logging

from reboot.aio.applications import Application

from servicers.todo import TodoListServicer, UserServicer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def main() -> None:
    application = Application(
        servicers=[UserServicer, TodoListServicer],
    )
    await application.run()


if __name__ == "__main__":
    asyncio.run(main())
