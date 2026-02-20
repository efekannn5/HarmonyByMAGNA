# Forklift Telemetry + Location Extension (API Guide)

Purpose: add movement-based performance measurement + realtime location for forklifts
without touching the main flow (login / group / scan / submit).

This document is for HarmonyEco System backend changes and API contract.

---

## 1) Goals

- Track forklift movement state (moving / idle) using gyro + accelerometer
- Send GPS position so HarmonyEco can show realtime forklift location
- Compute performance metrics (distance, moving time, idle time, stops, harsh events)
- Keep existing app behavior unchanged (feature runs in background)

Non-goals:
- No change to login / scan / submit logic
- No UI changes required (optional admin toggles only)

---

## 2) High-Level Flow

1) App logs in and receives token (existing flow).
2) Background telemetry service starts after login (silent).
3) Service samples:
   - gyro + accel (movement)
   - GPS (location)
4) Service POSTs batches to backend.
5) Backend stores raw samples, updates latest location, and computes performance.

---

## 3) Device-side collection (reference behavior)

### Sensors
- Gyroscope: detect rotation / vibration
- Accelerometer: detect linear motion
- Location: GPS / fused provider

### Movement state (simple, stable, not too sensitive)

We avoid too sensitive detection with hysteresis + min-duration.

Variables (configurable from backend):
```
gyro_threshold_rad_s = 0.18
accel_threshold_mps2 = 1.4   # ~0.14g
move_min_duration_ms = 1500
stop_min_duration_ms = 3000
sampling_hz = 25
```

Movement decision:
```
gyro_mag = sqrt(gx^2 + gy^2 + gz^2)
accel_mag = sqrt(ax^2 + ay^2 + az^2) - 9.81

moving if (gyro_mag > gyro_threshold_rad_s OR accel_mag > accel_threshold_mps2)
for at least move_min_duration_ms

idle if (gyro_mag < gyro_threshold_rad_s*0.7 AND accel_mag < accel_threshold_mps2*0.7)
for at least stop_min_duration_ms
```

### Location sampling rate
```
moving -> every 3-5s
idle   -> every 15-30s
```
Use accuracy filter:
- Accept location if accuracy_m <= 25m (moving) or <= 50m (idle)
- If no GPS, send motion-only sample with gps_available=false

### Batching
- Send telemetry batch every 10s while moving, 30s while idle
- Also send immediately on state change (idle -> moving, moving -> idle)

---

## 4) API Contract (new endpoints)

### 4.1 POST /api/forklift/telemetry
Batch upload of telemetry samples.

Headers:
```
Authorization: Bearer <token>
Content-Type: application/json
```

Request body:
```json
{
  "device_id": "android-2f6c9a1e",
  "operator_barcode": "EMP12345",
  "forklift_id": "FL-07",
  "app_version": "1.6.0",
  "schema_version": 1,
  "samples": [
    {
      "ts": "2026-01-30T12:03:05.120Z",
      "seq": 12899,
      "movement_state": "moving",
      "motion_confidence": 0.82,
      "gyro_mag_rad_s": 0.25,
      "accel_mag_mps2": 1.9,
      "gps_available": true,
      "lat": 40.991234,
      "lon": 29.112345,
      "speed_mps": 2.6,
      "bearing_deg": 170.0,
      "accuracy_m": 7.2,
      "alt_m": 12.4,
      "provider": "fused"
    },
    {
      "ts": "2026-01-30T12:03:09.900Z",
      "seq": 12900,
      "movement_state": "moving",
      "motion_confidence": 0.78,
      "gyro_mag_rad_s": 0.21,
      "accel_mag_mps2": 1.6,
      "gps_available": true,
      "lat": 40.991290,
      "lon": 29.112390,
      "speed_mps": 2.8,
      "bearing_deg": 175.0,
      "accuracy_m": 6.8,
      "alt_m": 12.6,
      "provider": "fused"
    }
  ]
}
```

Notes:
- `forklift_id` optional (backend can map device_id -> forklift_id)
- `seq` monotonic counter for dedup
- `movement_state` in {"moving","idle","unknown"}

Response (200):
```json
{
  "accepted": 2,
  "server_time": "2026-01-30T12:03:10.050Z",
  "config": {
    "gyro_threshold_rad_s": 0.18,
    "accel_threshold_mps2": 1.4,
    "move_min_duration_ms": 1500,
    "stop_min_duration_ms": 3000,
    "sampling_hz": 25,
    "location_interval_moving_ms": 4000,
    "location_interval_idle_ms": 20000
  },
  "next_upload_in_ms": 10000
}
```

Errors:
- 401 Unauthorized (token invalid)
- 400 Bad Request (missing fields / invalid data)
- 413 Payload Too Large (if too many samples)

---

### 4.2 GET /api/forklift/locations/latest
Realtime location for dashboard.

Query params:
```
?plant_id=...&forklift_id=...&active_only=true
```

Response:
```json
{
  "items": [
    {
      "forklift_id": "FL-07",
      "operator_barcode": "EMP12345",
      "ts": "2026-01-30T12:03:09.900Z",
      "lat": 40.991290,
      "lon": 29.112390,
      "speed_mps": 2.8,
      "accuracy_m": 6.8,
      "movement_state": "moving"
    }
  ]
}
```

---

### 4.3 GET /api/forklift/performance/summary
Aggregated metrics for reporting.

