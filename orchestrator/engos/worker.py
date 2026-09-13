import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from engos.activities import (
    create_git_worktree,
    create_openhands_conversation,
    get_openhands_conversation_status,
    send_openhands_message,
)
from engos.workflows import (
    GitWorktreeWorkflow,
    OpenHandsIsolatedTaskWorkflow,
    HealthcheckWorkflow,
    OpenHandsStatusWorkflow,
    OpenHandsMessageWorkflow,
    OpenHandsCreateConversationWorkflow,
    OpenHandsPrepareTaskWorkflow,
)

from engos.supervised_activities import get_git_worktree_status, normalize_worktree_permissions, record_supervised_evidence
from engos.supervised_workflows import OpenHandsSupervisedTaskWorkflow


async def main() -> None:
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="engos-control",
        workflows=[
            GitWorktreeWorkflow,
            OpenHandsIsolatedTaskWorkflow,
            OpenHandsSupervisedTaskWorkflow,
            HealthcheckWorkflow,
            OpenHandsStatusWorkflow,
            OpenHandsMessageWorkflow,
            OpenHandsCreateConversationWorkflow,
            OpenHandsPrepareTaskWorkflow,
        ],
        activities=[
            create_git_worktree,
            create_openhands_conversation,
            get_openhands_conversation_status,
            send_openhands_message,
            normalize_worktree_permissions,
            get_git_worktree_status,
            record_supervised_evidence,
        ],
    )

    print("Engineering OS worker conectado em engos-control")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
