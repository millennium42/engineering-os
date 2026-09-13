from __future__ import annotations

import asyncio
import subprocess
import os
import platform
from typing import Any

from temporalio import activity

from engos.evidence import EvidenceStore


@activity.defn
async def normalize_worktree_permissions(worktree_path: str) -> str:
    completed = await asyncio.to_thread(
        subprocess.run,
        ["sudo", "-n", "/usr/local/sbin/engos-normalize-worktree-permissions", worktree_path],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"permission normalization failed: {completed.stderr.strip()}"
        )
    return worktree_path


@activity.defn
async def get_git_worktree_status(worktree_path: str) -> str:
    completed = await asyncio.to_thread(
        subprocess.run,
        ["git", "-C", worktree_path, "status", "--short"],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"git status failed: {completed.stderr.strip()}")
    return completed.stdout.strip()


@activity.defn
async def record_supervised_evidence(payload: dict[str, Any]) -> str:
    run_id = str(payload["run_id"])
    worktree_path = str(payload["worktree_path"])
    store = EvidenceStore(run_id)

    diff = await asyncio.to_thread(
        subprocess.run,
        ["git", "-C", worktree_path, "diff", "--binary", "HEAD"],
        capture_output=True,
        text=True,
    )
    if diff.returncode != 0:
        raise RuntimeError(f"git diff failed: {diff.stderr.strip()}")

    store.write_json("request.json", {
        "workflow_id": payload["workflow_id"],
        "run_id": run_id,
        "repo_path": payload["repo_path"],
        "worktree_path": worktree_path,
        "branch_name": payload["branch_name"],
        "base_ref": payload["base_ref"],
        "message": payload["message"],
    })
    store.write_json("model.json", {
        "model": payload["model"],
        "base_url": payload["base_url"],
        "harness": "openhands",
    })
    store.write_json("environment.json", {
        "hostname": platform.node(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "pid": os.getpid(),
    })
    store.write_text("git-status.txt", str(payload["git_status"]) + "\n")
    store.write_text("git-diff.patch", diff.stdout)
    store.write_json("metrics.json", {
        "git_status_nonempty": bool(payload["git_status"]),
        "diff_bytes": len(diff.stdout.encode("utf-8")),
    })
    store.append_event({
        "type": "execution_completed",
        "execution_status": payload["execution_status"],
        "conversation_id": payload["conversation_id"],
        "message_id": payload["message_id"],
    })
    store.write_result({
        "status": payload["execution_status"],
        "workflow_id": payload["workflow_id"],
        "conversation_id": payload["conversation_id"],
        "message_id": payload["message_id"],
        "worktree_path": worktree_path,
        "git_status": payload["git_status"],
    })
    return str(store.run_dir)
