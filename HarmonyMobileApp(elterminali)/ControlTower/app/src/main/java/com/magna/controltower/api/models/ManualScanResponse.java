package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;

/**
 * Response from manual scan operation
 * POST /api/manual-collection/scan
 */
public class ManualScanResponse {
    @SerializedName("success")
    private boolean success;
    
    @SerializedName("dolly_no")
    private String dollyNo;
    
    @SerializedName("message")
    private String message;
    
    @SerializedName("expected_dolly")
    private String expectedDolly;
    
    @SerializedName("received_dolly")
    private String receivedDolly;
    
    @SerializedName("eol_name")
    private String eolName;

    public boolean isSuccess() {
        return success;
    }

    public void setSuccess(boolean success) {
        this.success = success;
    }

    public String getDollyNo() {
        return dollyNo;
    }

    public void setDollyNo(String dollyNo) {
        this.dollyNo = dollyNo;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public String getExpectedDolly() {
        return expectedDolly;
    }

    public void setExpectedDolly(String expectedDolly) {
        this.expectedDolly = expectedDolly;
    }

    public String getReceivedDolly() {
        return receivedDolly;
    }

    public void setReceivedDolly(String receivedDolly) {
        this.receivedDolly = receivedDolly;
    }

    public String getEolName() {
        return eolName;
    }

    public void setEolName(String eolName) {
        this.eolName = eolName;
    }
}
