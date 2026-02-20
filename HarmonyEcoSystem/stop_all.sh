#!/bin/bash
# ============================================================================
# HarmonyEcoSystem - Stop All Services Script
# ============================================================================

echo "Stopping HarmonyEcoSystem services..."

# Stop main app (port 8181)
if lsof -i:8181 >/dev/null 2>&1; then
    PID=$(lsof -ti:8181)
    echo "Stopping main app (PID: $PID)..."
    kill $PID
    echo "[✓] Main app stopped"
else
    echo "[!] Main app not running"
fi

# Stop analytics (port 8190)
if lsof -i:8190 >/dev/null 2>&1; then
    PID=$(lsof -ti:8190)
    echo "Stopping analytics (PID: $PID)..."
    kill $PID
    echo "[✓] Analytics stopped"
else
    echo "[!] Analytics not running"
fi

echo "All services stopped."
