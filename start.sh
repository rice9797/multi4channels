#!/bin/bash

# Check if /app/data is writable
if [ ! -d /app/data ]; then
    mkdir -p /app/data
    if [ $? -ne 0 ]; then
        echo "*** Error: Failed to create /app/data directory"
        exit 1
    fi
    echo "*** Created /app/data directory"
fi

# Test writability of /app/data
touch /app/data/.test_write 2>/dev/null
if [ $? -ne 0 ]; then
    echo "*** Warning: /app/data is not writable by vlcuser, attempting to create favorites.json in /tmp and copy"
    # Create favorites.json in /tmp
    echo '[]' > /tmp/favorites.json
    chmod 666 /tmp/favorites.json
    chown vlcuser:vlcuser /tmp/favorites.json
    # Try copying to /app/data
    cp /tmp/favorites.json /app/data/favorites.json 2>/dev/null
    if [ $? -eq 0 ]; then
        chmod 666 /app/data/favorites.json 2>/dev/null
        chown vlcuser:vlcuser /app/data/favorites.json 2>/dev/null
        echo "*** Copied /tmp/favorites.json to /app/data/favorites.json"
    else
        echo "*** Error: Failed to copy favorites.json to /app/data"
        # Use /tmp/favorites.json as fallback
        ln -sf /tmp/favorites.json /app/data/favorites.json 2>/dev/null
        echo "*** Linked /tmp/favorites.json to /app/data/favorites.json as fallback"
    fi
    rm /tmp/favorites.json 2>/dev/null
else
    # /app/data is writable, create favorites.json
    rm /app/data/.test_write
    if [ ! -f /app/data/favorites.json ]; then
        echo '[]' > /app/data/favorites.json
        chmod 666 /app/data/favorites.json
        chown vlcuser:vlcuser /app/data/favorites.json
        echo "*** Created /app/data/favorites.json with 666 permissions"
    else
        chmod 666 /app/data/favorites.json 2>/dev/null
        chown vlcuser:vlcuser /app/data/favorites.json 2>/dev/null
        echo "*** Set /app/data/favorites.json to 666 permissions and vlcuser ownership"
    fi
fi

# Start the Python application
source /opt/venv/bin/activate
python /app/app.py
