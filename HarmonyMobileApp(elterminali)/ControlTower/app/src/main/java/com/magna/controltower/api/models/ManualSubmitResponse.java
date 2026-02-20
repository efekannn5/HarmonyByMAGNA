package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;

/**
 * Response from manual collection submit operation
 * POST /api/manual-collection/mobile-submit
 */
public class ManualSubmitResponse {
    @SerializedName("success")
    private boolean success;
    
    @SerializedName("submitted_count")
    private int submittedCount;
    
    @SerializedName("vin_count")
    private int vinCount;
    
    @SerializedName("part_number")
    private String partNumber;
    
    @SerializedName("message")
    private String message;

    public boolean isSuccess() {
        return success;
    }

    public void setSuccess(boolean success) {
        this.success = success;
    }

    public int getSubmittedCount() {
        return submittedCount;
    }

    public void setSubmittedCount(int submittedCount) {
        this.submittedCount = submittedCount;
    }

    public int getVinCount() {
        return vinCount;
    }

    public void setVinCount(int vinCount) {
        this.vinCount = vinCount;
    }

    public String getPartNumber() {
        return partNumber;
    }

    public void setPartNumber(String partNumber) {
        this.partNumber = partNumber;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }
}
