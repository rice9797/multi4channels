#!/bin/bash

# Ensure /app/data directory exists and is writable
if [ ! -d /app/data ]; then
    mkdir -p /app/data
    chmod 777 /app/data
    echo "*** Created /app/data directory"
fi

# Create favorites.json if it doesn't exist
if [ ! -f /app/data/favorites.json ]; then
    echo '[]' > /app/data/favorites.json
    chmod 666 /app/data/favorites.json
    echo "*** Created /app/data/favorites.json"
fi

# Start the Python application
source /opt/venv/bin/activate
python /app/app.py
