#!/bin/bash
# launchd 執行入口:載入本機環境變數(含 ANTHROPIC_API_KEY),再呼叫 morning_note.py。
# 金鑰不放進本 repo 或 plist,而是放在下面這個「不受版本控管」的檔案裡:
#   ~/.config/morningnote/env
# 內容範例:
#   export ANTHROPIC_API_KEY="sk-ant-..."
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$HOME/.config/morningnote/env"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "ANTHROPIC_API_KEY 未設定,請先建立 $ENV_FILE" >&2
  exit 1
fi

exec /usr/bin/python3 "$SCRIPT_DIR/morning_note.py" "$@"
