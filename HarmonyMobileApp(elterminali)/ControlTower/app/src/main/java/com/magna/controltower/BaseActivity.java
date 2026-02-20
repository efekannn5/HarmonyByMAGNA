package com.magna.controltower;

import android.app.admin.DevicePolicyManager;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Color;
import android.os.BatteryManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.OnBackPressedCallback;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.view.WindowInsetsControllerCompat;

import java.util.Locale;

/**
 * Base Activity - Tüm aktivitelerde ortak özellikler
 * - Status bar gizleme (saat, şarj, bildirimler)
 * - Navigation bar gizleme (geri, home, son uygulamalar)
 * - Tam ekran mod (immersive sticky)
 * - Bildirim paneli engelleme
 * - Sol alt köşede geri butonu
 * - Hardware geri tuşu engelleme
 * - Lock Task Mode (Device Owner gerekli)
 */
public abstract class BaseActivity extends AppCompatActivity {
    
    private long lastBackPressTime = 0;
    private static final long BACK_PRESS_INTERVAL = 2000; // 2 saniye
    private static final int SWIPE_THRESHOLD = 100; // Üstten kaç piksel kaydırma engellensin
    private static final long INACTIVITY_TIMEOUT_MS = 90L * 60L * 1000L; // 1.5 saat
    private View blockingOverlay;
    private DevicePolicyManager devicePolicyManager;
    private ComponentName adminComponent;
    private TextView batteryTextView;
    private BroadcastReceiver batteryReceiver;
    private boolean isBatteryReceiverRegistered = false;
    private final Handler inactivityHandler = new Handler(Looper.getMainLooper());
    private final Runnable inactivityRunnable = this::handleInactivityTimeout;
    private float topSwipeStartY = -1f;
    private boolean blockTopSwipe = false;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // Device Policy Manager'ı başlat
        devicePolicyManager = (DevicePolicyManager) getSystemService(Context.DEVICE_POLICY_SERVICE);
        adminComponent = new ComponentName(this, KioskModeReceiver.class);
        
