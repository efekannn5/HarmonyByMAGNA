package com.magna.controltower.model;

import java.util.List;

public class KasaItem {
    public enum Status { PENDING, SCANNED, SKIPPED }

    private final String kasaNo;
    private final String dollyOrderNo;
    private final String firstVin;
    private final String lastVin;
    private final List<String> vinList;
    private Status status = Status.PENDING;
    private boolean expanded = false;

    public KasaItem(String kasaNo, String dollyOrderNo, String firstVin, String lastVin, List<String> vinList) {
        this.kasaNo = kasaNo;
        this.dollyOrderNo = dollyOrderNo;
        this.firstVin = firstVin;
        this.lastVin = lastVin;
        this.vinList = vinList;
    }

    public String getKasaNo() { return kasaNo; }
    public String getDollyOrderNo() { return dollyOrderNo; }
    public String getFirstVin() { return firstVin; }
    public String getLastVin() { return lastVin; }
    public List<String> getVinList() { return vinList; }

    public Status getStatus() { return status; }
    public void setStatus(Status s) { status = s; }

    public boolean isExpanded() { return expanded; }
    public void setExpanded(boolean e) { expanded = e; }
}
