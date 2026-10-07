#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WIN_SCRIPT="$(wslpath -w "$SCRIPT_DIR\\run_l3250.bat")"

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
  "& '$WIN_SCRIPT'"
