package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;

/**
 * Dolly dolma durumu - EOL grup bilgisi
 * GET /api/yuzde
 */
public class EOLGroupStatus {
    @SerializedName("eol_name")
    private String eolName;
    
    @SerializedName("current_dolly")
    private int currentDolly;
    
    @SerializedName("current_vin_count")
    private int currentVinCount;
    
    @SerializedName("max_vin_capacity")
    private int maxVinCapacity;
    
    @SerializedName("vin_display")
    private String vinDisplay;
    
    @SerializedName("pending_dollys")
    private int pendingDollys;
    
    @SerializedName("total_dollys_scanned")
    private int totalDollysScanned;
    
    @SerializedName("remaining_vins")
    private int remainingVins;
    
    @SerializedName("status")
    private String status;
    
    @SerializedName("message")
    private String message;
    
    @SerializedName("last_vin")
    private String lastVin;
    
    @SerializedName("last_insert_time")
    private String lastInsertTime;
    
    @SerializedName("can_scan")
    private boolean canScan;

    // Getters and Setters
    public String getEolName() { return eolName; }
    public void setEolName(String eolName) { this.eolName = eolName; }

    public int getCurrentDolly() { return currentDolly; }
    public void setCurrentDolly(int currentDolly) { this.currentDolly = currentDolly; }

    public int getCurrentVinCount() { return currentVinCount; }
    public void setCurrentVinCount(int currentVinCount) { this.currentVinCount = currentVinCount; }

    public int getMaxVinCapacity() { return maxVinCapacity; }
    public void setMaxVinCapacity(int maxVinCapacity) { this.maxVinCapacity = maxVinCapacity; }

    public String getVinDisplay() { return vinDisplay; }
    public void setVinDisplay(String vinDisplay) { this.vinDisplay = vinDisplay; }

    public int getPendingDollys() { return pendingDollys; }
    public void setPendingDollys(int pendingDollys) { this.pendingDollys = pendingDollys; }

    public int getTotalDollysScanned() { return totalDollysScanned; }
    public void setTotalDollysScanned(int totalDollysScanned) { this.totalDollysScanned = totalDollysScanned; }

    public int getRemainingVins() { return remainingVins; }
    public void setRemainingVins(int remainingVins) { this.remainingVins = remainingVins; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }

    public String getLastVin() { return lastVin; }
    public void setLastVin(String lastVin) { this.lastVin = lastVin; }

    public String getLastInsertTime() { return lastInsertTime; }
    public void setLastInsertTime(String lastInsertTime) { this.lastInsertTime = lastInsertTime; }

    public boolean isCanScan() { return canScan; }
    public void setCanScan(boolean canScan) { this.canScan = canScan; }
}
