package com.magna.controltower.model;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

public class LoadingSession {
    private String loadingSessionId;
    private String status; // "scanned", "loading_completed", "completed"
    private String forkliftUser;
    private int dollyCount;
    private String firstScanAt;
    private String completedAt;
    private List<DollyHold> dollys;

    public LoadingSession() {
        this.dollys = new ArrayList<>();
    }

    public static LoadingSession fromJson(JSONObject json) throws JSONException {
        LoadingSession session = new LoadingSession();
        session.loadingSessionId = json.optString("loadingSessionId", "");
        session.status = json.optString("status", "");
        session.forkliftUser = json.optString("forkliftUser", "");
        session.dollyCount = json.optInt("dollyCount", 0);
        session.firstScanAt = json.optString("firstScanAt", null);
        session.completedAt = json.optString("completedAt", null);

        if (json.has("dollys")) {
            JSONArray dollysArray = json.getJSONArray("dollys");
            for (int i = 0; i < dollysArray.length(); i++) {
                session.dollys.add(DollyHold.fromJson(dollysArray.getJSONObject(i)));
            }
        }

        return session;
    }

    public static List<LoadingSession> fromJsonArray(JSONArray array) throws JSONException {
        List<LoadingSession> sessions = new ArrayList<>();
        for (int i = 0; i < array.length(); i++) {
            sessions.add(fromJson(array.getJSONObject(i)));
        }
        return sessions;
    }

    // Getters and setters
    public String getLoadingSessionId() { return loadingSessionId; }
    public void setLoadingSessionId(String loadingSessionId) { this.loadingSessionId = loadingSessionId; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getForkliftUser() { return forkliftUser; }
    public void setForkliftUser(String forkliftUser) { this.forkliftUser = forkliftUser; }

    public int getDollyCount() { return dollyCount; }
    public void setDollyCount(int dollyCount) { this.dollyCount = dollyCount; }

    public String getFirstScanAt() { return firstScanAt; }
    public void setFirstScanAt(String firstScanAt) { this.firstScanAt = firstScanAt; }

    public String getCompletedAt() { return completedAt; }
    public void setCompletedAt(String completedAt) { this.completedAt = completedAt; }

    public List<DollyHold> getDollys() { return dollys; }
    public void setDollys(List<DollyHold> dollys) { this.dollys = dollys; }
}
