# Analytics Views (Detailed) - Documentation

## Goal
Provide a full, end-to-end timeline and performance reporting using **read-only SQL Server views**. No application code changes required.

## Key Assumptions
- Timestamps written by the app use **UTC** (`datetime.utcnow()` in code). Views convert UTC -> Turkey time using:
  - `(utc_datetime AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time'`
- SQL Server version supports `AT TIME ZONE` (2016+).
- Some stages may be missing when records are deleted (e.g., `DollySubmissionHold` rows removed after ASN send).

## Source Tables Used
- `DollyEOLInfo` (production/EOL entry)
- `DollySubmissionHold` (scan/hold workflow)
- `SeferDollyEOL` (final shipment)
- `WebOperatorTask` (operator tasks)
- `DollyLifecycle` (status events)
- `DollyGroup`, `DollyGroupEOL`, `PWorkStation` (group & EOL mapping)

## New Views (file: `database/021_create_analytics_views_detailed.sql`)

### 1) `vw_Analytics_DollyTimelineDetailed`
**Grain:** 1 row per `DollyNo + VinNo`.

**What it includes**
- Identification: `DollyNo`, `VinNo`, `DollyOrderNo`, `PartNumber`, `CustomerReferans`, `EOLName`, `EOLID`, `GroupName`, `ShippingTag`.
- Operators: `ForkliftOperator`, `WebOperator`.
- Timestamps in UTC and Turkey time for:
  - Production (EOL), Scan, Loading Complete, Task Created/Completed, ASN/Irsaliye.
- Durations in minutes:
  - Production -> First Scan
  - First Scan -> Loading Completed
  - Task Created -> Shipment
  - Scan -> Shipment
  - Production -> Shipment
- Lifecycle first/last status from `DollyLifecycle`.

**Typical use**
- Build the end-to-end timeline for any dolly/vin.
- Compute custom KPIs per dolly, EOL, group, operator, or day.

**Example**
```sql
SELECT TOP 100 *
FROM dbo.vw_Analytics_DollyTimelineDetailed
WHERE EOLName = 'EOL_1'
ORDER BY ProductionCompletedAtLocal DESC;
```

---

### 2) `vw_Analytics_EventTimeline`
**Grain:** 1 row per event.

**Event sources**
- `DollyEOLInfo`: `EOL_COMPLETED`, `EOL_RECORDED`
- `DollySubmissionHold`: `SCAN`, `LOADING_COMPLETED`, `HOLD_SUBMITTED`
- `WebOperatorTask`: `TASK_CREATED`, `TASK_COMPLETED`
- `SeferDollyEOL`: `ASN_SENT`, `IRSALIYE_SENT`
- `DollyLifecycle`: `LIFECYCLE_<STATUS>`

**Typical use**
- Build a full event timeline for any dolly/vin.
- Track gaps and delays between events.

**Example**
```sql
SELECT *
FROM dbo.vw_Analytics_EventTimeline
WHERE DollyNo = '5170427'
ORDER BY EventTimeUtc;
```

---

### 3) `vw_Analytics_LoadingSessionTimeline`
**Grain:** 1 row per loading session (`LoadingSessionId`).

**KPIs**
- Session duration (scan start -> scan end)
- Scan-to-loading completion
- Dolly/VIN counts

**Example**
```sql
SELECT TOP 50 *
FROM dbo.vw_Analytics_LoadingSessionTimeline
ORDER BY FirstScanAtLocal DESC;
```

---

### 4) `vw_Analytics_ScanIntervals`
**Grain:** 1 row per scan (with previous scan delta).

**KPIs**
- Time between scans within the same session
- Operator scan pace

**Example**
```sql
SELECT *
FROM dbo.vw_Analytics_ScanIntervals
WHERE LoadingSessionId = 'LOAD_20260130_101500_MEHMET'
ORDER BY ScanAtUtc;
```

---

### 5) `vw_Analytics_ForkliftPerformanceDaily`
**Grain:** per forklift operator + part + shift + day (local time).

**KPIs**
- Dolly/VIN counts
- Avg scan -> loading complete
- Avg scan -> ASN / Irsaliye
- Shift label (`SHIFT_1`, `SHIFT_2`, `SHIFT_3`)

**Example**
```sql
SELECT *
FROM dbo.vw_Analytics_ForkliftPerformanceDaily
WHERE ActivityDateLocal >= DATEADD(DAY, -7, CAST(GETDATE() AS date));
```

---

### 6) `vw_Analytics_WebOperatorPerformanceDaily`
**Grain:** per web operator + part + shift + day (local time).

