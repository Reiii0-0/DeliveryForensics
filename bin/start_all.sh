#!/bin/bash
cd "$(dirname "#!/bin/bash
")/.."

# ============================================================================
# DeliveryForensics: Master Startup Script
# Standard: @bash-pro
# Description: Initializes and starts the ELT infrastructure (Docker stack)
# ============================================================================

set -e # Exit immediately if a command exits with a non-zero status.

# Colors for logging
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

function log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

function log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

function log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# --- Step 1: Prerequisite Checks ---
log_info "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    # Check for docker compose (v2)
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed."
        exit 1
    fi
fi

# --- Step 2: Permission Setup ---
log_info "Setting up file permissions and environment variables (may require sudo)..."
mkdir -p data/clickhouse data/metabase logs
sudo chmod -R 777 data logs

# Handle .env and Fernet Key
if [ ! -f .env ]; then
    log_info "Creating initial .env file..."
    cp .env.example .env 2>/dev/null || touch .env
fi

if ! grep -q "FERNET_KEY" .env || [ -z "$(grep FERNET_KEY .env | cut -d'=' -f2)" ]; then
    log_info "Generating Airflow Fernet Key..."
    # Generate a simple base64 key if python is available
    if command -v python3 &> /dev/null; then
        FERNET_KEY=$(python3 -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())")
        # Remove existing FERNET_KEY line if any
        sed -i '/FERNET_KEY/d' .env
        echo "FERNET_KEY=$FERNET_KEY" >> .env
    fi
fi

# Ensure AIRFLOW_UID is set to current user
if ! grep -q "AIRFLOW_UID" .env; then
    echo "AIRFLOW_UID=$(id -u)" >> .env
fi

# --- Step 3: Start Stack ---
log_info "Launching Docker Stack (Airflow, ClickHouse, Metabase)..."

# Use 'docker compose' (v2) if available, fallback to 'docker-compose'
DOCKER_COMPOSE="docker-compose"
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
fi

$DOCKER_COMPOSE up -d --build

# --- Step 4: Auto-Provisioning (Dashboard-as-Code) ---
log_info "Waiting for ClickHouse to be healthy..."
until [ "$($DOCKER_COMPOSE ps clickhouse --format "{{.Health}}")" == "healthy" ]; do
    printf '.'
    sleep 2
done
echo -e "\nClickHouse is UP."

log_info "Waiting for Metabase to initialize (may take 1-2 minutes)..."
until $(curl --output /dev/null --silent --head --fail http://localhost:3000/api/health); do
    printf '.'
    sleep 5
done
echo -e "\nMetabase is UP. Running provisioning and restoration script..."

# We run this from inside the airflow-scheduler container because it has all Python dependencies
log_info "Restoring ClickHouse Data (Aligning with IEEE Paper)..."
docker exec -e PYTHONPATH=/opt/airflow/plugins --user airflow project-airflow-scheduler-1 python3 /opt/airflow/scripts/restore_db.py

log_info "Provisioning Metabase Dashboard..."
docker exec -e PYTHONPATH=/opt/airflow/plugins --user airflow project-airflow-scheduler-1 python3 /opt/airflow/scripts/provision_metabase.py

# --- Step 5: Final Summary ---
echo -e "\n"
log_success "DeliveryForensics system is starting up!"
echo "--------------------------------------------------------"
echo -e "ðŸš€ ${GREEN}Airflow Webserver:${NC}  http://localhost:8080 (User: airflow, Pass: airflow)"
echo -e "ðŸ“Š ${GREEN}Metabase Dashboard:${NC} http://localhost:3000 (User: admin@dustinia.com, Pass: DustiniaMaster2026!)"
echo -e "ðŸ“¦ ${GREEN}ClickHouse HTTP:${NC}    http://localhost:8123"
echo "--------------------------------------------------------"
echo "Note: It may take 1-2 minutes for all services to become healthy."
echo "Run 'docker compose ps' in the project directory to check status."

