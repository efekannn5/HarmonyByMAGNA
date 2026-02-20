# AI Development Prompt - HarmonyEcoSystem Project

## Project Context

You are a senior full-stack developer working on **HarmonyEcoSystem**, a dolly (vehicle carrier) management and tracking system. The system manages the end-to-end lifecycle of dollies from EOL (End of Line) station to customer shipment.

---

## Current System Architecture

### Technology Stack

**Backend:**
- Framework: Flask (Python 3.x)
- ORM: SQLAlchemy
- Database: Microsoft SQL Server (10.25.1.174:1433)
- Database Name: ControlTower
- Authentication: Session-based with Bearer tokens (8-hour expiry)

**Frontend:**
- Web: Jinja2 templates with Bootstrap 5
- Mobile: Android app (Kotlin - to be developed)
- JavaScript: Vanilla JS for dynamic interactions

**Server:**
- Host: 10.25.1.174
- Port: 8181
- Base URL: http://10.25.1.174:8181/api

### Project Structure

```
/home/sua_it_ai/controltower/HarmonyEcoSystem/
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── dolly.py
│   │   ├── dolly_hold.py
│   │   ├── forklift_session.py
│   │   ├── group.py
│   │   ├── lifecycle.py
│   │   ├── sefer.py
│   │   └── user.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api.py
│   │   ├── auth.py
│   │   └── dashboard.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── audit_service.py
│   │   ├── dolly_service.py
│   │   └── lifecycle_service.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── forklift_auth.py
│   │   └── security.py
│   ├── templates/
│   │   └── dashboard/
│   └── static/
├── config/
│   └── config.yaml
├── database/
│   └── *.sql (migration files)
├── docs/
├── logs/
├── run.py
└── requirements.txt
```

---

## Database Schema

### Core Tables

**1. DollyEOLInfo** (Live EOL Queue)
```sql
- DollyNo (PK, NVARCHAR(50)) - Dolly unique identifier
- VinNo (NVARCHAR(MAX)) - Vehicle VIN number(s), newline-separated
- CustomerReferans (NVARCHAR(255)) - Customer reference
- EOLName (NVARCHAR(100)) - EOL station name
- EOLID (INT) - EOL station ID
- EOLDATE (DATETIME2) - EOL completion timestamp
- Adet (INT) - Number of vehicles on dolly
- EOLDollyBarcode (NVARCHAR(100)) - Physical barcode on dolly
- Lokasyon (NVARCHAR(50)) - Current location
```

**2. DollySubmissionHold** (Temporary Tracking)
```sql
- Id (PK, INT IDENTITY)
- DollyNo (NVARCHAR(50))
- VinNo (NVARCHAR(500))
- Status (NVARCHAR(50)) - scanned | loading_completed | completed | removed
- TerminalUser (NVARCHAR(100)) - Forklift operator name
- CreatedAt (DATETIME2)
- UpdatedAt (DATETIME2)
- ScanOrder (INT) - Sequence number (1, 2, 3...)
- LoadingSessionId (NVARCHAR(50)) - Group identifier
- LoadingCompletedAt (DATETIME2)
- SeferNumarasi (NVARCHAR(20)) - Shipment number
- PlakaNo (NVARCHAR(20)) - Truck license plate
- SubmittedAt (DATETIME2)
```

**3. SeferDollyEOL** (Historical Shipments)
```sql
- Id (PK, INT IDENTITY)
- SeferNumarasi (NVARCHAR(20))
- PlakaNo (NVARCHAR(20))
- DollyNo (NVARCHAR(50))
- VinNo (NVARCHAR(500))
- Lokasyon (NVARCHAR(50))
- CustomerReferans (NVARCHAR(255))
- Adet (INT)
- EOLName (NVARCHAR(100))
- EOLID (INT)
- EOLDate (DATETIME2)
- TerminalUser (NVARCHAR(100)) - Forklift operator
- TerminalDate (DATETIME2) - Loading completion time
- VeriGirisUser (NVARCHAR(100)) - Web operator
- VeriGirisDate (DATETIME2) - Shipment completion time
- ASNDate (DATETIME2) - ASN sent timestamp
- IrsaliyeDate (DATETIME2) - Irsaliye sent timestamp
```

**4. ForkliftLoginSession** (Authentication)
```sql
- Id (PK, INT IDENTITY)
- OperatorBarcode (NVARCHAR(50))
- OperatorName (NVARCHAR(100))
- SessionToken (NVARCHAR(128) UNIQUE)
- IsActive (BIT)
- LoginAt (DATETIME2)
- ExpiresAt (DATETIME2)
- LastActivityAt (DATETIME2)
- DeviceId (NVARCHAR(100))
- LogoutAt (DATETIME2)
```

