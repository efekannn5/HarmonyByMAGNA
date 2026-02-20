package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;

/**
 * Manual scan request for Manual Collection
 * POST /api/manual-collection/scan
 */
public class ManualScanRequest {
    @SerializedName("group_name")
    private String groupName;
    
    @SerializedName("eol_name")
    private String eolName;
    
    @SerializedName("barcode")
    private String barcode;

    public ManualScanRequest(String groupName, String eolName, String barcode) {
        this.groupName = groupName;
        this.eolName = eolName;
        this.barcode = barcode;
    }

    public String getGroupName() {
        return groupName;
    }

    public void setGroupName(String groupName) {
        this.groupName = groupName;
    }

    public String getEolName() {
        return eolName;
    }

    public void setEolName(String eolName) {
        this.eolName = eolName;
    }

    public String getBarcode() {
        return barcode;
    }

    public void setBarcode(String barcode) {
        this.barcode = barcode;
    }
}
