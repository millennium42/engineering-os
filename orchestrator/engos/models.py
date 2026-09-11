from dataclasses import dataclass


@dataclass
class OpenHandsMessageInput:
    """Dados necessários para enviar uma instrução a uma conversa OpenHands."""

    conversation_id: str
    message: str
    message_id: str | None = None
    run: bool = False


@dataclass
class OpenHandsConversationInput:
    """Configuração mínima para criar uma conversa OpenHands."""

    working_dir: str
    model: str
    base_url: str
    conversation_id: str | None = None
    worktree: bool = False


@dataclass
class OpenHandsTaskInput:
    """Entrada de uma tarefa completa do Engineering OS para o OpenHands."""

    working_dir: str
    model: str
    base_url: str
    message: str
    worktree: bool = False


@dataclass
class OpenHandsTaskResult:
    """Resultado mínimo de uma tarefa preparada no OpenHands."""

    conversation_id: str
    message_id: str