**5. DollyLifecycle** (Status Tracking)
```sql
- Id (PK, INT IDENTITY)
- DollyNo (NVARCHAR(50))
- VinNo (NVARCHAR(500))
- Status (NVARCHAR(50))
- Source (NVARCHAR(50))
- CreatedAt (DATETIME2)
- Metadata (NVARCHAR(MAX)) - JSON
```

**6. AuditLog** (Complete Audit Trail)
```sql
- Id (PK, INT IDENTITY)
- Action (NVARCHAR(100))
- Resource (NVARCHAR(100))
- ResourceId (NVARCHAR(255))
- ActorName (NVARCHAR(100))
- Metadata (NVARCHAR(MAX)) - JSON
- CreatedAt (DATETIME2)
```

---

## Business Process Flow

### Complete Workflow

```
[EOL Station] → [DollyEOLInfo Live Queue]
                        ↓
                [Forklift Operator - Android App]
                        ↓
                1. Login with barcode scan
                   └─ POST /api/forklift/login
                   └─ Creates ForkliftLoginSession
                   └─ Returns 8-hour Bearer token
                        ↓
                2. Start loading session
                   └─ Generate LoadingSessionId = "LOAD_YYYYMMDD_HHMMSS_OPERATORNAME"
                        ↓
                3. Scan dolly barcodes (one by one)
                   └─ POST /api/forklift/scan
                   └─ Lookup by EOLDollyBarcode in DollyEOLInfo
                   └─ Create DollySubmissionHold record
                   └─ Status: "scanned"
                   └─ ScanOrder: auto-increment (1, 2, 3...)
                   └─ Log to DollyLifecycle: "SCAN_CAPTURED"
                   └─ Log to AuditLog: "forklift.scan"
                        ↓
                3a. [OPTIONAL] Remove last dolly if mistake
                   └─ POST /api/forklift/remove-last
                   └─ Validate: Only last scanned dolly (highest ScanOrder)
                   └─ Update Status: "removed"
                   └─ Log to DollyLifecycle: "SCAN_CAPTURED" (revert)
                   └─ Log to AuditLog: "forklift.remove_dolly"
                        ↓
                4. Complete loading
                   └─ POST /api/forklift/complete-loading
                   └─ Update all "scanned" → "loading_completed"
                   └─ Set LoadingCompletedAt timestamp
                   └─ Log to DollyLifecycle: "WAITING_OPERATOR"
                   └─ Log to AuditLog: "forklift.complete_loading"
                        ↓
                5. Logout
                   └─ POST /api/forklift/logout
                   └─ Update ForkliftLoginSession: IsActive = 0, LogoutAt
                        ↓
                [Web Operator - Dashboard]
                        ↓
                1. Login with username/password
                   └─ POST /auth/login (session-based)
                        ↓
                2. View pending shipments
                   └─ GET /dashboard/operator/shipments
                   └─ List all LoadingSessionIds with Status="loading_completed"
                   └─ Display dollys with checkbox selection
                        ↓
                3. Complete shipment
                   └─ Select dollys (checkbox) - Optional: partial shipment
                   └─ Enter Sefer Number (validation required)
                   └─ Enter Plaka (license plate) (validation required)
                   └─ Select shipping type: ASN | Irsaliye | Both
                   └─ POST /dashboard/operator/shipments/complete
                        ↓
                   Validation:
                   ├─ Sefer format: ^[A-Z]{2,5}\d{4,10}$|^[A-Z0-9]{5,20}$
                   ├─ Plaka format: ^\d{2}[A-Z]{1,3}\d{2,5}$
                   └─ Duplicate check: SELECT FROM SeferDollyEOL WHERE SeferNumarasi=?
                        ↓
                   Processing:
                   ├─ Update selected DollySubmissionHold → Status="completed"
                   ├─ Create SeferDollyEOL records (one per dolly)
                   ├─ Set ASNDate/IrsaliyeDate based on shipping_type
                   ├─ Log to DollyLifecycle: "COMPLETED_ASN" | "COMPLETED_IRS" | "COMPLETED_BOTH"
                   └─ Log to AuditLog: "operator.complete_shipment"
                        ↓
                [Future: ASN/Irsaliye Integration]
                   └─ Send to customer system (pending customer readiness)
```

---

## Lifecycle States

```
EOL_READY → SCAN_CAPTURED → WAITING_OPERATOR → COMPLETED_ASN
                                              → COMPLETED_IRS
                                              → COMPLETED_BOTH
```

**State Definitions:**
- `EOL_READY`: Dolly completed EOL process, in DollyEOLInfo queue
- `SCAN_CAPTURED`: Forklift scanned dolly barcode
- `WAITING_OPERATOR`: Forklift completed loading, waiting for web operator
- `COMPLETED_ASN`: ASN sent to customer
- `COMPLETED_IRS`: Irsaliye (invoice) sent
- `COMPLETED_BOTH`: Both ASN and Irsaliye sent

---

## Authentication & Authorization

### Forklift Authentication (Android App)

