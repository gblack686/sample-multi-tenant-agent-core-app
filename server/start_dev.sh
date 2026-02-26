#!/bin/bash
SCRIPT_DIR="$(dirname "$0")"
export $(cat "$SCRIPT_DIR/../.env" | xargs)
cd "$SCRIPT_DIR"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
