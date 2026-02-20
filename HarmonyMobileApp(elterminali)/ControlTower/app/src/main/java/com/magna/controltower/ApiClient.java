package com.magna.controltower;

import android.content.Context;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.magna.controltower.api.ForkliftApiService;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeUnit;

import okhttp3.Interceptor;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import okhttp3.logging.HttpLoggingInterceptor;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

/**
 * API Client for Harmony Ecosystem
 * Provides both Retrofit service and legacy JSON methods for backward compatibility
 */
class ApiClient {
    private final OkHttpClient client;
    private final Context ctx;
    private final ForkliftApiService apiService;
    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");

    ApiClient(Context ctx){ 
        this.ctx = ctx.getApplicationContext();
        
        // Setup logging interceptor
        HttpLoggingInterceptor loggingInterceptor = new HttpLoggingInterceptor();
        loggingInterceptor.setLevel(HttpLoggingInterceptor.Level.BODY);
        
        // Setup auth interceptor
        Interceptor authInterceptor = new Interceptor() {
            @Override
            public Response intercept(Chain chain) throws IOException {
                Request original = chain.request();
                
                // Skip auth for login endpoint
                String url = original.url().toString();
                if (url.contains("/login")) {
                    return chain.proceed(original);
                }
                
                // Add auth header if not present and token exists
                if (original.header("Authorization") == null) {
                    String token = SessionManager.token(ctx);
                    if (token != null && !token.isEmpty()) {
                        Request.Builder builder = original.newBuilder()
                                .header("Authorization", "Bearer " + token);
                        return chain.proceed(builder.build());
                    }
                }
                
                return chain.proceed(original);
            }
        };
        
        this.client = new OkHttpClient.Builder()
                .connectTimeout(15, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .addInterceptor(authInterceptor)
                .addInterceptor(loggingInterceptor)
                .build();
        
        // Setup Retrofit
        String baseUrl = getBaseUrl();
        Gson gson = new GsonBuilder()
                .setLenient()
                .create();
        
        Retrofit retrofit = new Retrofit.Builder()
                .baseUrl(baseUrl)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create(gson))
                .build();
        
        this.apiService = retrofit.create(ForkliftApiService.class);
    }
    
    /**
     * Get Retrofit API service instance
     */
    public ForkliftApiService getService() {
        return apiService;
    }

    private String getBaseUrl() {
        String base = Prefs.getBaseUrl(ctx);
        if (!base.endsWith("/")) base = base + "/";
        if (!base.contains("/api")) base = base + "api/";
        return base;
    }

    private String url(String path){
        String base = Prefs.getBaseUrl(ctx);
        if (base.endsWith("/")) base = base.substring(0, base.length()-1);
        if (!path.startsWith("/")) path = "/" + path;
        return base + path;
    }

    private Request.Builder authBuilder(){
        Request.Builder builder = new Request.Builder();
        String token = SessionManager.token(ctx);
        if (token != null && !token.isEmpty()) {
            builder.addHeader("Authorization", "Bearer " + token);
        }
        return builder;
    }

    // ============ Legacy JSON methods (for backward compatibility) ============

    JSONObject postJson(String path, JSONObject body) throws Exception{
        Request req = new Request.Builder()
                .url(url(path))
                .post(RequestBody.create(body.toString().getBytes(StandardCharsets.UTF_8), JSON))
                .build();
        try(Response r = client.newCall(req).execute()){
            int code = r.code();
            String s = r.body()!=null ? r.body().string() : "";
            if (code>=200 && code<300) return new JSONObject(s);
            // Yetki başlığı gerekmiyor dendi; 400/401 özel davran
            JSONObject err = new JSONObject();
            err.put("http_code", code);
            err.put("body", s);
            return err; // çağıran taraf handle edecek
        }
    }

    JSONObject postJsonAuth(String path, JSONObject body) throws Exception{
        Request req = authBuilder()
                .url(url(path))
                .post(RequestBody.create(body.toString().getBytes(StandardCharsets.UTF_8), JSON))
                .build();
        try(Response r = client.newCall(req).execute()){
            int code = r.code();
            String s = r.body()!=null ? r.body().string() : "";
            
            if (code == 401) {
                JSONObject err = new JSONObject();
                err.put("http_code", 401);
                err.put("error", "Session expired");
                err.put("retryable", false);
                return err;
            }
            
            if (code>=200 && code<300) {
                return new JSONObject(s);
            }
            
            JSONObject err = new JSONObject();
            err.put("http_code", code);
            err.put("body", s);
            try {
                JSONObject responseJson = new JSONObject(s);
                if (responseJson.has("error")) {
                    err.put("error", responseJson.getString("error"));
                }
                if (responseJson.has("retryable")) {
                    err.put("retryable", responseJson.getBoolean("retryable"));
                }
            } catch (Exception ignored) {}
            return err;
        }
    }

    JSONArray getJsonArray(String path) throws Exception{
        Request req = authBuilder().url(url(path)).get().build();
        try(Response r = client.newCall(req).execute()){
            int code = r.code();
            String s = r.body()!=null ? r.body().string() : "";
            
            if (code == 401) {
                throw new RuntimeException("Session expired");
            }
            
            if (code>=200 && code<300) return new JSONArray(s);
            throw new RuntimeException("GET "+path+" failed: "+code+" "+s);
        }
    }

    JSONObject getJsonObject(String path) throws Exception{
        Request req = authBuilder().url(url(path)).get().build();
        try(Response r = client.newCall(req).execute()){
            int code = r.code();
            String s = r.body()!=null ? r.body().string() : "";
            
            if (code == 401) {
                throw new RuntimeException("Session expired");
            }
            
            if (code>=200 && code<300) return new JSONObject(s);
            throw new RuntimeException("GET "+path+" failed: "+code+" "+s);
        }
    }
}