        // Ekranı sürekli açık tut
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        
        // Geri tuşu kontrolü için yeni API kullan
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                handleBackPress();
            }
        });
    }
    
    @Override
    public void onContentChanged() {
        super.onContentChanged();
        // setContentView() çağrıldıktan sonra tam ekran modunu etkinleştir
        enableFullscreenMode();
        // Bildirim panelini engellemek için overlay ekle
        addNotificationBlocker();
        // Sol alt köşeye geri butonu ekle
        addBackButton();
        // Sağ üstte batarya yüzdesi göster
        addBatteryIndicator();
        // Lock task mode'u başlat (Device Owner modunda)
        startLockTaskMode();
    }
    
    @Override
    protected void onResume() {
        super.onResume();
        // Her resume'da tam ekran modunu yeniden uygula
        enableFullscreenMode();
        resetInactivityTimer();
    }

    @Override
    protected void onStart() {
        super.onStart();
        registerBatteryReceiver();
    }

    @Override
    protected void onStop() {
        super.onStop();
        unregisterBatteryReceiver();
        stopInactivityTimer();
    }
    
    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) {
            // Focus geri geldiğinde tam ekran modunu yeniden uygula
            enableFullscreenMode();
        }
    }
    
    /**
     * Tam ekran modu - Status bar ve Navigation bar'ı gizle
     * Hem yeni (API 30+) hem eski API'leri destekler
     */
    private void enableFullscreenMode() {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                // Android 11+ (API 30+) için yeni yöntem
                WindowInsetsController controller = getWindow().getInsetsController();
                if (controller != null) {
                    // Status bar ve navigation bar'ı gizle
                    controller.hide(WindowInsets.Type.statusBars() | WindowInsets.Type.navigationBars());
                    // Immersive sticky mode - kullanıcı kaydırsa bile geri gelir
                    controller.setSystemBarsBehavior(WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
                }
            } else {
                // Android 10 ve altı için eski yöntem
                WindowCompat.setDecorFitsSystemWindows(getWindow(), false);
                WindowInsetsControllerCompat controller = WindowCompat.getInsetsController(getWindow(), getWindow().getDecorView());
                if (controller != null) {
                    // Status bar ve navigation bar'ı gizle
                    controller.hide(WindowInsetsCompat.Type.statusBars() | WindowInsetsCompat.Type.navigationBars());
                    // Immersive sticky mode
                    controller.setSystemBarsBehavior(WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
                }
                
                // Ekstra güvenlik için eski flag'leri de ekle
                getWindow().getDecorView().setSystemUiVisibility(
                        View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                                | View.SYSTEM_UI_FLAG_FULLSCREEN
                                | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                                | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                                | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                                | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                );
            }
        } catch (Exception e) {
            // Hata olursa sessizce devam et
            e.printStackTrace();
        }
    }
    
    /**
     * Bildirim panelini engellemek için üst kısıma görünmez overlay ekle
     */
    private void addNotificationBlocker() {
        try {
            if (this instanceof GroupDetailActivity) {
                return;
            }
            ViewGroup rootView = findViewById(android.R.id.content);
            if (rootView != null && blockingOverlay == null) {
                blockingOverlay = new View(this);
                FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        SWIPE_THRESHOLD
                );
                blockingOverlay.setLayoutParams(params);
                blockingOverlay.setBackgroundColor(0x00000000); // Tamamen şeffaf
                
                // Touch event'leri yakala ve bildirim panelini engelle
                blockingOverlay.setOnTouchListener((v, event) -> {
                    // Tüm touch event'leri tüket (engelle)
                    return true;
                });
                
                rootView.addView(blockingOverlay);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    
    /**
     * Sol alt köşeye geri butonu ekle
     */
    private void addBackButton() {
        try {
            // Login ekranında geri butonu gösterme
            if (this instanceof AuthActivity) {
                return;
            }
            
            ViewGroup rootView = findViewById(android.R.id.content);
            if (rootView != null) {
                Button backButton = new Button(this);
                
                // Gruplar ekranında "Çıkış Yap", diğer ekranlarda "Geri"
                if (this instanceof GroupActivity) {
                    backButton.setText("◄ Çıkış Yap");
                } else {
                    backButton.setText("◄ Geri");
                }
                
                backButton.setTextColor(Color.WHITE);
                backButton.setBackgroundColor(0xCC000000); // Daha opak siyah
                backButton.setTextSize(14);
                backButton.setPadding(30, 15, 30, 15);
                backButton.setElevation(10f); // Yüksek elevation ile üstte kal
                
                FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(
                        ViewGroup.LayoutParams.WRAP_CONTENT,
                        ViewGroup.LayoutParams.WRAP_CONTENT
                );
                params.gravity = Gravity.BOTTOM | Gravity.START;
                params.setMargins(16, 0, 0, 16); // En alta yerleştir
                backButton.setLayoutParams(params);
                
                // Tıklama ile işlem yap
                backButton.setOnClickListener(v -> {
                    if (this instanceof GroupActivity) {
                        // Gruplar ekranında çıkış yaparken onay iste
                        new androidx.appcompat.app.AlertDialog.Builder(this)
                            .setTitle("Çıkış Yap")
                            .setMessage("Oturumu kapatmak istediğinize emin misiniz?")
                            .setPositiveButton("Evet", (dialog, which) -> {
                                // Logout yap
                                SessionManager.clear(this);
                                android.content.Intent intent = new android.content.Intent(this, AuthActivity.class);
                                intent.setFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK | android.content.Intent.FLAG_ACTIVITY_CLEAR_TASK);
                                startActivity(intent);
                                finish();
                            })
                            .setNegativeButton("Hayır", null)
                            .show();
                    } else {
                        // Diğer ekranlarda sadece geri git
                        finish();
                    }
                });
                
                rootView.addView(backButton);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * Sağ altta küçük batarya yüzdesi göstergesi ekle
     */
    private void addBatteryIndicator() {
        try {
            ViewGroup rootView = findViewById(android.R.id.content);
            if (rootView != null && batteryTextView == null) {
                batteryTextView = new TextView(this);
                batteryTextView.setTextColor(Color.WHITE);
                batteryTextView.setBackgroundColor(0x80000000); // Yarı şeffaf siyah
                batteryTextView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12);
                int padH = dpToPx(8);
                int padV = dpToPx(4);
                batteryTextView.setPadding(padH, padV, padH, padV);
                batteryTextView.setText("BAT --%");

                FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(
                        ViewGroup.LayoutParams.WRAP_CONTENT,
                        ViewGroup.LayoutParams.WRAP_CONTENT
                );
                params.gravity = Gravity.BOTTOM | Gravity.END;
                params.setMargins(0, 0, dpToPx(8), dpToPx(8));
                batteryTextView.setLayoutParams(params);

                rootView.addView(batteryTextView);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void registerBatteryReceiver() {
        if (isBatteryReceiverRegistered) {
            return;
        }
        if (batteryReceiver == null) {
            batteryReceiver = new BroadcastReceiver() {
                @Override
                public void onReceive(Context context, Intent intent) {
                    int level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
                    int scale = intent.getIntExtra(BatteryManager.EXTRA_SCALE, 100);
                    updateBatteryText(level, scale);
                }
            };
        }
        try {
            IntentFilter filter = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);
            registerReceiver(batteryReceiver, filter);
            isBatteryReceiverRegistered = true;
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void unregisterBatteryReceiver() {
        if (!isBatteryReceiverRegistered || batteryReceiver == null) {
            return;
        }
        try {
            unregisterReceiver(batteryReceiver);
        } catch (Exception e) {
            // No-op
        } finally {
            isBatteryReceiverRegistered = false;
        }
    }

    private void updateBatteryText(int level, int scale) {
        if (batteryTextView == null || level < 0 || scale <= 0) {
            return;
        }
        int percent = Math.round((level * 100f) / scale);
        batteryTextView.setText(String.format(Locale.US, "BAT %d%%", percent));
    }

    private int dpToPx(int dp) {
        return Math.round(dp * getResources().getDisplayMetrics().density);
    }
    
    /**
     * Ekran touch event'lerini yakala ve üstten kaydırmayı engelle
     */
    @Override
    public boolean dispatchTouchEvent(MotionEvent event) {
        int action = event.getActionMasked();
        if (action == MotionEvent.ACTION_DOWN) {
            topSwipeStartY = event.getY();
            blockTopSwipe = topSwipeStartY < SWIPE_THRESHOLD;
            return super.dispatchTouchEvent(event);
        }
        if (action == MotionEvent.ACTION_MOVE && blockTopSwipe) {
            float dy = event.getY() - topSwipeStartY;
            if (dy > dpToPx(12)) {
                return true;
            }
        }
        if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
            blockTopSwipe = false;
            topSwipeStartY = -1f;
        }
        return super.dispatchTouchEvent(event);
    }

    @Override
    public void onUserInteraction() {
        super.onUserInteraction();
        resetInactivityTimer();
    }
    
    /**
     * Geri tuşu kontrolü - Tüm ekranlarda engellendi
     */
    private void handleBackPress() {
        // Tüm ekranlarda geri tuşunu engelle
        Toast.makeText(this, "Sol alttaki geri butonunu kullanın", Toast.LENGTH_SHORT).show();
    }

    private void resetInactivityTimer() {
        if (this instanceof AuthActivity) {
            return;
        }
        inactivityHandler.removeCallbacks(inactivityRunnable);
        inactivityHandler.postDelayed(inactivityRunnable, INACTIVITY_TIMEOUT_MS);
    }

    private void stopInactivityTimer() {
        inactivityHandler.removeCallbacks(inactivityRunnable);
    }

    private void handleInactivityTimeout() {
        if (this instanceof AuthActivity || isFinishing()) {
            return;
        }
        SessionManager.clear(this);
        Intent intent = new Intent(this, AuthActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }
    
    /**
     * Alt sınıflar bu metodu override ederek geri tuşuna izin verebilir
     * @return true ise geri tuşuna izin verilir, false ise engellenir
     */
    protected boolean shouldAllowBackPress() {
        return false; // Varsayılan: geri tuşu engellendi
    }
    
    /**
     * Lock Task Mode - Device Owner modunda uygulamayı kilitle
     * Kullanıcı uygulamadan çıkamaz, home tuşu çalışmaz
     */
    private void startLockTaskMode() {
        try {
            if (devicePolicyManager != null && devicePolicyManager.isDeviceOwnerApp(getPackageName())) {
                // Bu uygulamayı lock task mode için whitelist'e ekle
                devicePolicyManager.setLockTaskPackages(adminComponent, new String[]{getPackageName()});
                
                // Lock task mode'u başlat
                startLockTask();
                
                // Status bar'ı tamamen devre dışı bırak
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                    devicePolicyManager.setStatusBarDisabled(adminComponent, true);
                }
            }
        } catch (Exception e) {
            // Device Owner değilse veya hata olursa sessizce devam et
            e.printStackTrace();
        }
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        stopInactivityTimer();
        // Activity kapanırken lock task mode'dan çıkma (çıkmaya izin verme)
        // stopLockTask(); - BUNU YAPMA!
    }
}
