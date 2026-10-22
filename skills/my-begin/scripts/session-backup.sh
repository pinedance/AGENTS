#!/usr/bin/env bash
# session-backup.sh: Surgical untracked & ignored safety snapshot helper
# Creates a rolling backup of untracked/.gitignore files in ~/.cache/agents/backups/<project>/

set -euo pipefail

WORKSPACE_ROOT="${1:-$PWD}"
WORKSPACE_ROOT="$(cd "$WORKSPACE_ROOT" 2>/dev/null && pwd -P || echo "$WORKSPACE_ROOT")"

# 1. Verify Git workspace
if ! git -C "$WORKSPACE_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "[Safety Snapshot] Workspace is not a git repository. Skipping snapshot."
    exit 0
fi

PROJECT_NAME="$(basename "$WORKSPACE_ROOT")"
BASE_DIR="$HOME/.cache/agents/backups/$PROJECT_NAME"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
TARGET_DIR="$BASE_DIR/$TIMESTAMP"

# 2. Gather untracked & ignored files with C-level excludes
TMP_LIST="$(mktemp)"
trap 'rm -f "$TMP_LIST"' EXIT

git -C "$WORKSPACE_ROOT" ls-files -o \
    --exclude='.git*' \
    --exclude='node_modules*' \
    --exclude='.venv*' \
    --exclude='venv*' \
    --exclude='env*' \
    --exclude='__pycache__*' \
    --exclude='*.egg-info*' \
    --exclude='dist*' \
    --exclude='build*' \
    --exclude='target*' \
    --exclude='.cache*' \
    --exclude='.pytest_cache*' \
    --exclude='.skills-repos*' \
    --exclude='skills-library*' \
    --exclude='.agents/scratch*' > "$TMP_LIST"

FILE_COUNT="$(grep -c . "$TMP_LIST" || true)"

mkdir -p "$BASE_DIR"

if [ "$FILE_COUNT" -eq 0 ]; then
    echo "[Safety Snapshot] No untracked/ignored files to protect in $PROJECT_NAME."
    exit 0
fi

mkdir -p "$TARGET_DIR"

# 3. Stream files preserving hierarchy, timestamps, and symlinks via POSIX tar
tar -cf - -C "$WORKSPACE_ROOT" --files-from="$TMP_LIST" | tar -xf - -C "$TARGET_DIR"

# 4. Update 'latest' symlink
ln -sfn "$TARGET_DIR" "$BASE_DIR/latest"

# 5. Enforce rolling retention: keep 3 newest snapshot directories, prune older
# Matching pattern: directories named with timestamp [0-9]*
PRUNE_TARGETS=$(find "$BASE_DIR" -mindepth 1 -maxdepth 1 -type d ! -name "latest" -name "[0-9]*" | sort -r | tail -n +4 || true)
if [ -n "$PRUNE_TARGETS" ]; then
    echo "$PRUNE_TARGETS" | xargs rm -rf 2>/dev/null || true
fi

echo "[Safety Snapshot] Saved $FILE_COUNT untracked file(s) to $TARGET_DIR"
