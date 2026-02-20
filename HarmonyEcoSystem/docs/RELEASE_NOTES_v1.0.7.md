# HarmonyEcoSystem - Release Notes v1.0.7

**Release Date:** 27-30 Kasım 2025  
**Version:** 1.0.7  
**Previous Version:** 1.0.6 (26 Kasım 2025)

---

## Overview

This release focuses on mobile device integration, UI optimization for operators, and critical production stability improvements. The update includes 4 new REST API endpoints for Zebra handheld devices, simplified operator interface, and resolution of critical database connectivity issues affecting mobile operations.

---

## New Features

### 1. Mobile Manual Collection API

**Target Device:** Zebra Android Handheld Scanner  
**Authentication:** Bearer Token (8-hour session)

Four new endpoints have been added to support mobile manual dolly collection workflow:

#### GET /api/manual-collection/groups
Lists all dolly groups with scanned dolly counts.

**Response:**
```json
{
  "groups": [
    {
      "GroupName": "A1",
      "TotalDollys": 24,
      "ScannedDollys": 5
    }
  ]
}
```

#### GET /api/manual-collection/groups/{group_name}
Returns all dollys in a specific group with scan status.

**Response:**
```json
{
  "group_name": "A1",
  "dollys": [
    {
      "DollyNo": "DL-A1-001",
      "Barcode": "123456789",
      "IsScanned": true
    }
  ],
  "total": 24,
  "scanned": 5
}
```

#### POST /api/manual-collection/scan
Scans a dolly barcode into manual collection session.

**Request:**
```json
{
  "barcode": "123456789"
}
```

**Response:**
```json
{
  "success": true,
  "dolly_no": "DL-A1-001",
  "scan_order": 1,
  "message": "Dolly başarıyla tarandı"
}
```

#### POST /api/manual-collection/remove-last
Removes the last scanned dolly (LIFO validation).

**Request:**
```json
{
  "barcode": "123456789"
}
```

**Response:**
```json
{
  "success": true,
  "dolly_no": "DL-A1-001",
  "message": "Son dolly çıkarıldı"
}
```

**Technical Implementation:**
- All endpoints use raw SQL queries (db.text()) for SQL Server compatibility
- Automatic transaction rollback on errors
- Standardized error format: `{"error": "message", "retryable": boolean}`
- Authentication via @require_forklift_auth decorator

---

### 2. Manual Collection UI Optimization

**Purpose:** Simplify operator interface by removing redundant header sections.

**Changes:**
- Removed "Manuel Dolly Toplama" header section (50 lines)
- Removed "Sıralı Dolly Listesi" info banner (30 lines)
- Reduced selection-info card:
  - Font size: 1.3rem → 0.95rem
  - Padding: 0.9rem → 0.6rem
- Title updated: "Dolly İşlem Durumu" → "Seçili Dolly'ler"

**Impact:**
- 80 lines of HTML removed
- Cleaner operator view with focus on active dollys
- Improved mobile responsiveness

**File:** `app/templates/dashboard/manual_collection.html`

---

## Critical Bug Fixes

### 1. Mobile API Database Connectivity Error

**Issue:** Production logs showed repeated "name 'db' is not defined" errors from Zebra device (IP: 10.25.25.18).

**Root Cause:**
- Missing import: `from ..extensions import db`
- SQLAlchemy ORM queries incompatible with raw SQL Server connections

**Resolution:**
1. Added missing db import in `app/routes/api.py` (line 5)
2. Converted all 4 mobile endpoints from SQLAlchemy ORM to raw SQL:
   ```python
   # Before (Broken)
   dollys = DollyEOLInfo.query.filter_by(GroupName=group_name).all()
   
   # After (Fixed)
   result = db.session.execute(db.text("""
       SELECT DollyNo, Barcode FROM DollyEOLInfo 
       WHERE GroupName = :group_name
   """), {"group_name": group_name})
   ```

**Validation:**
- Syntax check passed: `python3 -m py_compile app/routes/api.py`
- Flask startup successful (no errors)
- Mobile device can now retrieve group list

**Files Modified:**
- `app/routes/api.py` (lines 5, 1010-1350)

---

### 2. Syntax Error in Exception Handler

**Issue:** Duplicate exception handler line in api.py causing Python syntax error.

**Location:** Line 261

**Error:**
```python
return jsonify(...), 500xc), "retryable": False}), 500
```

**Resolution:**
Removed duplicate malformed line, cleaned up exception handler.

**File:** `app/routes/api.py` (line 261)

---

## Database Changes

### Migration 011: Dolly Submission Hold Workflow Fields

**File:** `database/011_alter_dolly_submission_hold_add_shipment_fields.sql`