Query params:
```
?from=2026-01-30T00:00:00Z&to=2026-01-30T23:59:59Z&forklift_id=FL-07
```

Response:
```json
{
  "forklift_id": "FL-07",
  "from": "2026-01-30T00:00:00Z",
  "to": "2026-01-30T23:59:59Z",
  "distance_m": 12450,
  "moving_time_s": 14800,
  "idle_time_s": 9200,
  "avg_speed_mps": 0.84,
  "max_speed_mps": 3.6,
  "stop_count": 41,
  "harsh_accel_count": 3,
  "harsh_brake_count": 2,
  "harsh_turn_count": 4
}
```

---

## 5) Backend Storage (recommended)

### 5.1 Table: forklift_telemetry_samples
```
id (pk)
device_id
forklift_id
operator_barcode
ts
seq
lat, lon, alt_m
speed_mps, bearing_deg, accuracy_m, provider
movement_state, motion_confidence
gyro_mag_rad_s, accel_mag_mps2
gps_available
created_at
```
Indexes:
- (forklift_id, ts)
- (device_id, seq)

### 5.2 Table: forklift_location_latest
```
forklift_id (pk)
operator_barcode
ts
lat, lon, speed_mps, accuracy_m
movement_state
updated_at
```

### 5.3 Table: forklift_performance_daily
```
forklift_id
date
distance_m
moving_time_s
idle_time_s
avg_speed_mps
max_speed_mps
stop_count
harsh_accel_count
harsh_brake_count
harsh_turn_count
```

---

## 6) Backend Processing Rules

### Dedup / order
- Use (device_id, seq) or ts for idempotency
- If out-of-order, accept but compute metrics by ts ordering

### Distance
Compute using Haversine between valid GPS samples
- ignore jumps if accuracy_m > 50m
- ignore speed spikes if speed_mps > 8.0 (tunable)

### Movement state
Prefer device-reported `movement_state`, but backend can recompute
if missing using speed + accel.

### Harsh events (tunable)
```
harsh_accel if delta_speed_mps / delta_t > 2.0 m/s^2
harsh_brake if delta_speed_mps / delta_t < -2.5 m/s^2
harsh_turn if gyro_mag_rad_s > 0.8 for > 1s
```

---

## 7) Realtime Visualization Guidance

HarmonyEco can:
- show forklift marker by latest location
- color by movement_state (moving vs idle)
- show path of last N minutes (query from telemetry table)
- show performance summary per shift/day

Optional: provide WebSocket or SSE later for push updates. For now
poll `/api/forklift/locations/latest` every 3-5 seconds.

---

## 8) Compatibility / Safety

- If GPS is disabled, still send motion-only samples
- If permissions denied, feature is silent (no impact to main flow)
- If battery low, backend can lower sampling via config response

---

## 9) Minimal App-side Changes (reference only)

- Add background service to collect sensor + location
- Start service after successful login, stop on logout
- No UI change required
- Use Authorization token already stored in SessionManager

---

## 10) Checklist for Backend Implementation

- [ ] Create telemetry endpoints
- [ ] Store raw samples
- [ ] Update latest location table
- [ ] Compute performance metrics (daily + on-demand)
- [ ] Provide config response for thresholds
- [ ] Add rate limits (max samples per request)

---

If you want, I can tailor thresholds, payload, or add extra fields
(shift_id, plant_id, route_id) based on your backend model.

---

## 11) Terminal (Android) ekibi icin net istek listesi

### Konum izinleri
- ACCESS_FINE_LOCATION + (Android 10+) ACCESS_BACKGROUND_LOCATION mutlaka istenmeli
- "arkaplanda konum" gerekcesi gosterilmeli
- Izin yoksa hicbir sample gonderilmesin veya gps_available=false acikca set edilsin

### Konum uretimi (FusedLocationProvider)
- interval: hareketliyken 4-5 sn, idle iken 20 sn
- priority: PRIORITY_HIGH_ACCURACY
- fastestInterval: ~2 sn
- smallestDisplacement: 3-5 m

### Payload zorunlu alanlar (her sample)
- lat, lon, accuracy_m, provider
- movement_state ("moving" / "idle")
- speed_mps (varsa)
- ts ISO UTC (orn. 2026-01-30T05:41:00.123Z)
- forklift_id (yoksa en azindan cihazda sabit device_id)

### Hareket/operatör bilgisi
- Operator barkodu payload'da kalabilir, UI'de gosterilmiyor (anonimlik saglandi)
- Gyro/accel esikleri dokumandaki gibi; movement_state hesaplanip gonderilsin
- Hesaplanamiyorsa "unknown" gonderilsin

### Gonderim periyodu
- hareketliyken 10 sn batch
- idle 30 sn batch
- state degisince hemen POST

---

## 12) Yenileme sorunu kontrol listesi

- Kodda cache kapatildi; deploy/restart sonrasi sayfa 4.5 sn'de bir cekmeye devam eder
- "Son yenileme" ilerlemiyorsa:
  - oturum suresi / 401 olabilir
  - ag hatasi olabilir
  - tarayici konsolunda hata var mi kontrol edin

---

## 13) GPS hala gelmiyorsa

- Cihazda konum servisi acik mi, izin verilmis mi kontrol edin
- Test icin gercek bir GPS'li sample gonderin
- app.log'da "with_gps=X" satirinda X>0 gorunmeli
- Marker ve Lat/Lon dolmali
