from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from engos.activities import (
        create_git_worktree,
        create_openhands_conversation,
        get_openhands_conversation_status,
        send_openhands_message,
    )
    from engos.models import (
        GitWorktreeInput,
        OpenHandsConversationInput,
        OpenHandsMessageInput,
        OpenHandsTaskInput,
        OpenHandsTaskResult,
        OpenHandsIsolatedTaskInput,
        OpenHandsIsolatedTaskResult,
    )


@workflow.defn
class HealthcheckWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        return f"Engineering OS Temporal OK: {name}"


@workflow.defn
class OpenHandsStatusWorkflow:
    @workflow.run
    async def run(self, conversation_id: str) -> str:
        return await workflow.execute_activity(
            get_openhands_conversation_status,
            conversation_id,
            start_to_close_timeout=timedelta(seconds=20),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_attempts=3,
            ),
        )


@workflow.defn
class OpenHandsMessageWorkflow:
    @workflow.run
    async def run(self, data: OpenHandsMessageInput) -> bool:
        message_data = OpenHandsMessageInput(
            conversation_id=data.conversation_id,
            message=data.message,
            message_id=data.message_id or str(workflow.uuid7()),
            run=data.run,
        )

        return await workflow.execute_activity(
            send_openhands_message,
            message_data,
            start_to_close_timeout=timedelta(seconds=20),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_attempts=3,
            ),
        )



@workflow.defn
class OpenHandsCreateConversationWorkflow:
    @workflow.run
    async def run(self, data: OpenHandsConversationInput) -> str:
        conversation_data = OpenHandsConversationInput(
            working_dir=data.working_dir,
            conversation_id=data.conversation_id or str(workflow.uuid7()),
            model=data.model,
            base_url=data.base_url,
            worktree=data.worktree,
        )

        return await workflow.execute_activity(
            create_openhands_conversation,
            conversation_data,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_attempts=3,
            ),
        )


@workflow.defn
class OpenHandsPrepareTaskWorkflow:
    @workflow.run
    async def run(self, data: OpenHandsTaskInput) -> OpenHandsTaskResult:
        conversation_id = str(workflow.uuid7())
        message_id = str(workflow.uuid7())

        conversation_data = OpenHandsConversationInput(
            working_dir=data.working_dir,
            model=data.model,
            base_url=data.base_url,
            conversation_id=conversation_id,
            worktree=data.worktree,
        )

        created_conversation_id = await workflow.execute_activity(
            create_openhands_conversation,
            conversation_data,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_attempts=3,
            ),
        )

        message_data = OpenHandsMessageInput(
            conversation_id=created_conversation_id,
            message=data.message,
            message_id=message_id,
            run=False,
        )

        await workflow.execute_activity(
            send_openhands_message,
            message_data,
            start_to_close_timeout=timedelta(seconds=20),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_attempts=3,
            ),
        )

        return OpenHandsTaskResult(
            conversation_id=created_conversation_id,
            message_id=message_id,
        )


@workflow.defn
class GitWorktreeWorkflow:
    @workflow.run
    async def run(self, data: GitWorktreeInput) -> str:
        return await workflow.execute_activity(
            create_git_worktree,
            data,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_attempts=3,
            ),
        )


@workflow.defn
class OpenHandsIsolatedTaskWorkflow:
    @workflow.run
    async def run(self, data: OpenHandsIsolatedTaskInput) -> OpenHandsIsolatedTaskResult:
        worktree_path = await workflow.execute_activity(
            create_git_worktree,
            GitWorktreeInput(
                repo_path=data.repo_path,
                worktree_path=data.worktree_path,
                branch_name=data.branch_name,
                base_ref=data.base_ref,
            ),
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(initial_interval=timedelta(seconds=1), maximum_attempts=3),
        )

        host_root = data.host_projects_root.rstrip("/")
        container_root = data.openhands_projects_root.rstrip("/")
        if not worktree_path.startswith(host_root + "/"):
            raise ValueError(f"Worktree {worktree_path} está fora de {host_root}")

        openhands_working_dir = container_root + worktree_path[len(host_root):]
        conversation_id = str(workflow.uuid7())
        message_id = str(workflow.uuid7())

        created_conversation_id = await workflow.execute_activity(
            create_openhands_conversation,
            OpenHandsConversationInput(
                working_dir=openhands_working_dir,
                model=data.model,
                base_url=data.base_url,
                conversation_id=conversation_id,
                worktree=False,
            ),
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(initial_interval=timedelta(seconds=1), maximum_attempts=3),
        )

        await workflow.execute_activity(
            send_openhands_message,
            OpenHandsMessageInput(
                conversation_id=created_conversation_id,
                message=data.message,
                message_id=message_id,
                run=data.run,
            ),
            start_to_close_timeout=timedelta(seconds=20),
            retry_policy=RetryPolicy(initial_interval=timedelta(seconds=1), maximum_attempts=3),
        )

        return OpenHandsIsolatedTaskResult(
            worktree_path=worktree_path,
            openhands_working_dir=openhands_working_dir,
            conversation_id=created_conversation_id,
            message_id=message_id,
        )
