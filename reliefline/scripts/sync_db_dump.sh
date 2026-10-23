#!/usr/bin/env bash
# Saves a fresh copy of the database into database/reliefline_db.sql (run after any database change).
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DUMP_FILE="$PROJECT_DIR/database/reliefline_db.sql"
DB_NAME="reliefline_db"
DB_HOST="127.0.0.1"

DUMP_BINS=()
if command -v mysqldump >/dev/null 2>&1; then
    DUMP_BINS+=("$(command -v mysqldump)")
fi
for candidate in \
    "/Applications/XAMPP/xamppfiles/bin/mysqldump" \
    "/opt/lampp/bin/mysqldump" \
    "/c/xampp/mysql/bin/mysqldump.exe" \
    "/d/program files/xamp/mysql/bin/mysqldump.exe" \
    "/d/xampp/mysql/bin/mysqldump.exe" \
    "/c/Program Files/MySQL/MySQL Server 8.0/bin/mysqldump.exe" \
    "/c/Program Files/MariaDB 11.4/bin/mysqldump.exe"
do
    [ -x "$candidate" ] || continue
    already=0
    for existing in "${DUMP_BINS[@]:-}"; do
        [ "$existing" = "$candidate" ] && already=1 && break
    done
    [ "$already" -eq 0 ] && DUMP_BINS+=("$candidate")
done
if [ "${#DUMP_BINS[@]}" -eq 0 ]; then
    echo "sync_db_dump: no mysqldump found - install MariaDB/MySQL client or XAMPP" >&2
    exit 1
fi

CANDIDATES=("reliefline|reliefline_dev_pw" "root|")
DUMP_BIN=""; DB_USER=""; DB_PASS=""
for bin in "${DUMP_BINS[@]}"; do
    for cand in "${CANDIDATES[@]}"; do
        u="${cand%%|*}"; p="${cand#*|}"
        if "$bin" -u "$u" ${p:+-p"$p"} -h "$DB_HOST" --no-data --skip-dump-date \
            "$DB_NAME" >/dev/null 2>&1; then
            DUMP_BIN="$bin"; DB_USER="$u"; DB_PASS="$p"; break 2
        fi
    done
done
if [ -z "$DB_USER" ]; then
    echo "sync_db_dump: could not authenticate to $DB_NAME on $DB_HOST (is the DB running?)" >&2
    exit 1
fi

TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT
"$DUMP_BIN" -u "$DB_USER" ${DB_PASS:+-p"$DB_PASS"} -h "$DB_HOST" "$DB_NAME" > "$TMP_FILE"

if ! tail -n 3 "$TMP_FILE" | grep -q "Dump completed"; then
    echo "sync_db_dump: dump looks incomplete - leaving $DUMP_FILE untouched" >&2
    exit 1
fi

mv "$TMP_FILE" "$DUMP_FILE"
trap - EXIT
echo "sync_db_dump: wrote $DUMP_FILE ($(wc -l < "$DUMP_FILE") lines, $(grep -c '^CREATE TABLE' "$DUMP_FILE") tables) via $DB_USER"