**Flow:**
1. Scan employee barcode (e.g., "EMP12345")
2. POST /api/forklift/login with barcode
3. Backend creates ForkliftLoginSession with unique token
4. Token expires after 8 hours
5. Every API call updates LastActivityAt
6. Auto-logout after expiry or manual logout

**Implementation:**
```python
# app/utils/forklift_auth.py
@require_forklift_auth decorator
- Validates Bearer token
- Checks expiry
- Updates activity timestamp
- Sets g.forklift_session
```

### Web Authentication (Dashboard)

**Flow:**
1. Username/password login
2. Session-based authentication (Flask-Login)
3. Role-based access control (admin, operator)

**Implementation:**
```python
# app/utils/auth.py
@role_required('operator') decorator
- Checks current_user.role
- Denies access if role mismatch
```

---

## Error Handling Strategy

### Standard Error Response

**All API endpoints return:**
```json
{
  "error": "User-friendly error message",
  "message": "Technical details (optional)",
  "retryable": true/false
}
```

### Error Types

**1. Validation Errors (HTTP 400)**
- Invalid input format
- Business rule violations
- Duplicate data
- **Retryable:** Yes
- **Action:** Show error, allow user to correct and retry

**2. Authentication Errors (HTTP 401)**
- Invalid token
- Expired session
- **Retryable:** No
- **Action:** Redirect to login

**3. System Errors (HTTP 500)**
- Database connection failure
- Transaction timeout
- Unexpected exceptions
- **Retryable:** Yes (after rollback)
- **Action:** Show error, offer retry

### Transaction Safety

**All critical operations use:**
```python
try:
    # Business logic
    db.session.commit()
except ValueError:
    # Validation error - no rollback needed
    raise
except Exception as e:
    # System error - rollback everything
    db.session.rollback()
    self._log_critical_error(function_name, e, context)
    raise RuntimeError("User-friendly message. Transaction rolled back.")
```

**Critical Error Logging:**
```python
def _log_critical_error(function_name, error, context):
    # 1. Log to AuditLog (database)
    self.audit.log(
        action="system.critical_error",
        resource="system",
        resource_id=function_name,
        metadata={
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context
        }
    )
    
    # 2. Log to file (logs/app.log)
    logger.critical(f"CRITICAL ERROR in {function_name}: {error}")
```

---

## API Endpoints

### Authentication Endpoints

**1. Forklift Login**
```http
POST /api/forklift/login
Content-Type: application/json

{
  "operatorBarcode": "EMP12345",
  "operatorName": "Mehmet Yılmaz", // Optional
  "deviceId": "android-serial-123" // Optional
}

Response 200:
{
  "success": true,
  "sessionToken": "eyJhbGc...",
  "operatorName": "Mehmet Yılmaz",
  "expiresAt": "2025-11-27T02:30:00Z"
}

Response 400:
{
  "error": "Operatör barkodu gerekli",
  "retryable": true
}
```

**2. Forklift Logout**
```http
POST /api/forklift/logout
Authorization: Bearer <token>

Response 200:
{
  "success": true,
  "message": "Çıkış yapıldı"
}
```

**3. Session Validation**
```http
GET /api/forklift/session/validate
Authorization: Bearer <token>

Response 200:
{
  "valid": true,
  "operatorName": "Mehmet Yılmaz",
  "expiresAt": "2025-11-27T02:30:00Z"
}

Response 401:
{
  "error": "Session expired"
}
```

### Forklift Operations

**4. Scan Dolly**
```http
POST /api/forklift/scan
Authorization: Bearer <token>
Content-Type: application/json

{
  "dollyNo": "DL-5170427",
  "loadingSessionId": "LOAD_20251126_143052_MEHMET", // Optional, auto-generated
  "barcode": "BARCODE123" // Optional, for validation
}

Response 201:
{
  "dolly_no": "DL-5170427",
  "vin_no": "3FA6P0LU6FR100001",
  "scan_order": 1,
  "scanned_at": "2025-11-26T14:30:52Z",
  "loading_session_id": "LOAD_20251126_143052_MEHMET"
}

Response 400 (Validation Error):
{
  "error": "Dolly DL-999 zaten bu session'a eklenmiş",
  "retryable": true
}

Response 500 (System Error):
{
  "error": "Database error. İşlem geri alındı, lütfen tekrar deneyin.",
  "retryable": true
}
```

**5. Remove Last Dolly**
```http
POST /api/forklift/remove-last
Authorization: Bearer <token>
Content-Type: application/json

{
  "loadingSessionId": "LOAD_20251126_143052_MEHMET",
  "dollyBarcode": "BARCODE123"
}

Response 200:
{
  "dollyNo": "DL-5170427",
  "vinNo": "3FA6P0LU6FR100001",
  "scanOrder": 15,
  "removedAt": "2025-11-26T15:50:00Z"
}

Response 400 (Not Last Dolly):
{
  "error": "Sadece en son eklenen dolly çıkarılabilir. En son: Sıra 15, Seçilen: Sıra 10",
  "retryable": true
}
```

