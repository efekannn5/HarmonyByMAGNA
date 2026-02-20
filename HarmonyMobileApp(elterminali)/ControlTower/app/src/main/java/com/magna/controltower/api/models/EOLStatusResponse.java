package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;
import java.util.List;

/**
 * Dolly dolma durumu response
 * GET /api/yuzde
 */
public class EOLStatusResponse {
    @SerializedName("success")
    private boolean success;
    
    @SerializedName("timestamp")
    private String timestamp;
    
    @SerializedName("eol_groups")
    private List<EOLGroupStatus> eolGroups;
    
    @SerializedName("summary")
    private Summary summary;

    public static class Summary {
        @SerializedName("total_active_dollys")
        private int totalActiveDollys;
        
        @SerializedName("filling_dollys")
        private int fillingDollys;
        
        @SerializedName("full_dollys")
        private int fullDollys;
        
        @SerializedName("empty_dollys")
        private int emptyDollys;

        public int getTotalActiveDollys() { return totalActiveDollys; }
        public void setTotalActiveDollys(int totalActiveDollys) { this.totalActiveDollys = totalActiveDollys; }

        public int getFillingDollys() { return fillingDollys; }
        public void setFillingDollys(int fillingDollys) { this.fillingDollys = fillingDollys; }

        public int getFullDollys() { return fullDollys; }
        public void setFullDollys(int fullDollys) { this.fullDollys = fullDollys; }

        public int getEmptyDollys() { return emptyDollys; }
        public void setEmptyDollys(int emptyDollys) { this.emptyDollys = emptyDollys; }
    }

    // Getters and Setters
    public boolean isSuccess() { return success; }
    public void setSuccess(boolean success) { this.success = success; }

    public String getTimestamp() { return timestamp; }
    public void setTimestamp(String timestamp) { this.timestamp = timestamp; }

    public List<EOLGroupStatus> getEolGroups() { return eolGroups; }
    public void setEolGroups(List<EOLGroupStatus> eolGroups) { this.eolGroups = eolGroups; }

    public Summary getSummary() { return summary; }
    public void setSummary(Summary summary) { this.summary = summary; }
}
