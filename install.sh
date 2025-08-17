#!/usr/bin/env bash
set -euo pipefail

echo "[EO] One-shot setup starting…"

# --- 0) Sanity checks ---
if ! command -v python3 >/dev/null; then
  echo "[EO] Python3 not found. Installing…"
  sudo apt-get update
  sudo apt-get install -y python3 python3-venv python3-pip
fi

# --- 1) System packages needed by EO (Phase 1/1.5) ---
echo "[EO] Installing system packages (ffmpeg, nvme/smart tools, build essentials)…"
sudo apt-get update
sudo apt-get install -y \
  ffmpeg \
  smartmontools \
  nvme-cli \
  build-essential

# --- 2) Move into repo root (this script should live at the repo root) ---
REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$REPO_DIR"

# --- 3) Python virtualenv ---
if [ ! -d "venv" ]; then
  echo "[EO] Creating virtualenv…"
  python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip wheel

# --- 4) Python deps (runtime + dev) ---
echo "[EO] Installing Python dependencies…"
pip install -r requirements.txt
if [ -f requirements-dev.txt ]; then
  pip install -r requirements-dev.txt
fi

# --- 5) Log directories for rotation/archiving (from config.yaml defaults) ---
LOG_ROOT="/var/log/echo-oculus"
ARCHIVE_DIR="${LOG_ROOT}/archive"
echo "[EO] Ensuring log directories exist: ${LOG_ROOT} and ${ARCHIVE_DIR}"
sudo mkdir -p "$ARCHIVE_DIR"
# Allow 'pi' user to write logs (adjust user if needed)
if id -u pi >/dev/null 2>&1; then
  sudo chown -R pi:pi "$LOG_ROOT"
fi

# --- 6) Quick tips / next steps ---
echo
echo "[EO] Setup complete ✅"
echo "Next steps:"
echo "  1) Edit config.yaml if needed (logger paths already created)."
echo "  2) Activate venv:    source venv/bin/activate"
echo "  3) Run EO:           python3 main.py"
echo
echo "Optional (systemd):"
echo "  - I can generate deploy/echo-oculus.service so EO starts on boot."
echo
