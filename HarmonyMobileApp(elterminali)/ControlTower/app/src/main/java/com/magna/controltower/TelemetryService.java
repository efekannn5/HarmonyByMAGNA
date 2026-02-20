package com.magna.controltower;

import android.Manifest;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.location.Location;
import android.os.Build;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.IBinder;
import android.provider.Settings;

import androidx.annotation.Nullable;
import androidx.core.content.ContextCompat;

import com.google.android.gms.location.LocationCallback;
import com.google.android.gms.location.LocationRequest;
import com.google.android.gms.location.LocationResult;
import com.google.android.gms.location.LocationServices;
import com.google.android.gms.location.LocationAvailability;
import com.google.android.gms.location.FusedLocationProviderClient;
import com.magna.controltower.api.models.ForkliftTelemetryRequest;
import com.magna.controltower.api.models.ForkliftTelemetryResponse;
import com.magna.controltower.api.models.TelemetrySample;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicLong;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class TelemetryService extends Service implements SensorEventListener {
    private static final int SCHEMA_VERSION = 1;
    private static final long DEFAULT_UPLOAD_MOVING_MS = 10_000L;
    private static final long DEFAULT_UPLOAD_IDLE_MS = 30_000L;
    private static final long DEFAULT_SAMPLE_INTERVAL_MS = 1000L;
    private static final int DEFAULT_LOCATION_MOVING_MS = 4000;
    private static final int DEFAULT_LOCATION_IDLE_MS = 20000;

    private static final double DEFAULT_GYRO_THRESHOLD = 0.18;
    private static final double DEFAULT_ACCEL_THRESHOLD = 1.4;
    private static final long DEFAULT_MOVE_MIN_MS = 1500L;
    private static final long DEFAULT_STOP_MIN_MS = 3000L;

    private HandlerThread workerThread;
    private Handler workerHandler;
    private SensorManager sensorManager;
    private FusedLocationProviderClient fusedClient;
    private LocationCallback locationCallback;
    private ApiClient apiClient;

    private volatile double gyroMag = 0.0;
    private volatile double accelMag = 0.0;
    private volatile Location lastLocation;
    private volatile long lastLocationTs = 0L;

    private double gyroThreshold = DEFAULT_GYRO_THRESHOLD;
    private double accelThreshold = DEFAULT_ACCEL_THRESHOLD;
    private long moveMinMs = DEFAULT_MOVE_MIN_MS;
    private long stopMinMs = DEFAULT_STOP_MIN_MS;
    private long uploadMovingMs = DEFAULT_UPLOAD_MOVING_MS;
    private long uploadIdleMs = DEFAULT_UPLOAD_IDLE_MS;
    private int locationMovingMs = DEFAULT_LOCATION_MOVING_MS;
    private int locationIdleMs = DEFAULT_LOCATION_IDLE_MS;
    private int fastestLocationMs = 2000;
    private float smallestDisplacementM = 4f;

    private final List<TelemetrySample> pendingSamples = new ArrayList<>();
    private final AtomicLong seq = new AtomicLong(1);
    private long lastSampleTs = 0L;

    private String movementState = "unknown";
    private long movingCandidateStart = 0L;
    private long idleCandidateStart = 0L;

    private final Runnable sampleRunnable = new Runnable() {
        @Override
        public void run() {
            collectSample();
            workerHandler.postDelayed(this, DEFAULT_SAMPLE_INTERVAL_MS);
        }
    };

    private final Runnable uploadRunnable = new Runnable() {
        @Override
        public void run() {
            uploadBatch(false);
            long delay = "moving".equals(movementState) ? uploadMovingMs : uploadIdleMs;
            workerHandler.postDelayed(this, delay);
        }
    };

    public static void start(Context context) {
        Intent i = new Intent(context, TelemetryService.class);
        context.startService(i);
    }

    public static void stop(Context context) {
        Intent i = new Intent(context, TelemetryService.class);
        context.stopService(i);
    }

    @Override
    public void onCreate() {
        super.onCreate();
        workerThread = new HandlerThread("telemetry-worker");
        workerThread.start();
        workerHandler = new Handler(workerThread.getLooper());
        sensorManager = (SensorManager) getSystemService(SENSOR_SERVICE);
        fusedClient = LocationServices.getFusedLocationProviderClient(this);
        locationCallback = new LocationCallback() {
            @Override
            public void onLocationResult(LocationResult result) {
                if (result == null) return;
                Location loc = result.getLastLocation();
                if (loc != null) {
                    lastLocation = loc;
                    lastLocationTs = System.currentTimeMillis();
                }
            }

            @Override
            public void onLocationAvailability(LocationAvailability availability) {
                // no-op
            }
        };
        apiClient = new ApiClient(this);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (!SessionManager.isValid(this)) {
            stopSelf();
            return START_NOT_STICKY;
        }
        startSensors();
        startLocationUpdates();
        workerHandler.removeCallbacks(sampleRunnable);
        workerHandler.post(sampleRunnable);
        workerHandler.removeCallbacks(uploadRunnable);
        workerHandler.postDelayed(uploadRunnable, uploadMovingMs);
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        stopSensors();
        stopLocationUpdates();
        if (workerHandler != null) {
            workerHandler.removeCallbacks(sampleRunnable);
            workerHandler.removeCallbacks(uploadRunnable);
        }
        if (workerThread != null) {
            workerThread.quitSafely();
        }
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    private void startSensors() {
        if (sensorManager == null) return;
        Sensor gyro = sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE);
        Sensor accel = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
        if (gyro != null) {
            sensorManager.registerListener(this, gyro, SensorManager.SENSOR_DELAY_GAME);
        }
        if (accel != null) {
            sensorManager.registerListener(this, accel, SensorManager.SENSOR_DELAY_GAME);
        }
    }

    private void stopSensors() {
        if (sensorManager != null) {
            sensorManager.unregisterListener(this);
        }
    }

    private void startLocationUpdates() {
        if (fusedClient == null) return;
        if (!hasLocationPermission()) return;
        int interval = "moving".equals(movementState) ? locationMovingMs : locationIdleMs;
        LocationRequest request = new LocationRequest.Builder(LocationRequest.PRIORITY_HIGH_ACCURACY, interval)
                .setMinUpdateIntervalMillis(fastestLocationMs)
                .setMinUpdateDistanceMeters(smallestDisplacementM)
                .build();
        try {
            fusedClient.requestLocationUpdates(request, locationCallback, workerHandler.getLooper());
        } catch (Exception ignored) {
        }
    }

    private void stopLocationUpdates() {
        if (fusedClient == null) return;
        if (!hasLocationPermission()) return;
        try {
            fusedClient.removeLocationUpdates(locationCallback);
        } catch (Exception ignored) {
        }
    }

    private boolean hasLocationPermission() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.M) return true;
        int fine = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION);
        int coarse = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION);
        boolean base = fine == PackageManager.PERMISSION_GRANTED || coarse == PackageManager.PERMISSION_GRANTED;
        if (!base) return false;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            int bg = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_BACKGROUND_LOCATION);
            return bg == PackageManager.PERMISSION_GRANTED;
        }
        return true;
    }

    @Override
    public void onSensorChanged(SensorEvent event) {
        if (event.sensor.getType() == Sensor.TYPE_GYROSCOPE) {
            double gx = event.values[0];
            double gy = event.values[1];
            double gz = event.values[2];
            gyroMag = Math.sqrt(gx * gx + gy * gy + gz * gz);
        } else if (event.sensor.getType() == Sensor.TYPE_ACCELEROMETER) {
            double ax = event.values[0];
            double ay = event.values[1];
            double az = event.values[2];
            double mag = Math.sqrt(ax * ax + ay * ay + az * az);
            accelMag = Math.abs(mag - 9.81);
        }
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {
        // no-op
    }

    private void collectSample() {
        long now = System.currentTimeMillis();
        if (now - lastSampleTs < DEFAULT_SAMPLE_INTERVAL_MS) return;
        lastSampleTs = now;

        String newState = computeMovementState(now);
        if (!newState.equals(movementState)) {
            movementState = newState;
            uploadBatch(true);
            adjustLocationInterval();
        }

        TelemetrySample sample = buildSample(now);
        if (sample != null) {
            pendingSamples.add(sample);
        }
    }

    private String computeMovementState(long now) {
        boolean movingCandidate = gyroMag > gyroThreshold || accelMag > accelThreshold;
        boolean idleCandidate = gyroMag < gyroThreshold * 0.7 && accelMag < accelThreshold * 0.7;

        if (movingCandidate) {
            if (movingCandidateStart == 0L) movingCandidateStart = now;
            idleCandidateStart = 0L;
        } else if (idleCandidate) {
            if (idleCandidateStart == 0L) idleCandidateStart = now;
            movingCandidateStart = 0L;
        }

        if (movingCandidateStart > 0L && now - movingCandidateStart >= moveMinMs) {
            return "moving";
        }
        if (idleCandidateStart > 0L && now - idleCandidateStart >= stopMinMs) {
            return "idle";
        }
        return movementState;
    }

    private void adjustLocationInterval() {
        if (fusedClient == null) return;
        if (!hasLocationPermission()) return;
        int interval = "moving".equals(movementState) ? locationMovingMs : locationIdleMs;
        stopLocationUpdates();
        LocationRequest request = new LocationRequest.Builder(LocationRequest.PRIORITY_HIGH_ACCURACY, interval)
                .setMinUpdateIntervalMillis(fastestLocationMs)
                .setMinUpdateDistanceMeters(smallestDisplacementM)
                .build();
        try {
            fusedClient.requestLocationUpdates(request, locationCallback, workerHandler.getLooper());
        } catch (Exception ignored) {
        }
    }

    private TelemetrySample buildSample(long now) {
        Location loc = lastLocation;
        boolean gpsAvailable = loc != null && (now - lastLocationTs) < 30_000L;
        Double lat = null;
        Double lon = null;
        Float speed = null;
        Float bearing = null;
        Float accuracy = null;
        Float alt = null;
        String provider = null;

        if (gpsAvailable) {
            accuracy = loc.hasAccuracy() ? loc.getAccuracy() : null;
            float accuracyLimit = "moving".equals(movementState) ? 25f : 50f;
            if (accuracy != null && accuracy > accuracyLimit) {
                gpsAvailable = false;
            } else {
                lat = loc.getLatitude();
                lon = loc.getLongitude();
                speed = loc.hasSpeed() ? loc.getSpeed() : null;
                bearing = loc.hasBearing() ? loc.getBearing() : null;
                alt = loc.hasAltitude() ? (float) loc.getAltitude() : null;
                provider = "fused";
            }
        }

        String ts = isoTime(now);
        double confidence = "moving".equals(movementState) ? 0.8 : ("idle".equals(movementState) ? 0.6 : 0.4);

        return new TelemetrySample(
                ts,
                seq.getAndIncrement(),
                movementState,
                confidence,
                gyroMag,
                accelMag,
                gpsAvailable,
                lat,
                lon,
                speed,
                bearing,
                accuracy,
                alt,
                provider
        );
    }

    private void uploadBatch(boolean force) {
        if (!SessionManager.isValid(this)) return;
        if (pendingSamples.isEmpty()) return;
        if (!force && pendingSamples.size() < 2) return;

        List<TelemetrySample> batch = new ArrayList<>(pendingSamples);
        pendingSamples.clear();

        ForkliftTelemetryRequest request = new ForkliftTelemetryRequest(
                getDeviceIdValue(),
                getOperatorBarcode(),
                null,
                getAppVersion(),
                SCHEMA_VERSION,
                batch
        );

        apiClient.getService().sendTelemetry(request).enqueue(new Callback<ForkliftTelemetryResponse>() {
            @Override
            public void onResponse(Call<ForkliftTelemetryResponse> call, Response<ForkliftTelemetryResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    applyConfig(response.body());
                }
            }

            @Override
            public void onFailure(Call<ForkliftTelemetryResponse> call, Throwable t) {
                // Drop silently; next batch will continue.
            }
        });
    }

    private void applyConfig(ForkliftTelemetryResponse resp) {
        ForkliftTelemetryResponse.TelemetryConfig cfg = resp.getConfig();
        if (cfg == null) return;
        if (cfg.getGyroThresholdRadS() != null) gyroThreshold = cfg.getGyroThresholdRadS();
        if (cfg.getAccelThresholdMps2() != null) accelThreshold = cfg.getAccelThresholdMps2();
        if (cfg.getMoveMinDurationMs() != null) moveMinMs = cfg.getMoveMinDurationMs();
        if (cfg.getStopMinDurationMs() != null) stopMinMs = cfg.getStopMinDurationMs();
        if (cfg.getLocationIntervalMovingMs() != null) locationMovingMs = cfg.getLocationIntervalMovingMs();
        if (cfg.getLocationIntervalIdleMs() != null) locationIdleMs = cfg.getLocationIntervalIdleMs();
        if (resp.getNextUploadInMs() > 0) {
            uploadMovingMs = resp.getNextUploadInMs();
        }
    }

    private String getDeviceIdValue() {
        return Settings.Secure.getString(getContentResolver(), Settings.Secure.ANDROID_ID);
    }

    private String getAppVersion() {
        try {
            return getPackageManager()
                    .getPackageInfo(getPackageName(), 0)
                    .versionName;
        } catch (Exception e) {
            return "unknown";
        }
    }

    private String getOperatorBarcode() {
        String barcode = SessionManager.getUserBarcode(this);
        if (barcode == null || barcode.isEmpty()) {
            barcode = SessionManager.username(this);
        }
        return barcode;
    }

    private String isoTime(long now) {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.US);
        sdf.setTimeZone(java.util.TimeZone.getTimeZone("UTC"));
        return sdf.format(new Date(now));
    }
}
