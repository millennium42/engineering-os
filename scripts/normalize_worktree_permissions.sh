#!/usr/bin/env bash
set -euo pipefail
target="${1:-}"
if [[ -z "$target" ]]; then echo "worktree path required" >&2; exit 64; fi
resolved="$(realpath -e -- "$target")"
case "$resolved" in
  /home/engops/projects/worktrees/*) ;;
  *) echo "refusing path outside worktree root: $resolved" >&2; exit 65 ;;
esac
setfacl -R -m u:engops:rwX,m::rwX -- "$resolved"
find "$resolved" -type d -exec setfacl -m d:u:engops:rwx,d:m::rwx {} +
