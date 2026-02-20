package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;
import java.util.List;

/**
 * Response containing all EOLs and their dollys in a group
 * GET /api/manual-collection/groups/{groupId}
 */
public class GroupDollysResponse {
    @SerializedName("group_id")
    private int groupId;
    
    @SerializedName("group_name")
    private String groupName;
    
    @SerializedName("part_number")
    private String partNumber;
    
    @SerializedName("eols")
    private List<EolGroup> eols;

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

    public List<EolGroup> getEols() {
        return eols;
    }

    public void setEols(List<EolGroup> eols) {
        this.eols = eols;
    }

    /**
     * Inner class representing an EOL within the group
     */
    public static class EolGroup {
        @SerializedName("eol_id")
        private int eolId;
        
        @SerializedName("eol_name")
        private String eolName;
        
        @SerializedName("dollys")
        private List<GroupDolly> dollys;

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

        public List<GroupDolly> getDollys() {
            return dollys;
        }

        public void setDollys(List<GroupDolly> dollys) {
            this.dollys = dollys;
        }
    }
}
