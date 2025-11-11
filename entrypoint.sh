#!/bin/bash
set -e

# wait for DB to be available (simple loop — adjust timeout)
if [ -n "$DATABASE_URL" ]; then
  echo "$DATABASE_URL"
  echo "Waiting for DB..."
  python - <<PY
import os,sys,time
from urllib.parse import urlparse
url=os.getenv("DATABASE_URL")
if url is None:
    sys.exit(0)
# naive check: try connecting via psycopg2
import psycopg2
for i in range(60):
    try:
        conn=psycopg2.connect(url, connect_timeout=3)
        conn.close()
        print("DB reachable")
        sys.exit(0)
    except Exception as e:
        time.sleep(1)
print("DB not reachable, exiting")
sys.exit(1)
PY
fi

# run alembic migrations here
if [ "$RUN_MIGRATIONS" = "1" ]; then
  echo "Running migrations..."
  alembic upgrade head
fi

# Start Uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port 80 --workers 1