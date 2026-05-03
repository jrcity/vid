#!/bin/bash
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting VID Backend with Python $(python --version 2>&1)..."
uvicorn app.main:app --reload --port 8000
