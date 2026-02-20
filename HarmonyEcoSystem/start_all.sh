#!/bin/bash
# ============================================================================
# HarmonyEcoSystem Analytics Platform - Quick Start Script
# ============================================================================
# This script starts both main app (8181) and analytics (8190) together
# ============================================================================

echo "============================================================================"
echo "HarmonyEcoSystem - Starting All Services"
echo "============================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if main app is already running
if lsof -i:8181 >/dev/null 2>&1; then
    echo -e "${YELLOW}[!]${NC} Main app (port 8181) is already running"
else
    echo -e "${BLUE}[*]${NC} Starting main application on port 8181..."
    python3 run.py > logs/main_app.log 2>&1 &
    MAIN_PID=$!
    echo -e "${GREEN}[✓]${NC} Main app started (PID: $MAIN_PID)"
fi

# Wait a bit for main app to initialize
sleep 2

# Check if analytics is already running
if lsof -i:8190 >/dev/null 2>&1; then
    echo -e "${YELLOW}[!]${NC} Analytics (port 8190) is already running"
else
    echo -e "${BLUE}[*]${NC} Starting analytics dashboard on port 8190..."
    python3 run_analytics.py > logs/analytics_app.log 2>&1 &
    ANALYTICS_PID=$!
    echo -e "${GREEN}[✓]${NC} Analytics started (PID: $ANALYTICS_PID)"
fi

echo ""
echo "============================================================================"
echo -e "${GREEN}All services started successfully!${NC}"
echo "============================================================================"
echo ""
echo "Access Points:"
echo -e "  ${BLUE}Main Application:${NC}     http://localhost:8181"
echo -e "  ${BLUE}Analytics Dashboard:${NC}  http://localhost:8190/analytics"
echo ""
echo "Logs:"
echo "  Main App:    logs/main_app.log"
echo "  Analytics:   logs/analytics_app.log"
echo ""
echo "To stop all services, run: ./stop_all.sh"
echo "============================================================================"
