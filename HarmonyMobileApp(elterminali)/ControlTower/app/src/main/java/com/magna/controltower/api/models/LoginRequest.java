package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;

/**
 * Login request model for Harmony Ecosystem API
 * POST /api/forklift/login
 */
public class LoginRequest {
    @SerializedName("operatorBarcode")
    private String operatorBarcode;
    
    @SerializedName("operatorName")
    private String operatorName;
    
    @SerializedName("deviceId")
    private String deviceId;

    public LoginRequest(String operatorBarcode, String operatorName, String deviceId) {
        this.operatorBarcode = operatorBarcode;
        this.operatorName = operatorName;
        this.deviceId = deviceId;
    }

    public LoginRequest(String operatorBarcode, String deviceId) {
        this(operatorBarcode, null, deviceId);
    }

    public LoginRequest(String operatorBarcode) {
        this(operatorBarcode, null, null);
    }

    public String getOperatorBarcode() {
        return operatorBarcode;
    }

    public void setOperatorBarcode(String operatorBarcode) {
        this.operatorBarcode = operatorBarcode;
    }

    public String getOperatorName() {
        return operatorName;
    }

    public void setOperatorName(String operatorName) {
        this.operatorName = operatorName;
    }

    public String getDeviceId() {
        return deviceId;
    }

    public void setDeviceId(String deviceId) {
        this.deviceId = deviceId;
    }
}
