#!/bin/sh
# Commit and deploy Firestore rules + indexes
# Usage: ./scripts/commit-deploy.sh ["commit message"]
#        ./scripts/commit-deploy.sh  (prompts for message)

set -e
cd "$(git rev-parse --show-toplevel)"

MSG="${1:-}"

# Commit
if [ -n "$MSG" ]; then
    echo ""
    echo "=== Staging changes ==="
    git add -A
    git status
    echo ""
    echo "=== Committing ==="
    if git commit -m "$MSG"; then
        echo ""
        echo "=== Pushing to remote (triggers Render deploy) ==="
        git push
    fi
else
    echo "Usage: $0 \"commit message\""
    echo "Or run: git commit -m \"your message\" && firebase deploy --only firestore"
    exit 0
fi

# Deploy Firestore
echo ""
echo "=== Deploying Firestore (rules + indexes) ==="
firebase deploy --only firestore

echo ""
echo "Done."
