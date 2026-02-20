package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;
import java.util.List;

public class ForkliftTelemetryRequest {
    @SerializedName("device_id")
    private String deviceId;

    @SerializedName("operator_barcode")
    private String operatorBarcode;

    @SerializedName("forklift_id")
    private String forkliftId;

    @SerializedName("app_version")
    private String appVersion;

    @SerializedName("schema_version")
    private int schemaVersion;

    @SerializedName("samples")
    private List<TelemetrySample> samples;

    public ForkliftTelemetryRequest(
            String deviceId,
            String operatorBarcode,
            String forkliftId,
            String appVersion,
            int schemaVersion,
            List<TelemetrySample> samples
    ) {
        this.deviceId = deviceId;
        this.operatorBarcode = operatorBarcode;
        this.forkliftId = forkliftId;
        this.appVersion = appVersion;
        this.schemaVersion = schemaVersion;
        this.samples = samples;
    }

    public String getDeviceId() { return deviceId; }
    public String getOperatorBarcode() { return operatorBarcode; }
    public String getForkliftId() { return forkliftId; }
    public String getAppVersion() { return appVersion; }
    public int getSchemaVersion() { return schemaVersion; }
    public List<TelemetrySample> getSamples() { return samples; }
}
