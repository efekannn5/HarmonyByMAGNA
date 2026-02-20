package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;

/**
 * Scan dolly request for Forklift operations
 * POST /api/forklift/scan
 */
public class ScanDollyRequest {
    @SerializedName("dollyNo")
    private String dollyNo;
    
    @SerializedName("loadingSessionId")
    private String loadingSessionId;
    
    @SerializedName("barcode")
    private String barcode;

    public ScanDollyRequest(String dollyNo, String loadingSessionId, String barcode) {
        this.dollyNo = dollyNo;
        this.loadingSessionId = loadingSessionId;
        this.barcode = barcode;
    }

    public ScanDollyRequest(String dollyNo) {
        this(dollyNo, null, null);
    }

    public String getDollyNo() {
        return dollyNo;
    }

    public void setDollyNo(String dollyNo) {
        this.dollyNo = dollyNo;
    }

    public String getLoadingSessionId() {
        return loadingSessionId;
    }

    public void setLoadingSessionId(String loadingSessionId) {
        this.loadingSessionId = loadingSessionId;
    }

    public String getBarcode() {
        return barcode;
    }

    public void setBarcode(String barcode) {
        this.barcode = barcode;
    }
}
