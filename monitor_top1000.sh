#!/bin/bash
# Monitor script for top1000 extraction - restarts if process crashes

SCRIPT_PATH="download_cryptocompare_hourly.py"
COMMAND="python3 $SCRIPT_PATH resume"
LOG_FILE="/tmp/top1000_resume.log"
MONITOR_LOG="/tmp/top1000_monitor.log"
CHECK_INTERVAL=60  # Check every 60 seconds

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$MONITOR_LOG"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if process is running
is_process_running() {
    pgrep -f "python3.*$SCRIPT_PATH.*resume" > /dev/null
}

# Start the process
start_process() {
    log_message "Starting resume top1000 process..."
    nohup $COMMAND >> "$LOG_FILE" 2>&1 &
    sleep 2  # Give it a moment to start
    if is_process_running; then
        log_message "Process started successfully (PID: $(pgrep -f "python3.*$SCRIPT_PATH.*resume"))"
        return 0
    else
        log_message "ERROR: Failed to start process!"
        return 1
    fi
}

# Main monitoring loop
log_message "Monitor script started. Checking every ${CHECK_INTERVAL} seconds."

while true; do
    if ! is_process_running; then
        log_message "Process not running - restarting..."
        start_process
        if [ $? -ne 0 ]; then
            log_message "Failed to restart process. Will retry in ${CHECK_INTERVAL} seconds."
        fi
    fi
    sleep "$CHECK_INTERVAL"
done

