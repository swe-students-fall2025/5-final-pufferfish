#!/bin/bash

if [ "$debug" = "true" ]; then
    echo "Starting Flask in development mode with auto-reload..."
    exec flask run --host=0.0.0.0 --port=8000 --debug
else
    echo "Starting Flask in production mode with Gunicorn..."
    exec gunicorn --bind 0.0.0.0:8000 run:app
fi