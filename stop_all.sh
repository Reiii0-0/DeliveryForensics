#!/bin/bash

# ============================================================================
# DeliveryForensics: Master Stop Script
# Standard: @bash-pro
# Description: Stops the ELT infrastructure safely (Persistent Mode)
# ============================================================================

# Colors for logging
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_info "Stopping DeliveryForensics Docker Stack..."

# Use 'docker compose' (v2) if available, fallback to 'docker-compose'
if docker compose version &> /dev/null; then
    docker compose stop
else
    docker-compose stop
fi

log_info "Services stopped successfully. Data remains persistent in project/data/."