**6. Complete Loading**
```http
POST /api/forklift/complete-loading
Authorization: Bearer <token>
Content-Type: application/json

{
  "loadingSessionId": "LOAD_20251126_143052_MEHMET"
}

Response 200:
{
  "loadingSessionId": "LOAD_20251126_143052_MEHMET",
  "status": "loading_completed",
  "dollyCount": 15,
  "completedAt": "2025-11-26T15:45:00Z",
  "dollys": [
    {
      "dollyNo": "DL-5170427",
      "vinNo": "3FA6P0LU6FR100001",
      "scanOrder": 1
    }
    // ...
  ]
}
```

**7. List Loading Sessions**
```http
GET /api/forklift/sessions?status=scanned
Authorization: Bearer <token>

Response 200:
[
  {
    "loadingSessionId": "LOAD_20251126_143052_MEHMET",
    "status": "scanned",
    "forkliftUser": "Mehmet Yılmaz",
    "dollyCount": 8,
    "firstScanAt": "2025-11-26T14:30:52Z",
    "completedAt": null
  }
]
```

### Operator Operations

**8. List Pending Shipments**
```http
GET /api/operator/pending-shipments

Response 200:
[
  {
    "loadingSessionId": "LOAD_20251126_143052_MEHMET",
    "status": "loading_completed",
    "forkliftUser": "Mehmet Yılmaz",
    "dollyCount": 15,
    "completedAt": "2025-11-26T15:45:00Z",
    "dollys": [
      {
        "id": 123, // For checkbox selection
        "dollyNo": "DL-5170427",
        "vinNo": "3FA6P0LU6FR100001",
        "scanOrder": 1,
        "customerReferans": "FORD-EXPORT",
        "eolName": "EOL-A1"
      }
    ]
  }
]
```

**9. Complete Shipment**
```http
POST /api/operator/complete-shipment
Content-Type: application/json

{
  "loadingSessionId": "LOAD_20251126_143052_MEHMET",
  "seferNumarasi": "SFR20250001",
  "plakaNo": "34 ABC 123",
  "shippingType": "both", // "asn" | "irsaliye" | "both"
  "operatorUser": "ahmet.yilmaz",
  "selectedDollyIds": [123, 124, 125] // Optional: for partial shipment
}

Response 200:
{
  "loadingSessionId": "LOAD_20251126_143052_MEHMET",
  "seferNumarasi": "SFR20250001",
  "plakaNo": "34ABC123",
  "shippingType": "both",
  "dollyCount": 3,
  "completedAt": "2025-11-26T16:00:00Z",
  "partialShipment": true,
  "dollys": [...]
}

Response 400 (Validation Error):
{
  "error": "Geçersiz sefer numarası formatı: XYZ. Örnek: SFR20250001",
  "retryable": true
}

Response 400 (Duplicate):
{
  "error": "Sefer numarası SFR20250001 daha önce kullanılmış. Lütfen farklı bir numara girin.",
  "retryable": true
}

Response 500 (System Error):
{
  "error": "Sevkiyat tamamlama hatası: Database timeout. İşlem geri alındı, lütfen tekrar deneyin.",
  "retryable": true
}
```

### Mobile Manual Collection Operations

**10. Get EOL Groups**
```http
GET /api/manual-collection/groups
Authorization: Bearer <token>

Response 200:
[
  {
    "group_name": "V710-MR-EOL",
    "dolly_count": 8,
    "scanned_count": 3
  }
]
```

**11. Get Group Dollys**
```http
GET /api/manual-collection/groups/{group_name}
Authorization: Bearer <token>

Response 200:
{
  "group_name": "V710-MR-EOL",
  "dollys": [
    {
      "dolly_no": "DOLLY123",
      "vin_no": "VIN001\nVIN002\nVIN003",
      "scanned": false
    },
    {
      "dolly_no": "DOLLY456",
      "vin_no": "VIN004\nVIN005",
      "scanned": true
    }
  ]
}

Response 404:
{
  "error": "Grup 'XYZ' bulunamadı veya dolly yok",
  "retryable": true
}
```

**12. Scan Dolly to Group**
```http
POST /api/manual-collection/scan
Authorization: Bearer <token>
Content-Type: application/json

{
  "group_name": "V710-MR-EOL",
  "barcode": "DOLLY123"
}

Response 200:
{
  "success": true,
  "dolly_no": "DOLLY123",
  "message": "Dolly eklendi"
}

Response 400:
{
  "error": "Bu dolly zaten taranmış",
  "retryable": true
}

Response 400:
{
  "error": "Bu dolly 'V710-MR-EOL' grubuna ait, 'ABC' değil",
  "retryable": true
}
```

