#!/bin/sh
# Setup git hooks to run tests before push
# Run: ./scripts/setup-hooks.sh

git config core.hooksPath .githooks
echo "Git hooks configured. Tests will run before each push."
