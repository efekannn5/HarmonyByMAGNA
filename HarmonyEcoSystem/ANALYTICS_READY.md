# HarmonyEcoSystem Analytics Dashboard
## Executive Analytics Platform - SYSTEM READY ✓

---

## 🎯 QUICK START

### Start Everything (Single Command)
```bash
cd /home/sua_it_ai/controltower/HarmonyEcoSystem
python3 run.py
```

This starts **both systems simultaneously**:
- **Port 8181** - Main Dolly Tracking System
- **Port 8190** - Analytics Dashboard (Manager Portal)

### Access URLs
- Main System: `http://10.25.64.181:8181`
- **Analytics Dashboard: `http://10.25.64.181:8190/analytics`**

### Default Login
- Username: `admin` (or any manager/admin account)
- Password: Your system password
- Access Level: Manager & Admin ONLY

---

## 📊 ANALYTICS FEATURES

### 1. **Overview Dashboard**
- Real-time KPI cards with live data
- Total dollies, completion rate, critical alerts
- Stage distribution charts
- Top production lines analysis
- Average cycle time metrics
- Auto-refresh every 30 seconds

### 2. **Timeline Analysis**
- Production-to-Scan duration
- Scan-to-Loading time
- Loading-to-Web Entry time
- Web Entry-to-Shipment time
- Visual timeline charts
- Bottleneck identification

### 3. **Production Lines**
- Performance by production line
- Volume comparison charts
- Completion rates per line
- Average cycle time per line
- Detailed performance tables

### 4. **Operator Performance**
- Productivity rankings
- Dollies handled per operator
- Average loading times
- Efficiency scores
- Performance visualizations

### 5. **Bottleneck Detection**
- Critical delay identification (>6 hours)
- Warning level alerts (5-6 hours)
- Stage-by-stage analysis
- Real-time bottleneck charts
- Actionable insights

### 6. **Reports**
- Custom report generation
- Monthly trend analysis
- Quick stats dashboard
- Export capabilities (planned)
- Historical data access

---

## 🎨 DESIGN FEATURES

### Professional Executive Style
- Modern gradient sidebar navigation
- Clean card-based layout
- Bootstrap Icons (NO EMOJIS)
- Responsive design
- Hover effects and transitions
- Color-coded status badges

### Visual Elements
- **Primary Blue**: Production/Main metrics
- **Success Green**: Completed/Positive
- **Warning Yellow**: In-progress/Attention
- **Danger Red**: Critical/Alerts

### User Experience
- Intuitive navigation
- Real-time data updates
- Fast loading times
- Mobile-responsive
- Clear visual hierarchy

---

## 🔧 TECHNICAL DETAILS

### Database Views Created
✓ `vw_Analytics_DollyJourney` - 72 records
✓ `vw_Analytics_RealtimeStatus` - Live status

### Technology Stack
- **Backend**: Flask 2.0+
- **Frontend**: Bootstrap 5, Chart.js 4.4.0
- **Database**: SQL Server (Read-only views)
- **Icons**: Bootstrap Icons
- **Authentication**: Flask-Login

### Data Updates
- Dashboard: Auto-refresh every 30 seconds
- Database: Read-only (no impact on main system)
- Connection pool: 5 connections for analytics

### Security
- Manager/Admin role required
- Separate authentication from main system
- Session-based access control
- Read-only database access

---

## 📁 PROJECT STRUCTURE

```
analytics/
├── __init__.py              # Flask app factory
├── routes/
│   ├── api.py              # REST API endpoints
│   └── dashboard.py        # Web page routes
└── templates/
    ├── base.html           # Professional layout
    ├── login.html          # Gradient login page
    ├── dashboard.html      # Overview dashboard
    ├── timeline.html       # Timeline analysis
    ├── lines.html          # Production lines
    ├── operators.html      # Operator performance
    ├── bottlenecks.html    # Bottleneck detection
    └── reports.html        # Reports & exports
```

---

## 🚀 CURRENT STATUS

### Operational Metrics (as of Jan 18, 2026)
- **Total Dollies**: 72
- **Current Stage**: All in PRODUCTION
- **Average Wait**: 67.2 hours (CRITICAL)
- **Top Line**: V710 Mirror Assembly (20 dollies)
- **Second Line**: V710 Front Bumper KIT (16 dollies)

### System Health
✓ Database connection: Active
✓ Analytics views: Created and tested
✓ Main system: Running on 8181
✓ Analytics system: Running on 8190
✓ Auto-start: Configured in run.py

---

## 💡 KEY METRICS EXPLAINED

### KPI Cards
- **Total Dollies**: All dollies in tracking system
- **Completed**: Dollies that reached shipment stage
- **In Progress**: Dollies between production and shipment
- **Critical Alerts**: Dollies waiting >6 hours

### Stage Breakdown
- **PRODUCTION**: Completed at EOL, waiting for forklift scan
- **SCANNING**: Being loaded by forklift operator
- **LOADING_COMPLETED**: Loading done, waiting for web entry
- **WEB_PROCESSING**: In web system, preparing shipment
- **COMPLETED**: ASN/Waybill sent, ready for dispatch

### Time Metrics
- **Production→Scan**: Time from EOL completion to first forklift scan
- **Scan→Loading**: Duration of loading process
- **Loading→Web**: Delay before web entry
- **Web→Shipment**: Time to generate ASN/Waybill
- **Total Cycle Time**: End-to-end duration

---

## 🎯 MANAGER INSIGHTS

### What This Dashboard Shows
1. **Real-time Production Flow**: See where every dolly is in the process
2. **Performance Bottlenecks**: Identify which stages cause delays
3. **Line Efficiency**: Compare production lines objectively
4. **Operator Productivity**: Track team performance
5. **Critical Alerts**: Immediate visibility into stuck dollies

### Business Value
- Reduce cycle times by identifying bottlenecks
- Improve operator allocation based on performance data
- Optimize production line capacity
- Prevent delays with early warning system
- Data-driven decision making

---

## 🔐 ACCESS CONTROL

**WHO CAN ACCESS:**
- Managers
- Administrators

**WHO CANNOT ACCESS:**
- Forklift operators
- Regular users
- External users

**AUTHENTICATION:**
- Same user database as main system
- Role-based access control
- Secure session management

---

## 📞 SUPPORT

### Common Issues

**Dashboard not loading?**
- Check both systems are running: `ps aux | grep python`
- Verify port 8190 is accessible
- Check firewall settings

**No data showing?**
- Run: `python3 create_analytics_views.py`
- Verify database views exist
- Check database connection

**Login failing?**
- Ensure user has manager/admin role
- Check credentials in main system
- Verify session configuration

### Logs
- Main system logs: Terminal output on port 8181
- Analytics logs: Terminal output on port 8190
- Database errors: Check SQL Server logs

---

## 🎉 SUCCESS CRITERIA

✓ Single command starts both systems
✓ Professional English interface
✓ Manager-focused metrics (not technical jargon)
✓ Visual charts and graphs
✓ Icons used (NO emojis)
✓ Real-time data updates
✓ Read-only (no impact on main system)
✓ Separate from main system (port 8190)
✓ Accurate data (72 dollies confirmed)
✓ Executive-level presentation

---

**System Status: PRODUCTION READY** ✓

Last Updated: January 18, 2026
Version: 1.0.0
