#!/usr/bin/env bash
set -e

echo "Installing Python dependencies for the Windows printer application..."

if command -v py.exe >/dev/null 2>&1; then
    py.exe -m pip install -r "$(wslpath -w "$PWD/requirements.txt")"
elif command -v python.exe >/dev/null 2>&1; then
    python.exe -m pip install -r "$(wslpath -w "$PWD/requirements.txt")"
else
    echo "Windows Python was not found."
    echo "Install Python for Windows first, then rerun ./setup_wsl.sh"
    exit 1
fi

echo
echo "Setup complete."
echo "Run the application from WSL with:"
echo
echo "    ./run_l3250.sh"
