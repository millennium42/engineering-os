from dataclasses import dataclass


@dataclass
class OpenHandsMessageInput:
    """Dados necessários para enviar uma instrução a uma conversa OpenHands."""

    conversation_id: str
    message: str
    run: bool = False
