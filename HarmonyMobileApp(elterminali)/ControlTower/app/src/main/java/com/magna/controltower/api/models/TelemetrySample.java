package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;

public class TelemetrySample {
    @SerializedName("ts")
    private String ts;

    @SerializedName("seq")
    private long seq;

    @SerializedName("movement_state")
    private String movementState;

    @SerializedName("motion_confidence")
    private double motionConfidence;

    @SerializedName("gyro_mag_rad_s")
    private double gyroMagRadS;

    @SerializedName("accel_mag_mps2")
    private double accelMagMps2;

    @SerializedName("gps_available")
    private boolean gpsAvailable;

    @SerializedName("lat")
    private Double lat;

    @SerializedName("lon")
    private Double lon;

    @SerializedName("speed_mps")
    private Float speedMps;

    @SerializedName("bearing_deg")
    private Float bearingDeg;

    @SerializedName("accuracy_m")
    private Float accuracyM;

    @SerializedName("alt_m")
    private Float altM;

    @SerializedName("provider")
    private String provider;

    public TelemetrySample(
            String ts,
            long seq,
            String movementState,
            double motionConfidence,
            double gyroMagRadS,
            double accelMagMps2,
            boolean gpsAvailable,
            Double lat,
            Double lon,
            Float speedMps,
            Float bearingDeg,
            Float accuracyM,
            Float altM,
            String provider
    ) {
        this.ts = ts;
        this.seq = seq;
        this.movementState = movementState;
        this.motionConfidence = motionConfidence;
        this.gyroMagRadS = gyroMagRadS;
        this.accelMagMps2 = accelMagMps2;
        this.gpsAvailable = gpsAvailable;
        this.lat = lat;
        this.lon = lon;
        this.speedMps = speedMps;
        this.bearingDeg = bearingDeg;
        this.accuracyM = accuracyM;
        this.altM = altM;
        this.provider = provider;
    }
}
