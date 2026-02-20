package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;

/**
 * Dolly Hold Entry response from API
 * Contains information about a scanned dolly
 */
public class DollyHoldEntry {
    @SerializedName("id")
    private Integer id;
    
    @SerializedName("dolly_no")
    private String dollyNo;
    
    @SerializedName("vin_no")
    private String vinNo;
    
    @SerializedName("status")
    private String status;
    
    @SerializedName("loading_session_id")
    private String loadingSessionId;
    
    @SerializedName("scan_order")
    private Integer scanOrder;
    
    @SerializedName("scanned_at")
    private String scannedAt;
    
    @SerializedName("eol_name")
    private String eolName;
    
    @SerializedName("customer_referans")
    private String customerReferans;
    
    @SerializedName("adet")
    private Integer adet;
    
    @SerializedName("eol_dolly_barcode")
    private String eolDollyBarcode;

    // Getters and Setters
    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public String getDollyNo() {
        return dollyNo;
    }

    public void setDollyNo(String dollyNo) {
        this.dollyNo = dollyNo;
    }

    public String getVinNo() {
        return vinNo;
    }

    public void setVinNo(String vinNo) {
        this.vinNo = vinNo;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getLoadingSessionId() {
        return loadingSessionId;
    }

    public void setLoadingSessionId(String loadingSessionId) {
        this.loadingSessionId = loadingSessionId;
    }

    public Integer getScanOrder() {
        return scanOrder;
    }

    public void setScanOrder(Integer scanOrder) {
        this.scanOrder = scanOrder;
    }

    public String getScannedAt() {
        return scannedAt;
    }

    public void setScannedAt(String scannedAt) {
        this.scannedAt = scannedAt;
    }

    public String getEolName() {
        return eolName;
    }

    public void setEolName(String eolName) {
        this.eolName = eolName;
    }

    public String getCustomerReferans() {
        return customerReferans;
    }

    public void setCustomerReferans(String customerReferans) {
        this.customerReferans = customerReferans;
    }

    public Integer getAdet() {
        return adet;
    }

    public void setAdet(Integer adet) {
        this.adet = adet;
    }

    public String getEolDollyBarcode() {
        return eolDollyBarcode;
    }

    public void setEolDollyBarcode(String eolDollyBarcode) {
        this.eolDollyBarcode = eolDollyBarcode;
    }
}
