#!/usr/bin/env bash
# Runs once when the codespace/devcontainer is created (or rebuilt).
# Installs MariaDB, loads the schema, and builds the Python venv so the
# app is immediately runnable after the container finishes creating.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$PROJECT_DIR/reliefline"

echo "==> Installing MariaDB"
sudo apt-get update
sudo apt-get install -y mariadb-server

echo "==> Starting MariaDB"
sudo service mariadb start

echo "==> Waiting for MariaDB to accept connections"
for i in $(seq 1 30); do
  sudo mariadb -e "SELECT 1" >/dev/null 2>&1 && break
  sleep 1
done

echo "==> Creating reliefline_db and loading schema"
sudo mariadb -e "DROP DATABASE IF EXISTS reliefline_db; CREATE DATABASE reliefline_db;"
sudo mariadb reliefline_db < "$APP_DIR/database/reliefline_db.sql"

echo "==> Creating dedicated app DB user"
# root@localhost uses unix_socket auth on Debian/MariaDB, which rejects the
# app's TCP connection with an empty password - a dedicated user avoids that.
sudo mariadb -e "
  CREATE USER IF NOT EXISTS 'reliefline'@'%' IDENTIFIED BY 'reliefline_dev_pw';
  GRANT ALL PRIVILEGES ON reliefline_db.* TO 'reliefline'@'%';
  FLUSH PRIVILEGES;
"

echo "==> Creating Python virtual environment"
cd "$APP_DIR"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo "==> Setup complete"
