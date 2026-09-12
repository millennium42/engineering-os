from __future__ import annotations

import asyncio
import subprocess

from temporalio import activity


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
