#!/usr/bin/env bash
# Sets up a new Codespace/devcontainer: installs MariaDB, loads the database, creates the Python environment and .env.
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

echo "==> Writing a development .env (if missing)"
if [ ! -f "$APP_DIR/.env" ]; then
  cat > "$APP_DIR/.env" <<EOF
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DATABASE_URL=mysql+pymysql://reliefline:reliefline_dev_pw@127.0.0.1/reliefline_db
FLASK_DEBUG=1
EOF
fi

echo "==> Enabling repo-tracked git hooks (.githooks/)"
git -C "$PROJECT_DIR" config core.hooksPath .githooks

echo "==> Setup complete"
