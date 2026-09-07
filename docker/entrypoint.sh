#!/bin/sh
set -e

mkdir -p /app/data

if [ ! -f /app/data/db.sqlite3 ]; then
  echo "Initializing SQLite database..."
  python import_data_to_sqlite.py
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8182
