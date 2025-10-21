#!/bin/bash

# Log rotation script for Koroh platform
# This script rotates and compresses old log files to manage disk space

LOG_DIR="/app/logs"
RETENTION_DAYS=30
COMPRESS_AFTER_DAYS=7

# Function to rotate logs
rotate_logs() {
    local log_file=$1
    local base_name=$(basename "$log_file" .log)
    local dir_name=$(dirname "$log_file")
    
    if [ -f "$log_file" ]; then
        # Get file size in MB
        local size=$(du -m "$log_file" | cut -f1)
        
        # Rotate if file is larger than 50MB
        if [ "$size" -gt 50 ]; then
            local timestamp=$(date +"%Y%m%d_%H%M%S")
            local rotated_file="${dir_name}/${base_name}_${timestamp}.log"
            
            echo "Rotating $log_file to $rotated_file"
            mv "$log_file" "$rotated_file"
            
            # Compress the rotated file
            gzip "$rotated_file"
            echo "Compressed $rotated_file"
        fi
    fi
}

# Function to clean old logs
clean_old_logs() {
    local log_dir=$1
    
    echo "Cleaning logs older than $RETENTION_DAYS days in $log_dir"
    
    # Remove logs older than retention period
    find "$log_dir" -name "*.log.gz" -type f -mtime +$RETENTION_DAYS -delete
    find "$log_dir" -name "*.log.*" -type f -mtime +$RETENTION_DAYS -delete
    
    echo "Old logs cleaned"
}

# Function to compress old logs
compress_old_logs() {
    local log_dir=$1
    
    echo "Compressing logs older than $COMPRESS_AFTER_DAYS days in $log_dir"
    
    # Compress uncompressed rotated logs older than compress threshold
    find "$log_dir" -name "*.log.*" -not -name "*.gz" -type f -mtime +$COMPRESS_AFTER_DAYS -exec gzip {} \;
    
    echo "Old logs compressed"
}

# Main execution
echo "Starting log rotation for Koroh platform..."
echo "Log directory: $LOG_DIR"
echo "Retention period: $RETENTION_DAYS days"
echo "Compression after: $COMPRESS_AFTER_DAYS days"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Rotate current log files
for log_file in "$LOG_DIR"/*.log; do
    if [ -f "$log_file" ]; then
        rotate_logs "$log_file"
    fi
done

# Compress old logs
compress_old_logs "$LOG_DIR"

# Clean very old logs
clean_old_logs "$LOG_DIR"

echo "Log rotation completed"

# Send signal to Django to reopen log files (if running)
if pgrep -f "manage.py runserver" > /dev/null; then
    echo "Sending SIGUSR1 to Django process to reopen log files"
    pkill -SIGUSR1 -f "manage.py runserver"
fi

# Send signal to Celery workers to reopen log files (if running)
if pgrep -f "celery.*worker" > /dev/null; then
    echo "Sending SIGUSR1 to Celery workers to reopen log files"
    pkill -SIGUSR1 -f "celery.*worker"
fi

echo "Log rotation script finished"