**13. Remove Last Scanned Dolly**
```http
POST /api/manual-collection/remove-last
Authorization: Bearer <token>
Content-Type: application/json

{
  "group_name": "V710-MR-EOL",
  "barcode": "DOLLY456"
}

Response 200:
{
  "success": true,
  "dolly_no": "DOLLY456",
  "message": "Dolly çıkartıldı"
}

Response 400:
{
  "error": "Bu dolly taranmamış",
  "retryable": true
}
```

---

## Service Layer Implementation

### DollyService (app/services/dolly_service.py)

**Key Methods:**

```python
class DollyService:
    def __init__(self, config):
        self.config = config
        self.audit = AuditService()
        self.lifecycle = LifecycleService()
    
    # Forklift operations
    def forklift_scan_dolly(self, dolly_no, forklift_user, loading_session_id=None, barcode=None):
        """
        Scan dolly barcode and add to loading session.
        
        Steps:
        1. Lookup dolly in DollyEOLInfo by DollyNo or EOLDollyBarcode
        2. Validate dolly exists and not already in session
        3. Create DollySubmissionHold record
        4. Calculate ScanOrder (max + 1)
        5. Log to DollyLifecycle (SCAN_CAPTURED)
        6. Log to AuditLog (forklift.scan)
        7. Return hold entry
        
        Raises:
        - ValueError: If validation fails (retryable)
        - RuntimeError: If system error (retryable after rollback)
        """
    
    def forklift_remove_last_dolly(
        self,
        loading_session_id: str,
        dolly_barcode: str,
        forklift_user: Optional[str] = None
    ) -> Dict[str, Any]:
        """Remove last scanned dolly (LIFO).
        
        CRITICAL JIS VALIDATION:
        This method implements strict validation to prevent wrong dolly removal.
        JIS manufacturing has ZERO error tolerance - wrong removal breaks the entire workflow.
        
        Algorithm (5-step validation):
        1. Query SQL Server for ALL scanned dollys (ORDER BY ScanOrder DESC)
        2. Get FIRST record = LAST scanned dolly (MAX ScanOrder)
        3. Lookup dolly by scanned barcode from DollyEOLInfo
        4. CRITICAL: Compare scanned DollyNo with LAST dolly's DollyNo
        5. If MISMATCH → Reject with error, If MATCH → Mark as removed
        
        Why this order?
        - SQL Server is source of truth for "what is last"
        - Client barcode is ONLY for validation, NOT for selection
        - Prevents race conditions and manipulation
        
        Args:
            loading_session_id: Session ID
            dolly_barcode: Barcode of dolly to remove (validation only)
            forklift_user: Operator name
        
        Returns:
            Removed dolly info
        
        Raises:
            ValueError: If validation fails (wrong dolly, not found, session empty)
            RuntimeError: If system error (transaction rolled back)
        
        Example Error Cases:
        - Operator scanned Kasa-001, but LAST is Kasa-003 → ValueError
        - Session has no scanned dollys → ValueError
        - Barcode not found in DollyEOLInfo → ValueError
        """
    
    def forklift_complete_loading(self, loading_session_id, forklift_user=None):
        """
        Mark all scanned dollys as loading completed.
        
        Steps:
        1. Get all holds with Status="scanned"
        2. Update Status to "loading_completed"
        3. Set LoadingCompletedAt timestamp
        4. Log to DollyLifecycle (WAITING_OPERATOR)
        5. Log to AuditLog (forklift.complete_loading)
        6. Return summary
        
        Raises:
        - ValueError: If session not found
        - RuntimeError: If system error
        """
    
    # Operator operations
    def operator_complete_shipment(self, loading_session_id, sefer_numarasi, plaka_no, 
                                   shipping_type, operator_user=None, selected_dolly_ids=None):
        """
        Complete shipment with Sefer, Plaka, and ASN/Irsaliye.
        
        Steps:
        1. Validate sefer format (regex)
        2. Validate plaka format (regex)
        3. Check duplicate sefer (database lookup)
        4. Get holds (all or selected by IDs)
        5. For each dolly:
           - Update DollySubmissionHold Status="completed"
           - Create SeferDollyEOL record
           - Set ASNDate/IrsaliyeDate based on shipping_type
           - Log to DollyLifecycle (final status)
        6. Commit transaction
        7. Log to AuditLog (operator.complete_shipment)
        8. Return summary
        
        Raises:
        - ValueError: Validation errors (retryable)
        - RuntimeError: System errors (retryable after rollback)
        """
    
    # Validation methods
    def validate_sefer_format(self, sefer):
        """Regex: ^[A-Z]{2,5}\d{4,10}$|^[A-Z0-9]{5,20}$"""
    
    def validate_plaka_format(self, plaka):
        """Regex: ^\d{2}[A-Z]{1,3}\d{2,5}$ (Turkish plate)"""
    
    def check_duplicate_sefer(self, sefer):
        """Query SeferDollyEOL for existing sefer number"""
    
    # Error logging
    def _log_critical_error(self, function_name, error, context):
        """
        Log critical errors to:
        1. AuditLog table (action="system.critical_error")
        2. Application log file (logs/app.log, level=CRITICAL)
        
        Metadata:
        - error_type: Exception class name
        - error_message: str(error)
        - traceback: full stack trace
        - context: function parameters and state
        - timestamp: UTC timestamp
        """
```

