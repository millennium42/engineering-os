from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from engos.activities import (
        create_openhands_conversation,
        get_openhands_conversation_status,
        send_openhands_message,
    )
    from engos.models import OpenHandsConversationInput, OpenHandsMessageInput


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
        return await workflow.execute_activity(
            send_openhands_message,
            data,
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
        return await workflow.execute_activity(
            create_openhands_conversation,
            data,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_attempts=3,
            ),
        )
