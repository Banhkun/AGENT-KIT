#!/usr/bin/env bash
set -e

echo "Fetching and pruning remote tracking branches..."
git fetch --prune

repo_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

# Find all branches marked [gone]
gone_branches=$(git branch -vv | grep '\[gone\]' | sed 's/^[+* ]//' | awk '{print $1}')

if [ -z "$gone_branches" ]; then
  echo "No stale [gone] branches detected. Repository is clean!"
  exit 0
fi

echo "Found stale [gone] branches:"
echo "$gone_branches"

echo "$gone_branches" | while read -r branch; do
  [ -z "$branch" ] && continue
  echo "Processing branch: $branch"

  # Find and remove associated worktree if exists (and not main worktree)
  worktree=$(git worktree list | grep "\[$branch\]" | awk '{print $1}')
  if [ -n "$worktree" ] && [ "$worktree" != "$repo_root" ]; then
    echo "  Removing associated worktree: $worktree"
    git worktree remove --force "$worktree"
  fi

  echo "  Deleting branch: $branch"
  git branch -D "$branch"
done

echo "Cleanup complete!"