---

## CRITICAL: JIS Manufacturing - Zero Error Tolerance

### Why Strict Validation Matters

**JIS (Just-In-Sequence)** manufacturing requires **EXACT sequence** of vehicles. One wrong dolly can break the entire production line.

**Real-world scenario that MUST be prevented:**

```
Loading Session: LOAD_20251126_MEHMET
├─ Kasa-001 (ScanOrder: 1) - Status: scanned
├─ Kasa-002 (ScanOrder: 2) - Status: scanned  
└─ Kasa-003 (ScanOrder: 3) - Status: scanned  ← LAST

Operator accidentally scans Kasa-001 for removal.

❌ WRONG APPROACH (Trusting client):
   - Remove Kasa-001 because client sent it
   - Result: Middle dolly removed, sequence broken
   - Customer receives wrong vehicle order
   - Production line stops
   - Financial penalties

✅ CORRECT APPROACH (SQL Server validation):
   1. Query: What is the LAST dolly? → Kasa-003
   2. Compare: Client sent Kasa-001, LAST is Kasa-003
   3. Reject: "Only last dolly can be removed"
   4. Operator re-scans correct barcode (Kasa-003)
   5. Validation passes, removal succeeds
```

### Critical Validation Pattern

**NEVER trust client input for sequence operations!**

```python
# ❌ WRONG - Trusts client barcode
def remove_dolly_wrong(barcode):
    dolly = find_by_barcode(barcode)
    dolly.status = "removed"  # No validation!
    db.commit()

# ✅ CORRECT - SQL Server is source of truth
def remove_dolly_correct(barcode):
    # 1. Get LAST from SQL (source of truth)
    last_dolly = db.query(DollySubmissionHold)\
        .filter_by(LoadingSessionId=session_id, Status="scanned")\
        .order_by(ScanOrder.desc())\
        .first()
    
    # 2. Get client's dolly
    scanned_dolly = find_by_barcode(barcode)
    
    # 3. CRITICAL VALIDATION
    if scanned_dolly.DollyNo != last_dolly.DollyNo:
        raise ValueError(
            f"Only last dolly can be removed. "
            f"Last: {last_dolly.DollyNo}, Scanned: {scanned_dolly.DollyNo}"
        )
    
    # 4. Validation passed - safe to remove
    last_dolly.status = "removed"
    db.commit()
```

### SQL Server Validation Queries

**1. Get LAST dolly (source of truth):**
```sql
SELECT TOP 1 
    Id, DollyNo, VinNo, ScanOrder, Status
FROM DollySubmissionHold
WHERE LoadingSessionId = @SessionId
  AND Status = 'scanned'
ORDER BY ScanOrder DESC
```

**2. Validate barcode matches LAST:**
```sql
DECLARE @LastDollyNo NVARCHAR(50)
DECLARE @ScannedDollyNo NVARCHAR(50)

-- Get last dolly from session
SELECT TOP 1 @LastDollyNo = DollyNo
FROM DollySubmissionHold
WHERE LoadingSessionId = @SessionId AND Status = 'scanned'
ORDER BY ScanOrder DESC

-- Get dolly from barcode
SELECT @ScannedDollyNo = DollyNo
FROM DollyEOLInfo
WHERE EOLDollyBarcode = @Barcode

-- CRITICAL VALIDATION
IF @LastDollyNo != @ScannedDollyNo
    RAISERROR('Only last dolly can be removed!', 16, 1)
```

### Test Scenarios (All MUST Pass)

**Test 1: Normal Removal (PASS)**
```
Session: Kasa-001, Kasa-002, Kasa-003 (LAST)
Action: Scan Kasa-003 barcode
Expected: ✅ Success - Kasa-003 removed
```

**Test 2: Wrong Dolly (FAIL - Protection Working)**
```
Session: Kasa-001, Kasa-002, Kasa-003 (LAST)
Action: Scan Kasa-001 barcode
Expected: ❌ 400 Error - "Only last dolly can be removed. Last: Kasa-003, Scanned: Kasa-001"
```

**Test 3: Empty Session (FAIL - Protection Working)**
```
Session: All dollys already removed
Action: Scan any barcode
Expected: ❌ 400 Error - "Session has no scanned dollys"
```

**Test 4: Unknown Barcode (FAIL - Protection Working)**
```
Action: Scan barcode not in DollyEOLInfo
Expected: ❌ 400 Error - "Barcode 'XYZ' not found in system"
```

