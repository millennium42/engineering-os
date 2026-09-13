from __future__ import annotations

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
        OpenHandsIsolatedTaskInput,
        OpenHandsMessageInput,
    )
    from engos.supervised_activities import (
        get_git_worktree_status,
        normalize_worktree_permissions,
        record_supervised_evidence,
    )


@workflow.defn
class OpenHandsSupervisedTaskWorkflow:
    @workflow.run
    async def run(self, data: OpenHandsIsolatedTaskInput) -> dict[str, str]:
        if not data.run:
            raise ValueError("OpenHandsSupervisedTaskWorkflow requires run=true")

        retry = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_attempts=3,
        )

        worktree_path = await workflow.execute_activity(
            create_git_worktree,
            GitWorktreeInput(
                repo_path=data.repo_path,
                worktree_path=data.worktree_path,
                branch_name=data.branch_name,
                base_ref=data.base_ref,
            ),
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry,
        )

        host_root = data.host_projects_root.rstrip("/")
        container_root = data.openhands_projects_root.rstrip("/")
        if not worktree_path.startswith(host_root + "/"):
            raise ValueError(f"Worktree {worktree_path} is outside {host_root}")

        openhands_working_dir = container_root + worktree_path[len(host_root):]
        conversation_id = str(workflow.uuid7())
        message_id = str(workflow.uuid7())

        conversation_id = await workflow.execute_activity(
            create_openhands_conversation,
            OpenHandsConversationInput(
                working_dir=openhands_working_dir,
                model=data.model,
                base_url=data.base_url,
                conversation_id=conversation_id,
                worktree=False,
            ),
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry,
        )

        await workflow.execute_activity(
            send_openhands_message,
            OpenHandsMessageInput(
                conversation_id=conversation_id,
                message=(f"AUTHORIZED_WORKSPACE_ROOT: {openhands_working_dir}\n" f"All file reads, writes, edits and terminal operations for this task MUST stay inside this directory. " f"Never use /workspace or any other project directory. Use absolute paths rooted at {openhands_working_dir}.\n\n" f"TASK:\n{data.message}"),
                message_id=message_id,
                run=True,
            ),
            start_to_close_timeout=timedelta(seconds=20),
            retry_policy=retry,
        )

        status = "unknown"

        for _ in range(360):
            status = await workflow.execute_activity(
                get_openhands_conversation_status,
                conversation_id,
                start_to_close_timeout=timedelta(seconds=15),
                retry_policy=retry,
            )

            if status in {"finished", "error", "stuck"}:
                break

            await workflow.sleep(timedelta(seconds=5))
        else:
            status = "timeout"

        await workflow.execute_activity(
            normalize_worktree_permissions,
            worktree_path,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry,
        )

        git_status = await workflow.execute_activity(
            get_git_worktree_status,
            worktree_path,
            start_to_close_timeout=timedelta(seconds=15),
            retry_policy=retry,
        )

        info = workflow.info()
        evidence_dir = await workflow.execute_activity(
            record_supervised_evidence,
            {
                "workflow_id": info.workflow_id,
                "run_id": info.run_id,
                "repo_path": data.repo_path,
                "worktree_path": worktree_path,
                "branch_name": data.branch_name,
                "base_ref": data.base_ref,
                "model": data.model,
                "base_url": data.base_url,
                "message": data.message,
                "conversation_id": conversation_id,
                "message_id": message_id,
                "execution_status": status,
                "git_status": git_status,
            },
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry,
        )

        if not git_status:
            raise RuntimeError("OpenHands reported finished but produced no Git-visible changes")

        if status != "finished":
            raise RuntimeError(
                f"OpenHands ended with status={status}; git_status={git_status!r}"
            )

        return {
            "worktree_path": worktree_path,
            "openhands_working_dir": openhands_working_dir,
            "conversation_id": conversation_id,
            "message_id": message_id,
            "execution_status": status,
            "git_status": git_status,
        }
