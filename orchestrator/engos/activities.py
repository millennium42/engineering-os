import os

import httpx
from temporalio import activity


@activity.defn
async def get_openhands_conversation_status(conversation_id: str) -> str:
    """Consulta o estado de uma conversa no OpenHands Agent Server."""

    api_key = os.environ.get("OPENHANDS_API_KEY")

    if not api_key:
        raise RuntimeError("OPENHANDS_API_KEY não está definida")

    url = f"http://localhost:3000/api/conversations/{conversation_id}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            url,
            headers={"X-Session-API-Key": api_key},
        )

        response.raise_for_status()
        data = response.json()

    return data["execution_status"]


from engos.models import OpenHandsMessageInput


@activity.defn
async def send_openhands_message(data: OpenHandsMessageInput) -> bool:
    """Envia uma mensagem para uma conversa OpenHands existente."""

    api_key = os.environ.get("OPENHANDS_API_KEY")

    if not api_key:
        raise RuntimeError("OPENHANDS_API_KEY não está definida")

    url = (
        "http://localhost:3000/api/conversations/"
        f"{data.conversation_id}/events"
    )

    payload = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": data.message,
            }
        ],
        "run": data.run,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            url,
            headers={"X-Session-API-Key": api_key},
            json=payload,
        )

        response.raise_for_status()
        result = response.json()

    return bool(result["success"])
