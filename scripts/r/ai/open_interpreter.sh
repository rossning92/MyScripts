# https://github.com/KillianLucas/open-interpreter

set -e

if [[ ! -d .venv/oi ]]; then
    python -m venv .venv/oi
    source .venv/oi/Scripts/activate
    pip install open-interpreter
fi

source .venv/oi/Scripts/activate

# Requires: OPENAI_API_KEY
interpreter
