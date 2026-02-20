package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;
import java.util.List;

/**
 * Response for EOL dollys in a group
 * GET /api/manual-collection/groups/{groupId}/eols/{eolId}
 */
public class EOLDollysResponse {
    @SerializedName("group_id")
    private int groupId;
    
    @SerializedName("group_name")
    private String groupName;
    
    @SerializedName("eol_id")
    private int eolId;
    
    @SerializedName("eol_name")
    private String eolName;
    
    @SerializedName("part_number")
    private String partNumber;
    
    @SerializedName("dollys")
    private List<GroupDolly> dollys;

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

    public String getPartNumber() {
        return partNumber;
    }

    public void setPartNumber(String partNumber) {
        this.partNumber = partNumber;
    }

    public List<GroupDolly> getDollys() {
        return dollys;
    }

    public void setDollys(List<GroupDolly> dollys) {
        this.dollys = dollys;
    }
}
