#!/bin/bash
# Simple restart script - checks if process is running, starts if not

SCRIPT_PATH="download_cryptocompare_hourly.py"
COMMAND="python3 $SCRIPT_PATH resume"
LOG_FILE="/tmp/top1000_resume.log"

# Check if process is running
if pgrep -f "python3.*$SCRIPT_PATH.*resume" > /dev/null; then
    echo "Process is already running (PID: $(pgrep -f "python3.*$SCRIPT_PATH.*resume"))"
    exit 0
fi

# Start the process
echo "Starting resume top1000 process..."
nohup $COMMAND >> "$LOG_FILE" 2>&1 &
sleep 2

# Check if it started
if pgrep -f "python3.*$SCRIPT_PATH.*resume" > /dev/null; then
    echo "Process started successfully (PID: $(pgrep -f "python3.*$SCRIPT_PATH.*resume"))"
else
    echo "ERROR: Failed to start process. Check $LOG_FILE for errors."
    exit 1
fi

