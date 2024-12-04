#!/bin/bash
set -e

# Run migrations
alembic upgrade head

>&2 echo "Migrations applied - starting server"

# Start the FastAPI server
exec uvicorn --workers 1 --host 0.0.0.0 --port $APPLICATION_SERVER_PORT app.main:app
