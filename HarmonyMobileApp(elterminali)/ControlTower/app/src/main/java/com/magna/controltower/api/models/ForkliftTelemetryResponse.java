package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;

public class ForkliftTelemetryResponse {
    @SerializedName("accepted")
    private int accepted;

    @SerializedName("server_time")
    private String serverTime;

    @SerializedName("next_upload_in_ms")
    private long nextUploadInMs;

    @SerializedName("config")
    private TelemetryConfig config;

    public int getAccepted() { return accepted; }
    public String getServerTime() { return serverTime; }
    public long getNextUploadInMs() { return nextUploadInMs; }
    public TelemetryConfig getConfig() { return config; }

    public static class TelemetryConfig {
        @SerializedName("gyro_threshold_rad_s")
        private Double gyroThresholdRadS;

        @SerializedName("accel_threshold_mps2")
        private Double accelThresholdMps2;

        @SerializedName("move_min_duration_ms")
        private Integer moveMinDurationMs;

        @SerializedName("stop_min_duration_ms")
        private Integer stopMinDurationMs;

        @SerializedName("sampling_hz")
        private Integer samplingHz;

        @SerializedName("location_interval_moving_ms")
        private Integer locationIntervalMovingMs;

        @SerializedName("location_interval_idle_ms")
        private Integer locationIntervalIdleMs;

        public Double getGyroThresholdRadS() { return gyroThresholdRadS; }
        public Double getAccelThresholdMps2() { return accelThresholdMps2; }
        public Integer getMoveMinDurationMs() { return moveMinDurationMs; }
        public Integer getStopMinDurationMs() { return stopMinDurationMs; }
        public Integer getSamplingHz() { return samplingHz; }
        public Integer getLocationIntervalMovingMs() { return locationIntervalMovingMs; }
        public Integer getLocationIntervalIdleMs() { return locationIntervalIdleMs; }
    }
}
