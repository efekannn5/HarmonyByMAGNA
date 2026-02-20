package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;

/**
 * EOL Group model for Manual Collection
 * GET /api/manual-collection/groups
 */
public class EOLGroup {
    @SerializedName("group_name")
    private String groupName;
    
    @SerializedName("dolly_count")
    private int dollyCount;
    
    @SerializedName("scanned_count")
    private int scannedCount;

    public String getGroupName() {
        return groupName;
    }

    public void setGroupName(String groupName) {
        this.groupName = groupName;
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
