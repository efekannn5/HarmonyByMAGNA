package com.magna.controltower;

import android.content.Intent;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.KeyEvent;
import android.view.WindowManager;
import android.view.inputmethod.InputMethodManager;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.core.view.WindowCompat;

import com.magna.controltower.api.models.LoginRequest;
import com.magna.controltower.api.models.LoginResponse;

import org.json.JSONObject;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class AuthActivity extends BaseActivity {
    private static final int REQ_LOCATION_PERMS = 701;
    private boolean pendingNavigate = false;
    private boolean pendingIsAdmin = false;
    private String pendingUserRole = "";
    private String pendingOperatorName = "";

    // ==================== TEMP_DEBUG: BYPASS CODE - SİL BUNU! ====================
    // Bu bypass özelliğini production'a çıkmadan önce SİL!
    // Bypass kodunu buradan değiştir:
    private static final String BYPASS_CODE = "JkE4Ttgog6R3vpir";
    // ============================================================================

    private EditText etHidden;
    private TextView tvWarn;
    private final Handler keyboardHandler = new Handler(Looper.getMainLooper());
    private final Runnable showKeyboardRunnable = this::showScannerKeyboardNow;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_auth);

        ImageView logo = findViewById(R.id.imgLogo);
        logo.setColorFilter(Color.WHITE);
        tvWarn = findViewById(R.id.tvWarnAuth);
        etHidden = findViewById(R.id.etHidden);

        etHidden.requestFocus();
        try {
            etHidden.setShowSoftInputOnFocus(false);
        } catch (Exception ignored) {
        }
        InputMethodManager imm = (InputMethodManager) getSystemService(INPUT_METHOD_SERVICE);
        if (imm != null)
            imm.hideSoftInputFromWindow(etHidden.getWindowToken(), 0);
        etHidden.setOnTouchListener((v, e) -> true);

        etHidden.setOnKeyListener((v, keyCode, event) -> {
            if (event.getAction() == KeyEvent.ACTION_DOWN && keyCode == KeyEvent.KEYCODE_ENTER) {
                String raw = etHidden.getText().toString();
                etHidden.getText().clear();
                doLogin(raw);
                showScannerKeyboardDelayed(150);
                return true;
            }
            return false;
        });

        etHidden.addTextChangedListener(new TextWatcher() {
            int last = 0;

            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {
            }

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
            }

            @Override
            public void afterTextChanged(Editable s) {
                if (s.length() > last) {
                    char c = s.charAt(s.length() - 1);
                    if (c == '\n' || c == '\r') {
                        String raw = s.toString();
                        etHidden.getText().clear();
                        doLogin(raw);
                        showScannerKeyboardDelayed(150);
                    }
                }
                last = s.length();
            }
        });
