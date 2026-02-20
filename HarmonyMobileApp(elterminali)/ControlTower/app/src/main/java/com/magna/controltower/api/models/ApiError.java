package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;

/**
 * Standard error response model
 */
public class ApiError {
    @SerializedName("error")
    private String error;
    
    @SerializedName("retryable")
    private boolean retryable;

    public ApiError() {
        this.retryable = true;
    }

    public ApiError(String error, boolean retryable) {
        this.error = error;
        this.retryable = retryable;
    }

    public String getError() {
        return error;
    }

    public void setError(String error) {
        this.error = error;
    }

    public boolean isRetryable() {
        return retryable;
    }

    public void setRetryable(boolean retryable) {
        this.retryable = retryable;
    }
}
