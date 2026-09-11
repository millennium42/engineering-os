from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from engos.activities import get_openhands_conversation_status


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
