#!/bin/bash

# Ensure /app/data directory exists and is writable
if [ ! -d /app/data ]; then
    mkdir -p /app/data
    if [ $? -ne 0 ]; then
        echo "*** Error: Failed to create /app/data directory"
        exit 1
    fi
    chmod 777 /app/data
    chown vlcuser:vlcuser /app/data
    echo "*** Created /app/data directory with 777 permissions"
else
    # Ensure directory is writable
    chmod 777 /app/data
    chown vlcuser:vlcuser /app/data
    echo "*** Set /app/data to 777 permissions and vlcuser ownership"
fi

# Create favorites.json if it doesn't exist
if [ ! -f /app/data/favorites.json ]; then
    touch /app/data/favorites.json
    if [ $? -ne 0 ]; then
        echo "*** Error: Failed to create /app/data/favorites.json"
        exit 1
    fi
    echo '[]' > /app/data/favorites.json
    chmod 666 /app/data/favorites.json
    chown vlcuser:vlcuser /app/data/favorites.json
    echo "*** Created /app/data/favorites.json with 666 permissions"
else
    # Ensure file is writable
    chmod 666 /app/data/favorites.json
    chown vlcuser:vlcuser /app/data/favorites.json
    echo "*** Set /app/data/favorites.json to 666 permissions and vlcuser ownership"
fi

# Start the Python application
source /opt/venv/bin/activate
python /app/app.py