---

## Code Implementation Guidelines


### When Adding New Features

**1. Database Changes**
- Create migration file: `database/NNN_description.sql`
- Include rollback statements in comments
- Test on development database first

**2. Model Updates**
- Add/modify SQLAlchemy models in `app/models/`
- Follow existing naming conventions
- Add relationship definitions

**3. Service Layer**
- Implement business logic in `app/services/`
- Use try-except with transaction rollback
- Call `_log_critical_error()` for system errors
- Return user-friendly error messages

**4. API Routes**
- Add endpoints in `app/routes/api.py`
- Use `@require_forklift_auth` for forklift endpoints
- Use `@login_required` and `@role_required()` for web endpoints
- Return standardized error format
- Include `retryable` flag in errors

**5. Error Handling Template**
```python
@api_bp.post("/endpoint")
@require_forklift_auth
def endpoint_function():
    try:
        # Get session and parameters
        session = g.forklift_session
        payload = request.get_json()
        
        # Validate parameters
        if not payload.get("required_field"):
            return jsonify({
                "error": "required_field is required",
                "retryable": True
            }), 400
        
        # Call service layer
        result = _service().service_method(...)
        
        return jsonify(result), 200
        
    except ValueError as e:
        # Validation errors
        return jsonify({
            "error": str(e),
            "retryable": True
        }), 400
        
    except RuntimeError as e:
        # System errors (after rollback)
        return jsonify({
            "error": str(e),
            "retryable": True
        }), 500
        
    except Exception as e:
        # Unexpected errors
        return jsonify({
            "error": "Beklenmeyen hata",
            "message": str(e),
            "retryable": False
        }), 500
```

**6. Audit Logging**
```python
self.audit.log(
    action="module.action_name",
    resource="resource_type",
    resource_id="identifier",
    actor_name=user_name,
    metadata={
        "key": "value",
        "nested": {"data": "here"}
    }
)
```

**7. Lifecycle Logging**
```python
self.lifecycle.log_status(
    dolly_no,
    vin_no,
    LifecycleService.Status.STATUS_NAME,
    source="SOURCE",
    metadata={"context": "data"}
)
```

---

## Testing Requirements

### Unit Tests
- Validation functions (sefer, plaka, duplicate)
- Error logging function
- Model relationships

### Integration Tests
- Complete workflow (login → scan → complete → logout)
- Remove last dolly
- Partial shipment
- Error handling for all endpoints

### Manual Test Scenarios
1. Normal flow
2. Remove last dolly flow
3. Partial shipment flow
4. Validation error handling
5. System error handling
6. Authentication error handling

---

## Documentation Standards

**When adding new features, update:**

1. **API Documentation** (`docs/ANDROID_API_FULL_GUIDE.md`)
   - Add endpoint documentation
   - Include request/response examples
   - Add Kotlin code examples
   - Document error responses

2. **Quick Reference** (`docs/ANDROID_QUICK_REFERENCE.md`)
   - Add endpoint to table
   - Add quick example

3. **Changelog** (`docs/CHANGELOG.md`)
   - Document changes
   - Include algorithm updates
   - Add deployment notes

4. **Error Handling Guide** (`docs/ERROR_HANDLING_GUIDE.md`)
   - Document new error types
   - Add handling examples

---

## Deployment Checklist

**Before deploying:**
- [ ] Run database migrations
- [ ] Test all endpoints
- [ ] Update documentation
- [ ] Test error handling
- [ ] Verify rollback works
- [ ] Check audit logging
- [ ] Review performance
- [ ] Update version number

**Deployment steps:**
```bash
# 1. Pull code
cd /home/sua_it_ai/controltower/HarmonyEcoSystem
git pull origin main

# 2. Run migrations (if any)
sqlcmd -S 10.25.1.174 -d ControlTower -i database/XXX_migration.sql

# 3. Restart application
sudo systemctl restart harmony-ecosystem

# 4. Verify
curl http://10.25.1.174:8181/api/health

# 5. Test critical endpoints
curl -X POST http://10.25.1.174:8181/api/forklift/login ...
```

---

## Current Version

**Version:** 1.0.6  
**Last Updated:** 26 Kasım 2025  
**Status:** Production Ready

---

## AI Development Instructions

When you receive a feature request or bug fix for this system:

### Step 1: Understanding
- Read the current design and architecture
- Identify which components need changes
- Check existing similar implementations
- Review database schema requirements

### Step 2: Planning
- List all files that need modification/creation
- Identify database changes required
- Plan error handling strategy
- Consider impact on existing features

### Step 3: Implementation Order
1. Database migrations (if needed)
2. Model updates (if needed)
3. Service layer methods
4. API routes
5. Templates/UI (if needed)
6. Tests
7. Documentation

### Step 4: Code Implementation
- Follow existing code patterns
- Use transaction safety (try-except-rollback)
- Add comprehensive error handling
- Include audit logging
- Use standardized error responses
- Add validation where needed

