package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;

/**
 * Response from complete loading operation
 * POST /api/forklift/complete-loading
 */
public class CompleteLoadingResponse {
    @SerializedName("loadingSessionId")
    private String loadingSessionId;
    
    @SerializedName("dollyCount")
    private int dollyCount;
    
    @SerializedName("completedAt")
    private String completedAt;
    
    @SerializedName("status")
    private String status;

    public String getLoadingSessionId() {
        return loadingSessionId;
    }

    public void setLoadingSessionId(String loadingSessionId) {
        this.loadingSessionId = loadingSessionId;
    }

    public int getDollyCount() {
        return dollyCount;
    }

    public void setDollyCount(int dollyCount) {
        this.dollyCount = dollyCount;
    }

    public String getCompletedAt() {
        return completedAt;
    }

    public void setCompletedAt(String completedAt) {
        this.completedAt = completedAt;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }
}
