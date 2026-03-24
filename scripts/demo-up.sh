#!/usr/bin/env bash
#
# Start local demo environment for portfolio screenshots.
#
# Usage:
#   ./scripts/demo-up.sh        — start PostgreSQL + seed + backend + frontend
#   ./scripts/demo-up.sh --clean — stop and remove everything
#
# Login (open http://localhost:3000):
#   Admin:     100001 (Елена Соколова)
#   Moderator: 100002 (Алексей Морозов)
#   Member:    100003 (Дмитрий Волков)

set -euo pipefail

CONTAINER_NAME="oncoschool-demo-pg"
DB_PORT=5433
DB_NAME="oncoschool_demo"
DB_PASSWORD="demo"
DB_URL="postgresql+asyncpg://postgres:${DB_PASSWORD}@localhost:${DB_PORT}/${DB_NAME}"

API_PORT="${DEMO_API_PORT:-8002}"
FRONTEND_PORT="${DEMO_FRONTEND_PORT:-3000}"

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# -------------------------------------------------------------------------
# Clean
# -------------------------------------------------------------------------
if [[ "${1:-}" == "--clean" ]]; then
    echo -e "${YELLOW}Stopping demo environment...${NC}"
    # Kill background processes if pid files exist
    for pidfile in /tmp/oncoschool-demo-backend.pid /tmp/oncoschool-demo-frontend.pid; do
        if [[ -f "$pidfile" ]]; then
            pid=$(cat "$pidfile")
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || true
                echo "  Stopped process $pid"
            fi
            rm -f "$pidfile"
        fi
    done
    # Stop PostgreSQL container
    if docker ps -q -f name="${CONTAINER_NAME}" | grep -q .; then
        docker stop "${CONTAINER_NAME}" >/dev/null
        echo "  Stopped PostgreSQL container"
    fi
    if docker ps -aq -f name="${CONTAINER_NAME}" | grep -q .; then
        docker rm "${CONTAINER_NAME}" >/dev/null
        echo "  Removed PostgreSQL container"
    fi
    echo -e "${GREEN}Demo environment cleaned up.${NC}"
    exit 0
fi

# -------------------------------------------------------------------------
# Pre-checks
# -------------------------------------------------------------------------
echo -e "${CYAN}=== Oncoschool Demo Environment ===${NC}"
echo

if ! command -v docker &>/dev/null; then
    echo -e "${RED}Error: docker is not installed.${NC}"
    exit 1
fi

if ! docker info &>/dev/null 2>&1; then
    echo -e "${RED}Error: Docker daemon is not running. Start Docker Desktop first.${NC}"
    exit 1
fi

# Check that API port is free
if lsof -i ":${API_PORT}" -sTCP:LISTEN &>/dev/null; then
    echo -e "${RED}Error: Port ${API_PORT} is already in use.${NC}"
    echo -e "  Either free the port or set a different one: ${CYAN}DEMO_API_PORT=8005 ./scripts/demo-up.sh${NC}"
    exit 1
fi

# -------------------------------------------------------------------------
# 1. PostgreSQL
# -------------------------------------------------------------------------
if docker ps -q -f name="${CONTAINER_NAME}" | grep -q .; then
    echo -e "${GREEN}[1/5] PostgreSQL already running on port ${DB_PORT}${NC}"
else
    # Remove stopped container if exists
    if docker ps -aq -f name="${CONTAINER_NAME}" | grep -q .; then
        docker rm "${CONTAINER_NAME}" >/dev/null
    fi
    echo -e "${YELLOW}[1/5] Starting PostgreSQL on port ${DB_PORT}...${NC}"
    docker run -d \
        --name "${CONTAINER_NAME}" \
        -p "${DB_PORT}:5432" \
        -e POSTGRES_DB="${DB_NAME}" \
        -e POSTGRES_PASSWORD="${DB_PASSWORD}" \
        postgres:16-alpine >/dev/null

    # Wait for PostgreSQL to be ready
    echo -n "  Waiting for PostgreSQL"
    for i in $(seq 1 30); do
        if docker exec "${CONTAINER_NAME}" pg_isready -U postgres &>/dev/null; then
            echo -e " ${GREEN}ready${NC}"
            break
        fi
        echo -n "."
        sleep 1
        if [[ $i -eq 30 ]]; then
            echo -e " ${RED}timeout${NC}"
            exit 1
        fi
    done
