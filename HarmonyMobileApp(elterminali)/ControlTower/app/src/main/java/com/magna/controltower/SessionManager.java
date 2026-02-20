package com.magna.controltower;

import android.content.Context;
import android.content.SharedPreferences;

public class SessionManager {
    private static final String FILE = "ct_session";
    private static final String K_TOKEN = "token";
    private static final String K_EXPIRES_AT = "expires_at";
    private static final String K_ROLE = "role";
    private static final String K_DISPLAY = "display_name";
    private static final String K_USERNAME = "username";
    private static final String K_BARCODE = "operator_barcode";

    public static void save(Context c, String token, long expiresIn, String role, String display, String username) {
        save(c, token, expiresIn, role, display, username, null);
    }

    public static void save(Context c, String token, long expiresIn, String role, String display, String username, String barcode) {
        // expiresIn is in seconds, convert to milliseconds and add to current time
        long expiresAtMillis = System.currentTimeMillis() + (expiresIn * 1000);
        
        SharedPreferences.Editor editor = c.getSharedPreferences(FILE, Context.MODE_PRIVATE).edit()
                .putString(K_TOKEN, token)
                .putLong(K_EXPIRES_AT, expiresAtMillis)
                .putString(K_ROLE, role)
                .putString(K_DISPLAY, display)
                .putString(K_USERNAME, username);
        
        if (barcode != null) {
            editor.putString(K_BARCODE, barcode);
        }
        
        editor.apply();
    }

    public static boolean isValid(Context c) {
        SharedPreferences sp = c.getSharedPreferences(FILE, Context.MODE_PRIVATE);
        String token = sp.getString(K_TOKEN, "");
        long expiresAt = sp.getLong(K_EXPIRES_AT, 0);
        
        if (token.isEmpty()) return false;
        if (expiresAt == 0) return false;
        
        // Check if token is expired
        return System.currentTimeMillis() < expiresAt;
    }

    public static String role(Context c){ return c.getSharedPreferences(FILE, Context.MODE_PRIVATE).getString(K_ROLE, ""); }
    public static String display(Context c){ return c.getSharedPreferences(FILE, Context.MODE_PRIVATE).getString(K_DISPLAY, ""); }
    public static String token(Context c){ return c.getSharedPreferences(FILE, Context.MODE_PRIVATE).getString(K_TOKEN, ""); }
    public static String username(Context c){ return c.getSharedPreferences(FILE, Context.MODE_PRIVATE).getString(K_USERNAME, ""); }
    public static String getUserBarcode(Context c){ return c.getSharedPreferences(FILE, Context.MODE_PRIVATE).getString(K_BARCODE, ""); }
    public static long expiresAt(Context c){ return c.getSharedPreferences(FILE, Context.MODE_PRIVATE).getLong(K_EXPIRES_AT, 0); }
    
    public static boolean isAdmin(Context c) {
        String role = role(c);
        return role != null && (role.equalsIgnoreCase("admin") || role.equalsIgnoreCase("administrator"));
    }

    public static void clear(Context c){
        TelemetryService.stop(c);
        c.getSharedPreferences(FILE, Context.MODE_PRIVATE).edit().clear().apply();
    }
}