/*
        // ==================== TEMP_DEBUG: BYPASS BUTTON - SİL BUNU!
        // ====================
        // Production'a çıkmadan bu butonu ve listener'ı SİL!
        findViewById(R.id.btnBypass).setOnClickListener(v -> {
            tvWarn.setText("Bypass giriş yapılıyor...");
            doLogin(BYPASS_CODE);
        });
        // ============================================================================

*/

    }

    private void doLogin(String raw) {
        String barcode = sanitize(raw);
        if (barcode.isEmpty()) {
            tvWarn.setText("Boş barkod. Lütfen tekrar okutun.");
            return;
        }
        tvWarn.setText("Doğrulanıyor…");

        // Use Retrofit API
        ApiClient apiClient = new ApiClient(this);
        LoginRequest request = new LoginRequest(barcode, android.os.Build.MODEL);

        apiClient.getService().login(request).enqueue(new Callback<LoginResponse>() {
            @Override
            public void onResponse(Call<LoginResponse> call, Response<LoginResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    LoginResponse loginResponse = response.body();

                    if (!loginResponse.isSuccess()) {
                        tvWarn.setText("Giriş başarısız.");
                        return;
                    }

                    String token = loginResponse.getSessionToken();
                    String operatorName = loginResponse.getOperatorName();
                    boolean isAdmin = loginResponse.isAdmin();
                    String role = loginResponse.getRole();

                    if (token == null || token.isEmpty()) {
                        tvWarn.setText("Token alınamadı.");
                        return;
                    }

                    // Token 8 saat geçerli (28800 saniye)
                    long expiresIn = 28800;
                    
                    // Determine role: admin veya forklift
                    String userRole = "forklift"; // Default
                    if (isAdmin) {
                        userRole = "admin";
                    } else if (role != null && !role.isEmpty()) {
                        userRole = role;
                    }

                    // Lambda için final değişkenler
                    final boolean finalIsAdmin = isAdmin;
                    final String finalUserRole = userRole;

                    // Save session
                    SessionManager.save(
                            AuthActivity.this,
                            token,
                            expiresIn,
                            userRole,
                            operatorName != null ? operatorName : barcode,
                            barcode);

                    tvWarn.setText("Hoş geldin " + operatorName);

                    pendingNavigate = true;
                    pendingIsAdmin = finalIsAdmin;
                    pendingUserRole = finalUserRole;
                    pendingOperatorName = operatorName != null ? operatorName : barcode;
                    ensureLocationPermissionsThenContinue();

                } else {
                    // Handle error response
                    int code = response.code();
                    if (code == 400) {
                        tvWarn.setText("Boş/Geçersiz barkod. Tekrar okutun.");
                    } else if (code == 401) {
                        tvWarn.setText("Tanınmayan barkod. Lütfen yeni barkod okutun.");
                    } else {
                        tvWarn.setText("Sunucu hatası: " + code);
                    }
                }
            }

            @Override
            public void onFailure(Call<LoginResponse> call, Throwable t) {
                tvWarn.setText("Bağlantı hatası: " + t.getMessage());
            }
        });
    }

    private void ensureLocationPermissionsThenContinue() {
        if (!pendingNavigate) return;
        if (hasLocationPermissions()) {
            TelemetryService.start(AuthActivity.this);
            proceedAfterLogin();
            return;
        }

        if (shouldShowLocationRationale()) {
            new androidx.appcompat.app.AlertDialog.Builder(this)
                    .setTitle("Konum İzni Gerekli")
                    .setMessage("Forklift konumu ve hareket takibi için arkaplanda konum izni gerekiyor.")
                    .setPositiveButton("İzin Ver", (d, w) -> requestLocationPermissions())
                    .setNegativeButton("Şimdi Değil", (d, w) -> {
                        TelemetryService.start(AuthActivity.this);
                        proceedAfterLogin();
                    })
                    .show();
        } else {
            requestLocationPermissions();
        }
    }

    private boolean hasLocationPermissions() {
        boolean fine = ContextCompat.checkSelfPermission(this, android.Manifest.permission.ACCESS_FINE_LOCATION)
                == android.content.pm.PackageManager.PERMISSION_GRANTED;
        boolean coarse = ContextCompat.checkSelfPermission(this, android.Manifest.permission.ACCESS_COARSE_LOCATION)
                == android.content.pm.PackageManager.PERMISSION_GRANTED;
        boolean base = fine || coarse;
        if (!base) return false;
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.Q) {
            return ContextCompat.checkSelfPermission(this, android.Manifest.permission.ACCESS_BACKGROUND_LOCATION)
                    == android.content.pm.PackageManager.PERMISSION_GRANTED;
        }
        return true;
    }

    private boolean shouldShowLocationRationale() {
        boolean fine = ActivityCompat.shouldShowRequestPermissionRationale(this, android.Manifest.permission.ACCESS_FINE_LOCATION);
        boolean coarse = ActivityCompat.shouldShowRequestPermissionRationale(this, android.Manifest.permission.ACCESS_COARSE_LOCATION);
        boolean bg = false;
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.Q) {
            bg = ActivityCompat.shouldShowRequestPermissionRationale(this, android.Manifest.permission.ACCESS_BACKGROUND_LOCATION);
        }
        return fine || coarse || bg;
    }

    private void requestLocationPermissions() {
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.Q) {
            ActivityCompat.requestPermissions(
                    this,
                    new String[] {
                            android.Manifest.permission.ACCESS_FINE_LOCATION,
                            android.Manifest.permission.ACCESS_COARSE_LOCATION,
                            android.Manifest.permission.ACCESS_BACKGROUND_LOCATION
                    },
                    REQ_LOCATION_PERMS
            );
        } else {
            ActivityCompat.requestPermissions(
                    this,
                    new String[] {
                            android.Manifest.permission.ACCESS_FINE_LOCATION,
                            android.Manifest.permission.ACCESS_COARSE_LOCATION
                    },
                    REQ_LOCATION_PERMS
            );
        }
    }

    private void proceedAfterLogin() {
        if (!pendingNavigate) return;
        pendingNavigate = false;
        new android.os.Handler().postDelayed(() -> {
            Intent i;
            if (pendingIsAdmin || "admin".equalsIgnoreCase(pendingUserRole)) {
                i = new Intent(AuthActivity.this, SettingsActivity.class);
            } else {
                i = new Intent(AuthActivity.this, GroupActivity.class);
            }
            startActivity(i);
            finish();
        }, 1000);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQ_LOCATION_PERMS) {
            TelemetryService.start(AuthActivity.this);
            proceedAfterLogin();
        }
    }

    private String sanitize(String s) {
        if (s == null)
            return "";
        return s.replaceAll("[\\r\\n\\t\\u0000-\\u001F]", "").trim();
    }

    @Override
    protected void onResume() {
        super.onResume();
        etHidden.requestFocus();
        showScannerKeyboardDelayed(150);
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) {
            showScannerKeyboardDelayed(150);
        }
    }

    private void showScannerKeyboardDelayed(int delayMs) {
        keyboardHandler.removeCallbacks(showKeyboardRunnable);
        keyboardHandler.postDelayed(showKeyboardRunnable, delayMs);
    }

    private void showScannerKeyboardNow() {
        if (etHidden == null) {
            return;
        }
        etHidden.requestFocus();
        etHidden.setSelection(etHidden.getText().length());
        InputMethodManager imm = (InputMethodManager) getSystemService(INPUT_METHOD_SERVICE);
        if (imm != null) {
            imm.showSoftInput(etHidden, InputMethodManager.SHOW_IMPLICIT);
        }
    }
}