fi

# -------------------------------------------------------------------------
# 2. Migrations
# -------------------------------------------------------------------------
echo -e "${YELLOW}[2/5] Running database migrations...${NC}"
cd "${BACKEND_DIR}"

# Required env vars for alembic (app.config imports need these)
export DATABASE_URL="${DB_URL}"
export BOT_TOKEN="0000000000:AAFake-token-for-demo-only_not-real"
export OPENAI_API_KEY="sk-fake-demo-key"
export DEBUG=true
export JWT_SECRET="demo-secret-key-for-screenshots"

python3 -m alembic upgrade head 2>&1 | tail -1

# -------------------------------------------------------------------------
# 3. Seed data
# -------------------------------------------------------------------------
echo -e "${YELLOW}[3/5] Seeding demo data...${NC}"
python3 -m scripts.seed_demo || true

# -------------------------------------------------------------------------
# 4. Start backend (API only, no Telegram bot)
# -------------------------------------------------------------------------
echo -e "${YELLOW}[4/5] Starting backend on http://localhost:${API_PORT} ...${NC}"
python3 -m uvicorn app.main:app \
    --host 0.0.0.0 --port "${API_PORT}" --log-level warning \
    >/tmp/oncoschool-demo-backend.log 2>&1 &
echo $! > /tmp/oncoschool-demo-backend.pid

# Wait for backend to be ready (schedulers take time to start)
echo -n "  Waiting for backend"
for i in $(seq 1 30); do
    if curl -s "http://localhost:${API_PORT}/health" 2>/dev/null | grep -q "ok"; then
        echo -e " ${GREEN}ready${NC}"
        break
    fi
    echo -n "."
    sleep 1
    if [[ $i -eq 30 ]]; then
        echo -e " ${RED}timeout${NC}"
        echo -e "  ${RED}Backend failed to start. Check the process log.${NC}"
        exit 1
    fi
done

# -------------------------------------------------------------------------
# 5. Start frontend
# -------------------------------------------------------------------------
echo -e "${YELLOW}[5/5] Starting frontend on http://localhost:${FRONTEND_PORT} ...${NC}"
cd "${FRONTEND_DIR}"
export PATH="/opt/homebrew/Cellar/node/25.6.0/bin:/opt/homebrew/bin:$PATH"
NEXT_PUBLIC_API_URL="http://localhost:${API_PORT}" \
    npm run dev -- --port "${FRONTEND_PORT}" &>/dev/null &
echo $! > /tmp/oncoschool-demo-frontend.pid
sleep 3

echo
echo -e "${GREEN}=== Demo environment is ready! ===${NC}"
echo
echo -e "  Frontend:  ${CYAN}http://localhost:${FRONTEND_PORT}${NC}"
echo -e "  Backend:   ${CYAN}http://localhost:${API_PORT}${NC}"
echo -e "  API docs:  ${CYAN}http://localhost:${API_PORT}/docs${NC}"
echo
echo -e "  ${YELLOW}Login credentials (enter telegram_id on login page):${NC}"
echo -e "    Admin:     ${CYAN}100001${NC}  (Елена Соколова)"
echo -e "    Moderator: ${CYAN}100002${NC}  (Алексей Морозов)"
echo -e "    Member:    ${CYAN}100003${NC}  (Дмитрий Волков)"
echo
echo -e "  To stop: ${YELLOW}./scripts/demo-up.sh --clean${NC}"
