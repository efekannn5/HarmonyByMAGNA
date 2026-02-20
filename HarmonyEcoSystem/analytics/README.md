# HarmonyEcoSystem Analytics Platform

## Overview
Executive analytics and reporting platform running on port **8190**.

This is a **read-only** analytics dashboard that provides insights into dolly production and logistics processes.

## Features

- **Real-time KPI Dashboard** - Current status and metrics
- **Timeline Analysis** - Historical trends and patterns
- **Production Line Performance** - Comparative analysis by line
- **Operator Performance** - Anonymized efficiency metrics
- **Bottleneck Detection** - Identify and resolve delays
- **Monthly Reports** - Long-term trend analysis with export

## Installation

### Prerequisites
- Python 3.8+
- SQL Server (same database as main app)
- Running instance of main HarmonyEcoSystem app (port 8181)

### Setup

1. **Database Views** - Run the analytics view migration:
   ```bash
   # In SQL Server Management Studio or sqlcmd:
   sqlcmd -S 10.25.1.174 -U sua_appowneruser1 -P Magna2026!! -d ControlTower -i database/019_create_analytics_views.sql
   ```

2. **Dependencies** - Already installed with main app (no additional packages needed)

3. **Start Analytics Server**:
   ```bash
   python3 run_analytics.py
   ```

## Access

- **URL**: http://localhost:8190/analytics
- **Login**: Use admin or manager credentials from main system
- **Auto-refresh**: Dashboard auto-updates every 30 seconds

## Architecture

```
Port 8181 (Main App)          Port 8190 (Analytics)
┌─────────────────┐           ┌──────────────────┐
│  Flask Backend  │           │  Analytics App   │
│  (Operations)   │           │  (Read-Only)     │
└────────┬────────┘           └────────┬─────────┘
         │                              │
         └──────────┬───────────────────┘
                    ▼
           ┌────────────────┐
           │  SQL Server    │
           │  ControlTower  │
           │  + Views       │
           └────────────────┘
```

## Key Components

### Backend (`analytics/`)
- `__init__.py` - Flask app factory
- `routes/api.py` - RESTful API endpoints (read-only)
- `routes/dashboard.py` - Web interface routes

### Frontend (`analytics/templates/`)
- `dashboard.html` - Main KPI dashboard
- `timeline.html` - Trend analysis
- `lines.html` - Production line comparison
- `operators.html` - Operator performance
- `bottlenecks.html` - Delay detection
- `reports.html` - Monthly reports

### Database Views
- `vw_Analytics_DollyJourney` - Complete lifecycle tracking
- `vw_Analytics_DailySummary` - Daily KPIs
- `vw_Analytics_LinePerformance` - Line metrics
- `vw_Analytics_OperatorPerformance` - Operator stats (anonymized)
- `vw_Analytics_Bottlenecks` - Delay detection
- `vw_Analytics_HourlyThroughput` - Hourly production
- `vw_Analytics_CustomerPerformance` - Customer analysis
- `vw_Analytics_MonthlyTrend` - Long-term trends
- `vw_Analytics_PartNumberPerformance` - Part analysis
- `vw_Analytics_RealtimeStatus` - Current snapshot

## API Endpoints

All endpoints are under `/analytics/api/`:

- `GET /overview` - Dashboard overview data
- `GET /timeline` - Timeline data for charts
- `GET /line-performance` - Production line metrics
- `GET /bottlenecks` - Delayed dollys and alerts
- `GET /operator-performance` - Anonymized operator stats
- `GET /monthly-trend` - Monthly summary
- `GET /health` - Health check

## Security

- Requires login with admin/manager role
- Read-only database access via views
- No write operations allowed
- Operator identities anonymized (MD5 hash)
- Separate log file: `logs/analytics.log`

## Performance

- Optimized connection pool (5 connections)
- No SocketIO overhead
- Efficient SQL views with indexes
- Client-side caching with auto-refresh

## Monitoring

Check logs at: `logs/analytics.log`

```bash
tail -f logs/analytics.log
```

## Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8190
lsof -i :8190

# Kill process if needed
kill -9 <PID>
```

### Database Connection Issues
- Verify main app connects successfully (port 8181)
- Check `config/config.yaml` for database credentials
- Ensure analytics views are created (019_create_analytics_views.sql)

### Login Issues
- Only admin/manager roles can access
- Check user role in UserAccount table
- Verify password hash is correct

## Development

To modify analytics:

1. Edit views in `analytics/routes/`
2. Update templates in `analytics/templates/`
3. Add CSS in `analytics/static/css/analytics.css`
4. Add JS in `analytics/static/js/analytics.js`

No restart needed for template/static changes (in debug mode).

## Production Deployment

For production, use gunicorn:

```bash
gunicorn -w 2 -b 0.0.0.0:8190 run_analytics:app
```

Or create a systemd service (similar to main app).

## License

Internal use only - Magna HarmonyEcoSystem Project
