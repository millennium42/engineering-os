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


@dataclass
class GitWorktreeInput:
    """Dados para provisionar um worktree Git isolado."""

    repo_path: str
    worktree_path: str
    branch_name: str
    base_ref: str = "HEAD"


@dataclass
class OpenHandsIsolatedTaskInput:
    """Tarefa OpenHands executada em worktree Git isolado."""

    repo_path: str
    worktree_path: str
    branch_name: str
    model: str
    base_url: str
    message: str
    base_ref: str = "HEAD"
    host_projects_root: str = "/home/engops/projects"
    openhands_projects_root: str = "/projects"
    run: bool = False


@dataclass
class OpenHandsIsolatedTaskResult:
    """Identificadores e caminhos de uma tarefa isolada preparada."""

    worktree_path: str
    openhands_working_dir: str
    conversation_id: str
    message_id: str
