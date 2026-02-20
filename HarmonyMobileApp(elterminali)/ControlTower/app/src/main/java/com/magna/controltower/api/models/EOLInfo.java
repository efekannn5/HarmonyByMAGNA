package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;

/**
 * EOL Info model within a group
 * Part of ManualCollectionGroup response
 */
public class EOLInfo {
    @SerializedName("eol_id")
    private int eolId;
    
    @SerializedName("eol_name")
    private String eolName;
    
    @SerializedName("dolly_count")
    private int dollyCount;
    
    @SerializedName("scanned_count")
    private int scannedCount;

    public int getEolId() {
        return eolId;
    }

    public void setEolId(int eolId) {
        this.eolId = eolId;
    }

    public String getEolName() {
        return eolName;
    }

    public void setEolName(String eolName) {
        this.eolName = eolName;
    }

    public int getDollyCount() {
        return dollyCount;
    }

    public void setDollyCount(int dollyCount) {
        this.dollyCount = dollyCount;
    }

    public int getScannedCount() {
        return scannedCount;
    }

    public void setScannedCount(int scannedCount) {
        this.scannedCount = scannedCount;
    }
}
