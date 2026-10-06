#!/usr/bin/env bash
# ============================================================
# CloudFinOps – Codespaces bootstrap
# Installs MySQL server, creates database + user, installs
# Python dependencies, and prepares the workspace.
# Idempotent: safe to re-run.
# ============================================================
set -euo pipefail

echo "▶ Starting CloudFinOps Codespace setup..."

# ---------- 1. MySQL ----------
if ! command -v mysql >/dev/null 2>&1; then
  echo "▶ Installing MySQL server..."
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq mysql-server
fi

echo "▶ Starting MySQL..."
sudo service mysql start || sudo mysqld_safe --skip-grant-tables=0 &

# Wait for MySQL to become ready
for i in {1..30}; do
  if sudo mysqladmin ping --silent 2>/dev/null; then
    echo "✔ MySQL is up."
    break
  fi
  sleep 1
done

# Create DB + user (idempotent)
sudo mysql <<'SQL'
CREATE DATABASE IF NOT EXISTS cloudfinops
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'finops'@'localhost' IDENTIFIED BY 'finops_dev_password';
CREATE USER IF NOT EXISTS 'finops'@'%'         IDENTIFIED BY 'finops_dev_password';

GRANT ALL PRIVILEGES ON cloudfinops.* TO 'finops'@'localhost';
GRANT ALL PRIVILEGES ON cloudfinops.* TO 'finops'@'%';
FLUSH PRIVILEGES;
SQL

echo "✔ Database 'cloudfinops' ready. User: finops"

# ---------- 2. Python deps ----------
if [ -f "data-engineering/requirements.txt" ]; then
  echo "▶ Installing Python dependencies..."
  python -m pip install --upgrade pip -q
  python -m pip install -q -r data-engineering/requirements.txt
  echo "✔ Python dependencies installed."
fi

# ---------- 3. Node deps (only if frontend exists) ----------
if [ -f "frontend/cloudfinops-dashboard/package.json" ]; then
  echo "▶ Installing frontend dependencies..."
  (cd frontend/cloudfinops-dashboard && npm install --silent)
  echo "✔ Frontend dependencies installed."
fi

# ---------- 4. .env ----------
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
  echo "✔ Created .env from .env.example (edit secrets as needed)."
fi

# ---------- 5. Data directory ----------
mkdir -p data/raw data/processed data/reports

echo ""
echo "============================================================"
echo "  CloudFinOps Codespace is ready 🚀"
echo "  MySQL    : localhost:3306  (user: finops / finops_dev_password)"
echo "  Database : cloudfinops"
echo ""
echo "  Next step:"
echo "    python data-engineering/generators/generate_billing_data.py"
echo "============================================================"