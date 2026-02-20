package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;

/**
 * Request to submit/complete manual collection from mobile
 * POST /api/manual-collection/mobile-submit
 */
public class ManualSubmitRequest {
    @SerializedName("eol_name")
    private String eolName;
    
    @SerializedName("group_id")
    private Integer groupId;
    
    @SerializedName("group_name")
    private String groupName;
    
    @SerializedName("part_number")
    private String partNumber;

    // EOL bazlı submit (mevcut)
    public ManualSubmitRequest(String eolName) {
        this.eolName = eolName;
    }
    
    // Grup bazlı submit (yeni)
    public ManualSubmitRequest(Integer groupId, String groupName, String partNumber) {
        this.groupId = groupId;
        this.groupName = groupName;
        this.partNumber = partNumber;
    }

    public String getEolName() {
        return eolName;
    }

    public void setEolName(String eolName) {
        this.eolName = eolName;
    }
    
    public Integer getGroupId() {
        return groupId;
    }
    
    public void setGroupId(Integer groupId) {
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
}