**Execution Date:** 27 Kasım 2025

**New Columns Added to DollySubmissionHold:**
1. `ScanOrder` (INT) - Sequence number for scan order tracking
2. `LoadingSessionId` (NVARCHAR 50) - Links to ForkliftLoginSession
3. `LoadingCompletedAt` (DATETIME2) - Timestamp of loading completion
4. `SeferNumarasi` (NVARCHAR 20) - Shipment number
5. `PlakaNo` (NVARCHAR 20) - License plate number

**Purpose:**
- Enable scan order validation for JIS manufacturing LIFO requirements
- Track loading session lifecycle
- Support shipment documentation

**Verification:**
- All 15 columns confirmed in SQL Server schema
- Migration executed via Python pyodbc in 8 batches

---

## Documentation Updates

### AI_DEVELOPMENT_PROMPT.md Enhancement

**New Sections Added:**

1. **CRITICAL: JIS Manufacturing - Zero Error Tolerance**
   - Wrong vs Correct algorithm comparison
   - SQL Server validation queries
   - 4 test scenarios (pass/fail cases)
   - 150+ lines of JIS compliance documentation

2. **Mobile Manual Collection Operations**
   - Complete API documentation for 4 new endpoints
   - Request/response examples
   - Error handling patterns
   - Authentication requirements

**File:** `docs/AI_DEVELOPMENT_PROMPT.md` (lines 700-900)

---

## Testing Coverage

### Manual Testing Completed

1. **Mobile API Endpoints:**
   - ✅ GET /api/manual-collection/groups - Returns group list
   - ✅ GET /api/manual-collection/groups/{group_name} - Returns dollys
   - ✅ POST /api/manual-collection/scan - Validates barcode, inserts record
   - ✅ POST /api/manual-collection/remove-last - LIFO validation passed

2. **Syntax Validation:**
   - ✅ Python compilation: `python3 -m py_compile app/routes/api.py`
   - ✅ Flask startup: No errors, all blueprints registered
   - ✅ Database connection: Raw SQL queries execute successfully

3. **UI Validation:**
   - ✅ Manual collection page loads without header sections
   - ✅ Selection-info card displays with reduced size
   - ✅ "Seçili Dolly'ler" title visible

### Production Validation

- Mobile device (10.25.25.18) successfully connected to /api/manual-collection/groups
- No "name 'db' is not defined" errors in logs after fix
- Transaction rollback tested on SQL errors

---

## Known Issues

None. All critical issues from v1.0.6 have been resolved.

---

## Upgrade Instructions

### For Development Environment:

1. Pull latest code:
   ```bash
   git pull origin dev
   ```

2. Verify database migration 011 is applied:
   ```sql
   SELECT COUNT(*) FROM sys.columns 
   WHERE object_id = OBJECT_ID('DollySubmissionHold') 
   AND name IN ('ScanOrder', 'LoadingSessionId', 'LoadingCompletedAt', 'SeferNumarasi', 'PlakaNo')
   -- Expected: 5
   ```

3. Restart Flask application:
   ```bash
   python3 run.py
   ```

4. Test mobile API with curl:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        http://localhost:5000/api/manual-collection/groups
   ```

### For Production Environment:

1. **Backup database:**
   ```sql
   BACKUP DATABASE ControlTower TO DISK = 'ControlTower_backup_20251130.bak'
   ```

2. **Apply migration 011** (if not already applied):
   ```bash
   python3 -c "from scripts.run_migration import apply_migration; apply_migration('011')"
   ```

3. **Deploy code:**
   ```bash
   git checkout v1.0.7
   systemctl restart harmony-ecosystem
   ```

4. **Verify mobile connectivity:**
   - Test Zebra device connection
   - Check logs for "name 'db' is not defined" errors (should be absent)

---

## Technical Debt

### Resolved in This Release:
- ✅ SQLAlchemy ORM incompatibility with SQL Server raw connections
- ✅ Missing database import in mobile API routes
- ✅ Syntax errors in exception handlers

### Future Improvements:
- Consider migrating all ORM queries to raw SQL for consistency
- Add automated integration tests for mobile API endpoints
- Implement rate limiting for mobile API to prevent DoS

---

## Contributors

- AI Development Team
- QA Testing Team
- Mobile Device Integration Team

---

## Support

For issues or questions regarding this release:
- Review documentation: `docs/AI_DEVELOPMENT_PROMPT.md`
- Check API guide: `docs/ANDROID_API_FULL_GUIDE.md`
- Review error handling: `docs/ERROR_HANDLING_GUIDE.md`

---

**End of Release Notes v1.0.7**
