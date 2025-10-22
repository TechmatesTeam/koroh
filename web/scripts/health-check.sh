#!/bin/sh
# Health check script for Next.js application in Docker
# This script performs a comprehensive health check for the application

set -e

# Configuration
HOST=${HOSTNAME:-"localhost"}
PORT=${PORT:-3000}
TIMEOUT=${HEALTH_CHECK_TIMEOUT:-10}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log messages
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Function to check HTTP endpoint
check_endpoint() {
    local endpoint=$1
    local expected_status=${2:-200}
    local description=$3
    
    log "Checking $description..."
    
    if command -v curl >/dev/null 2>&1; then
        response=$(curl -s -o /dev/null -w "%{http_code}" \
                   --max-time $TIMEOUT \
                   --connect-timeout 5 \
                   "http://$HOST:$PORT$endpoint" || echo "000")
    else
        log "ERROR: curl not available for health check"
        return 1
    fi
    
    if [ "$response" = "$expected_status" ]; then
        log "${GREEN}✓${NC} $description - OK (HTTP $response)"
        return 0
    else
        log "${RED}✗${NC} $description - FAILED (HTTP $response, expected $expected_status)"
        return 1
    fi
}

# Function to check process
check_process() {
    log "Checking Node.js process..."
    
    if pgrep -f "node.*server.js" >/dev/null 2>&1; then
        log "${GREEN}✓${NC} Node.js process - RUNNING"
        return 0
    else
        log "${RED}✗${NC} Node.js process - NOT FOUND"
        return 1
    fi
}

# Main health check function
main() {
    log "Starting health check for Next.js application..."
    log "Target: http://$HOST:$PORT"
    
    local exit_code=0
    
    # Check if the process is running
    if ! check_process; then
        exit_code=1
    fi
    
    # Check basic health endpoint
    if ! check_endpoint "/api/health" "200" "Health endpoint"; then
        exit_code=1
    fi
    
    # Check if we can reach the main application
    if ! check_endpoint "/" "200" "Main application"; then
        exit_code=1
    fi
    
    # Optional: Check status endpoint for detailed information
    if check_endpoint "/api/status" "200" "Status endpoint (optional)"; then
        log "${GREEN}✓${NC} Detailed status check passed"
    else
        log "${YELLOW}⚠${NC} Status endpoint check failed (non-critical)"
    fi
    
    if [ $exit_code -eq 0 ]; then
        log "${GREEN}✓${NC} All health checks passed"
    else
        log "${RED}✗${NC} Health check failed"
    fi
    
    return $exit_code
}

# Run the health check
main "$@"