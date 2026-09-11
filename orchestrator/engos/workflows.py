from temporalio import workflow


@workflow.defn
class HealthcheckWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        return f"Engineering OS Temporal OK: {name}"
