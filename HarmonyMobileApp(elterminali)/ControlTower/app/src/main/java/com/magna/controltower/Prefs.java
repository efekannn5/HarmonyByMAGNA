package com.magna.controltower;

import android.content.Context;
import android.content.SharedPreferences;

public class Prefs {
    private static final String FILE = "ct_prefs";
    private static final String KEY_BASE_URL = "base_url";

    public static String getBaseUrl(Context c) {
        SharedPreferences sp = c.getSharedPreferences(FILE, Context.MODE_PRIVATE);
        // Updated to Harmony Ecosystem API server
        return sp.getString(KEY_BASE_URL, "http://10.25.64.181:8181");
    }
    public static void setBaseUrl(Context c, String url) {
        c.getSharedPreferences(FILE, Context.MODE_PRIVATE)
                .edit().putString(KEY_BASE_URL, url.trim()).apply();
    }
}
