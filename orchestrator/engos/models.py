from dataclasses import dataclass


@dataclass
class OpenHandsMessageInput:
    """Dados necessários para enviar uma instrução a uma conversa OpenHands."""

    conversation_id: str
    message: str
    run: bool = False


@dataclass
class OpenHandsConversationInput:
    """Configuração mínima para criar uma conversa OpenHands."""

    working_dir: str
    model: str
    base_url: str
    worktree: bool = False
