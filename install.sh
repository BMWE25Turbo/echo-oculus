#!/usr/bin/env bash
set -euo pipefail

echo "[EO] One-shot setup starting…"

# 0) Ensure Python
if ! command -v python3 >/dev/null; then
  sudo apt-get update
  sudo apt-get install -y python3 python3-venv python3-pip
fi

# 1) System packages
sudo apt-get update
sudo apt-get install -y ffmpeg smartmontools nvme-cli build-essential

# 2) Repo root
REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$REPO_DIR"

# 3) venv + Python deps
[ -d venv ] || python3 -m venv venv
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt
[ -f requirements-dev.txt ] && pip install -r requirements-dev.txt

# 4) Log dirs to match config.yaml
LOG_ROOT="/var/log/echo-oculus"
ARCHIVE_DIR="${LOG_ROOT}/archive"
sudo mkdir -p "$ARCHIVE_DIR"
# allow the current user (or 'pi') to write
USER_NAME="${SUDO_USER:-$(whoami)}"
sudo chown -R "$USER_NAME":"$USER_NAME" "$LOG_ROOT" || true

# 5) Install + enable systemd units (auto-start + SSD checks)
if [ -f deploy/echo-oculus.service ]; then
  sudo cp deploy/echo-oculus.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable --now echo-oculus
  echo "[EO] Enabled service: echo-oculus"
fi

if [ -f deploy/ssd-health.service ] && [ -f deploy/ssd-health.timer ]; then
  sudo cp deploy/ssd-health.service /etc/systemd/system/
  sudo cp deploy/ssd-health.timer /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable --now ssd-health.timer
  echo "[EO] Enabled timer: ssd-health.timer"
fi

echo "[EO] Setup complete ✅"
echo "Logs live in: $LOG_ROOT"
