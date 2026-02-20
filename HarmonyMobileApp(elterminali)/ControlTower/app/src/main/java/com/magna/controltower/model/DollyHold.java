package com.magna.controltower.model;

import org.json.JSONException;
import org.json.JSONObject;

public class DollyHold {
    private int id;
    private String dollyNo;
    private String vinNo;
    private int scanOrder;
    private String customerReferans;
    private String eolName;
    private String status;
    private String scannedAt;

    public DollyHold() {}

    public static DollyHold fromJson(JSONObject json) throws JSONException {
        DollyHold dolly = new DollyHold();
        dolly.id = json.optInt("id", 0);
        dolly.dollyNo = json.optString("dollyNo", "");
        dolly.vinNo = json.optString("vinNo", "");
        dolly.scanOrder = json.optInt("scanOrder", 0);
        dolly.customerReferans = json.optString("customerReferans", "");
        dolly.eolName = json.optString("eolName", "");
        dolly.status = json.optString("status", "");
        dolly.scannedAt = json.optString("scannedAt", null);
        return dolly;
    }

    // Getters and setters
    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public String getDollyNo() { return dollyNo; }
    public void setDollyNo(String dollyNo) { this.dollyNo = dollyNo; }

    public String getVinNo() { return vinNo; }
    public void setVinNo(String vinNo) { this.vinNo = vinNo; }

    public int getScanOrder() { return scanOrder; }
    public void setScanOrder(int scanOrder) { this.scanOrder = scanOrder; }

    public String getCustomerReferans() { return customerReferans; }
    public void setCustomerReferans(String customerReferans) { this.customerReferans = customerReferans; }

    public String getEolName() { return eolName; }
    public void setEolName(String eolName) { this.eolName = eolName; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getScannedAt() { return scannedAt; }
    public void setScannedAt(String scannedAt) { this.scannedAt = scannedAt; }
}
