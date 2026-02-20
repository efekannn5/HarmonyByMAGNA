package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;
import java.util.List;

/**
 * Manual Collection Group model
 * GET /api/manual-collection/groups
 */
public class ManualCollectionGroup {
    @SerializedName("group_id")
    private int groupId;
    
    @SerializedName("group_name")
    private String groupName;
    
    @SerializedName("part_number")
    private String partNumber;
    
    @SerializedName("eols")
    private List<EOLInfo> eols;
    
    @SerializedName("total_dolly_count")
    private int totalDollyCount;
    
    @SerializedName("total_scanned_count")
    private int totalScannedCount;

    public int getGroupId() {
        return groupId;
    }

    public void setGroupId(int groupId) {
        this.groupId = groupId;
    }

    public String getGroupName() {
        return groupName;
    }

    public void setGroupName(String groupName) {
        this.groupName = groupName;
    }

    public String getPartNumber() {
        return partNumber;
    }

    public void setPartNumber(String partNumber) {
        this.partNumber = partNumber;
    }

    public List<EOLInfo> getEols() {
        return eols;
    }

    public void setEols(List<EOLInfo> eols) {
        this.eols = eols;
    }

    public int getTotalDollyCount() {
        return totalDollyCount;
    }

    public void setTotalDollyCount(int totalDollyCount) {
        this.totalDollyCount = totalDollyCount;
    }

    public int getTotalScannedCount() {
        return totalScannedCount;
    }

    public void setTotalScannedCount(int totalScannedCount) {
        this.totalScannedCount = totalScannedCount;
    }
}
