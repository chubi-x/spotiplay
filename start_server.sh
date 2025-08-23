#!/bin/bash
# Production startup script for Spotiplay application using Gunicorn

# Default settings
WORKERS=4  # (2 * CPU cores) + 1 is a good starting point
TIMEOUT=120
PORT=${PORT:-5000}
HOST=${HOST:-0.0.0.0}
LOG_LEVEL=${LOG_LEVEL:-info}

# Start Gunicorn with appropriate settings
exec gunicorn wsgi:app \
    --workers $WORKERS \
    --bind $HOST:$PORT \
    --timeout $TIMEOUT \
    --log-level $LOG_LEVEL \
    --access-logfile - \
    --error-logfile - \
    --capture-output

