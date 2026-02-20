package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;

/**
 * Request to remove last scanned dolly
 * POST /api/forklift/remove-last
 */
public class RemoveLastRequest {
    @SerializedName("loadingSessionId")
    private String loadingSessionId;
    
    @SerializedName("dollyBarcode")
    private String dollyBarcode;

    public RemoveLastRequest(String loadingSessionId, String dollyBarcode) {
        this.loadingSessionId = loadingSessionId;
        this.dollyBarcode = dollyBarcode;
    }

    public String getLoadingSessionId() {
        return loadingSessionId;
    }

    public void setLoadingSessionId(String loadingSessionId) {
        this.loadingSessionId = loadingSessionId;
    }

    public String getDollyBarcode() {
        return dollyBarcode;
    }

    public void setDollyBarcode(String dollyBarcode) {
        this.dollyBarcode = dollyBarcode;
    }
}
