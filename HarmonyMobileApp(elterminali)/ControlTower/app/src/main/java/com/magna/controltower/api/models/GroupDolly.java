package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;

/**
 * Dolly information within a group
 * Part of GroupDollysResponse
 */
public class GroupDolly {
    @SerializedName("dolly_no")
    private String dollyNo;
    
    @SerializedName("dolly_order_no")
    private String dollyOrderNo;
    
    @SerializedName("vin_no")
    private String vinNo;
    
    // Backend'den hem "scanned" hem "is_scanned" gelebiliyor
    // Gson otomatik olarak hangisi gelirse onu kullanacak
    @SerializedName(value = "is_scanned", alternate = {"scanned"})
    private boolean scanned;

    public String getDollyNo() {
        return dollyNo;
    }

    public void setDollyNo(String dollyNo) {
        this.dollyNo = dollyNo;
    }

    public String getDollyOrderNo() {
        return dollyOrderNo;
    }

    public void setDollyOrderNo(String dollyOrderNo) {
        this.dollyOrderNo = dollyOrderNo;
    }

    public String getVinNo() {
        return vinNo;
    }

    public void setVinNo(String vinNo) {
        this.vinNo = vinNo;
    }

    public boolean isScanned() {
        return scanned;
    }

    public void setScanned(boolean scanned) {
        this.scanned = scanned;
    }
}
