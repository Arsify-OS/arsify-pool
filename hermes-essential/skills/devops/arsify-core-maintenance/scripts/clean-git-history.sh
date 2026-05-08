#!/bin/bash
# Clean git history of sensitive/legacy references using git-filter-repo
# Usage: ./clean-git-history.sh <repo_path> <old_term> <new_term>

set -euo pipefail

REPO_PATH="${1:-.}"
OLD_TERM="${2:-hermes}"
NEW_TERM="${3:-upshalter}"

if [ ! -d "$REPO_PATH/.git" ]; then
    echo "Error: $REPO_PATH is not a git repository"
    exit 1
fi

# Backup repo
BACKUP_PATH="${REPO_PATH}-backup-$(date +%Y%m%d-%H%M%S)"
echo "Backing up repo to $BACKUP_PATH..."
cp -r "$REPO_PATH" "$BACKUP_PATH"

cd "$REPO_PATH"

# Install git-filter-repo if not present
if ! command -v git-filter-repo &>/dev/null; then
    echo "Installing git-filter-repo..."
    apt-get update -qq && apt-get install -y git-filter-repo
fi

# Prepare replacement file (case-insensitive)
REPLACE_FILE=$(mktemp)
echo -e "${OLD_TERM}\n${OLD_TERM^}\n${OLD_TERM^^}" > "$REPLACE_FILE"
echo -e "${NEW_TERM}\n${NEW_TERM^}\n${NEW_TERM^^}" >> "$REPLACE_FILE"

echo "Running git filter-repo to replace $OLD_TERM with $NEW_TERM..."
git filter-repo --replace-text "$REPLACE_FILE" --force

# Cleanup
rm "$REPLACE_FILE"

echo "Git history cleaned. Next steps:"
echo "  cd $REPO_PATH"
echo "  git remote set-url origin git@github.com:Arsify-OS/Arsify-core.git"
echo "  git push -f origin main"
