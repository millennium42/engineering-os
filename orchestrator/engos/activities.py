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


from engos.models import OpenHandsConversationInput, OpenHandsMessageInput


@activity.defn
async def send_openhands_message(data: OpenHandsMessageInput) -> bool:
    """Envia uma mensagem ao OpenHands sem duplicá-la em retries."""

    api_key = os.environ.get("OPENHANDS_API_KEY")

    if not api_key:
        raise RuntimeError("OPENHANDS_API_KEY não está definida")

    if not data.message_id:
        raise RuntimeError("message_id é obrigatório para envio idempotente")

    base_url = (
        "http://localhost:3000/api/conversations/"
        f"{data.conversation_id}"
    )

    marker = f"[engos-message-id:{data.message_id}]"
    message_text = f"{data.message}\n\n{marker}"

    headers = {
        "X-Session-API-Key": api_key,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Verifica se uma tentativa anterior já persistiu esta mensagem.
        search_response = await client.get(
            f"{base_url}/events/search",
            headers=headers,
            params={
                "source": "user",
                "body": marker,
                "limit": 1,
            },
        )

        search_response.raise_for_status()

        if search_response.json().get("items"):
            return True

        payload = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": message_text,
                }
            ],
            "run": data.run,
        }

        response = await client.post(
            f"{base_url}/events",
            headers=headers,
            json=payload,
        )

        response.raise_for_status()
        result = response.json()

    return bool(result["success"])


@activity.defn
async def create_openhands_conversation(
    data: OpenHandsConversationInput,
) -> str:
    """Cria uma conversa OpenHands e retorna seu UUID."""

    api_key = os.environ.get("OPENHANDS_API_KEY")

    if not api_key:
        raise RuntimeError("OPENHANDS_API_KEY não está definida")

    payload = {
        "workspace": {
            "working_dir": data.working_dir,
            "kind": "LocalWorkspace",
        },
        "conversation_id": data.conversation_id,
        "worktree": data.worktree,
        "autotitle": False,
        "agent": {
            "kind": "Agent",
            "llm": {
                "model": data.model,
                "api_key": "placeholder",
                "base_url": data.base_url,
            },
            "tools": [],
        },
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            "http://localhost:3000/api/conversations",
            headers={"X-Session-API-Key": api_key},
            json=payload,
        )

        response.raise_for_status()
        result = response.json()

    return result["id"]
