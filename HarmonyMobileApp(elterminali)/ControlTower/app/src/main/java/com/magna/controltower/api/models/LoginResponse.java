package com.magna.controltower.api.models;

import com.google.gson.annotations.SerializedName;

/**
 * Login response model from Harmony Ecosystem API
 * POST /api/forklift/login
 */
public class LoginResponse {
    @SerializedName("success")
    private boolean success;
    
    @SerializedName("sessionToken")
    private String sessionToken;
    
    @SerializedName("operatorName")
    private String operatorName;
    
    @SerializedName("expiresAt")
    private String expiresAt;
    
    @SerializedName("message")
    private String message;
    
    @SerializedName("isAdmin")
    private boolean isAdmin;
    
    @SerializedName("role")
    private String role;

    public boolean isSuccess() {
        return success;
    }

    public void setSuccess(boolean success) {
        this.success = success;
    }

    public String getSessionToken() {
        return sessionToken;
    }

    public void setSessionToken(String sessionToken) {
        this.sessionToken = sessionToken;
    }

    public String getOperatorName() {
        return operatorName;
    }

    public void setOperatorName(String operatorName) {
        this.operatorName = operatorName;
    }

    public String getExpiresAt() {
        return expiresAt;
    }

    public void setExpiresAt(String expiresAt) {
        this.expiresAt = expiresAt;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }
    
    public boolean isAdmin() {
        return isAdmin;
    }
    
    public void setAdmin(boolean admin) {
        isAdmin = admin;
    }
    
    public String getRole() {
        return role;
    }
    
    public void setRole(String role) {
        this.role = role;
    }
}
