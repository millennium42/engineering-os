import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from engos.activities import get_openhands_conversation_status
from engos.workflows import HealthcheckWorkflow, OpenHandsStatusWorkflow


async def main() -> None:
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="engos-control",
        workflows=[
            HealthcheckWorkflow,
            OpenHandsStatusWorkflow,
        ],
        activities=[
            get_openhands_conversation_status,
        ],
    )

    print("Engineering OS worker conectado em engos-control")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
