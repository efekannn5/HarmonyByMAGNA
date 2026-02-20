package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;

/**
 * Request to complete loading session
 * POST /api/forklift/complete-loading
 */
public class CompleteLoadingRequest {
    @SerializedName("loadingSessionId")
    private String loadingSessionId;

    public CompleteLoadingRequest(String loadingSessionId) {
        this.loadingSessionId = loadingSessionId;
    }

    public String getLoadingSessionId() {
        return loadingSessionId;
    }

    public void setLoadingSessionId(String loadingSessionId) {
        this.loadingSessionId = loadingSessionId;
    }
}