**KPIs**
- Dolly/VIN counts
- ASN / Irsaliye counts
- Avg loading complete -> shipment
- Shift label (`SHIFT_1`, `SHIFT_2`, `SHIFT_3`)

**Example**
```sql
SELECT *
FROM dbo.vw_Analytics_WebOperatorPerformanceDaily
ORDER BY ActivityDateLocal DESC;
```

---

### 6B) `vw_Analytics_ShiftSummaryDaily`
**Grain:** per shift + day (local time), all roles.

**KPIs**
- Dolly/VIN counts
- Avg durations by shift
- On-time percent

**Example**
```sql
SELECT *
FROM dbo.vw_Analytics_ShiftSummaryDaily
ORDER BY ActivityDateLocal DESC, ShiftLabel;
```

---

### 7) `vw_Analytics_GroupEOLPerformanceDaily`
**Grain:** per EOL + Group + day.

**KPIs**
- Dolly/VIN counts
- Average duration metrics

**Example**
```sql
SELECT *
FROM dbo.vw_Analytics_GroupEOLPerformanceDaily
WHERE GroupName = 'G1'
ORDER BY ProductionDateLocal DESC;
```

---

### 8) `vw_Analytics_TaskPerformance`
**Grain:** per PartNumber.

**KPIs**
- Task duration
- Dolly/VIN counts
- Status tracking

**Example**
```sql
SELECT *
FROM dbo.vw_Analytics_TaskPerformance
WHERE TaskStatus = 'pending'
ORDER BY TaskCreatedAtLocal DESC;
```

---

## How to Use (Recommended Flow)
1) Use `vw_Analytics_DollyTimelineDetailed` as the **base dataset**.
2) For full event history, join or filter using `vw_Analytics_EventTimeline`.
3) For operator KPIs, use `vw_Analytics_ForkliftPerformanceDaily` and `vw_Analytics_WebOperatorPerformanceDaily`.
4) For shift-level health, use `vw_Analytics_ShiftSummaryDaily`.
4) For bottlenecks / cycle time, aggregate the duration columns from the timeline view.

## Caveats / Data Quality
- If ASN is sent via `operator_send_asn`, `DollySubmissionHold` rows are deleted, so durations that depend on `DollySubmissionHold` may be NULL for completed shipments.
- Forklift performance uses `DollyLifecycle` (`SCAN_CAPTURED`) with `Metadata` JSON. If Metadata is missing or not JSON, operator name may be NULL.
- Shift summary uses a **best-available time** (first scan → loading complete → shipment → production record). If scan timestamps are missing, shift is derived from the next available stage.
- `EOLDATE` is a DATE in `DollyEOLInfo`; time-of-day is not available there.
- Group mapping uses `PWorkStationName = EOLName`. If names don’t match, Group fields can be NULL.
- `AT TIME ZONE` assumes the stored timestamps are UTC. If any table stores local time, local conversions will shift by +3 hours.

## Validation Checklist
- Compare random dolly/vin in UI with `vw_Analytics_DollyTimelineDetailed` output.
- Validate local time conversions against known timestamps.
- Confirm group mapping for EOLs.
- Ensure ASN/irsaliye events exist after completion.

## Permissions (read-only user example)
```sql
-- Create login/user (example)
CREATE LOGIN analytics_reader WITH PASSWORD = 'StrongPasswordHere!';
CREATE USER analytics_reader FOR LOGIN analytics_reader;

-- Grant SELECT on views only
GRANT SELECT ON dbo.vw_Analytics_DollyTimelineDetailed TO analytics_reader;
GRANT SELECT ON dbo.vw_Analytics_EventTimeline TO analytics_reader;
GRANT SELECT ON dbo.vw_Analytics_LoadingSessionTimeline TO analytics_reader;
GRANT SELECT ON dbo.vw_Analytics_ScanIntervals TO analytics_reader;
GRANT SELECT ON dbo.vw_Analytics_ForkliftPerformanceDaily TO analytics_reader;
GRANT SELECT ON dbo.vw_Analytics_WebOperatorPerformanceDaily TO analytics_reader;
GRANT SELECT ON dbo.vw_Analytics_ShiftSummaryDaily TO analytics_reader;
GRANT SELECT ON dbo.vw_Analytics_GroupEOLPerformanceDaily TO analytics_reader;
GRANT SELECT ON dbo.vw_Analytics_TaskPerformance TO analytics_reader;

-- Deny writes
DENY INSERT, UPDATE, DELETE ON SCHEMA::dbo TO analytics_reader;
```