### Step 5: Error Handling
- Validation errors → HTTP 400, retryable: true
- Auth errors → HTTP 401, retryable: false
- System errors → HTTP 500, retryable: true (after rollback)
- Always call `_log_critical_error()` for system errors

### Step 6: Documentation
- Update API documentation with examples
- Add to quick reference
- Document in changelog
- Include error handling examples

### Step 7: Testing
- Write test scenarios
- Include error cases
- Test rollback functionality
- Verify audit logging

### Response Format
When implementing, provide:
1. **Summary** - What you're implementing
2. **Files Modified/Created** - List with explanations
3. **Code Changes** - Complete code blocks with context
4. **Database Changes** - SQL scripts if needed
5. **Testing Instructions** - How to test
6. **Documentation Updates** - What docs to update

### Code Quality Standards
- Use type hints where possible
- Add docstrings to all functions
- Follow PEP 8 for Python
- Use meaningful variable names
- Add comments for complex logic
- Keep functions focused and small

### Security Considerations
- Never store passwords in plain text
- Always validate user input
- Use parameterized queries
- Sanitize error messages (no stack traces to users)
- Implement proper authentication checks

---

## Common Patterns

### Pattern 1: Adding New Endpoint

```python
# app/routes/api.py
@api_bp.post("/new-endpoint")
@require_forklift_auth  # or @login_required + @role_required()
def new_endpoint():
    try:
        session = g.forklift_session  # or current_user
        payload = request.get_json()
        
        # Validation
        required_field = payload.get("requiredField")
        if not required_field:
            return jsonify({"error": "requiredField is required", "retryable": True}), 400
        
        # Service call
        result = _service().new_service_method(
            required_field=required_field,
            user=session.OperatorName
        )
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({"error": str(e), "retryable": True}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e), "retryable": True}), 500
    except Exception as e:
        return jsonify({"error": "Unexpected error", "message": str(e), "retryable": False}), 500
```

### Pattern 2: Adding Service Method

```python
# app/services/dolly_service.py
def new_service_method(self, required_field, user=None):
    """
    Description of what this does.
    
    Args:
        required_field: Description
        user: Optional user name
    
    Returns:
        Dictionary with result data
    
    Raises:
        ValueError: If validation fails
        RuntimeError: If system error occurs
    """
    try:
        # Validation
        if not self.validate_something(required_field):
            raise ValueError("Validation failed: ...")
        
        # Business logic
        record = Model.query.filter_by(field=required_field).first()
        if not record:
            raise ValueError("Record not found")
        
        record.status = "new_status"
        record.updated_at = datetime.utcnow()
        
        # Commit
        db.session.commit()
        
        # Audit log
        self.audit.log(
            action="module.action",
            resource="resource_type",
            resource_id=str(record.id),
            actor_name=user or "system",
            metadata={"field": required_field}
        )
        
        return {
            "id": record.id,
            "status": record.status,
            "updatedAt": record.updated_at.isoformat()
        }
        
    except ValueError:
        raise  # Re-raise validation errors
    except Exception as e:
        db.session.rollback()
        self._log_critical_error("new_service_method", e, {
            "required_field": required_field,
            "user": user
        })
        raise RuntimeError(f"Operation failed: {str(e)}. Transaction rolled back.")
```

---

## Important Notes

1. **Never break backward compatibility** unless absolutely necessary
2. **Always use transactions** for data modifications
3. **Always log to AuditLog** for critical operations
4. **Always provide user-friendly error messages**
5. **Always include retryable flag** in error responses
6. **Never expose stack traces** to end users
7. **Always validate input** before processing
8. **Always check for duplicates** where needed
9. **Always update documentation** when adding features
10. **Always test error scenarios** not just happy path

---

## Support Resources

**Documentation Files:**
- `docs/ANDROID_API_FULL_GUIDE.md` - Complete API reference
- `docs/ANDROID_QUICK_REFERENCE.md` - Quick start guide
- `docs/ERROR_HANDLING_GUIDE.md` - Error handling patterns
- `docs/CHANGELOG.md` - Version history
- `docs/API_ENDPOINTS.md` - Endpoint listing

**Database Documentation:**
- `database/*.sql` - All migration files
- `docs/database_schema_diagram.md` - Schema visualization
- `docs/data_model_graph.md` - Entity relationships

**Configuration:**
- `config/config.yaml` - Application configuration
- Server: 10.25.1.174:8181
- Database: 10.25.1.174:1433/ControlTower

---

## End of Prompt

You now have complete context about the HarmonyEcoSystem project. When implementing features:

1. Follow the established patterns
2. Maintain code quality standards
3. Ensure proper error handling
4. Update all relevant documentation
5. Provide complete, production-ready code
6. Include testing instructions

Ask clarifying questions if any requirement is unclear before implementing.
