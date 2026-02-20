package com.magna.controltower;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.KeyEvent;
import android.view.LayoutInflater;
import android.view.View;
import android.view.inputmethod.InputMethodManager;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import com.magna.controltower.api.models.EOLGroupStatus;
import com.magna.controltower.api.models.EOLInfo;
import com.magna.controltower.api.models.EOLStatusResponse;
import com.magna.controltower.api.models.ManualCollectionGroup;

import org.json.JSONObject;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class GroupActivity extends BaseActivity {

    private LinearLayout groupContainer;
    private ProgressBar progressBar;
    private TextView tvEmpty;
    private EditText etHiddenScanner; // Hidden input for barcode scanner
    private Handler autoRefreshHandler;
    private Handler keyboardHandler; // Keyboard handler for scanner
    private Runnable autoRefreshRunnable;
    private final Runnable showKeyboardRunnable = this::showScannerKeyboardNow;
    private static final long REFRESH_INTERVAL = 1000; // 1 saniye
    private ApiClient apiClient;
    private String previousGroupsJson = ""; // Önceki data'yı sakla
    private boolean isFirstLoad = true; // İlk yükleme kontrolü
    private Map<String, EOLGroupStatus> eolStatusMap = new HashMap<>(); // EOL status cache
    private Map<Integer, Boolean> groupExpandedState = new HashMap<>(); // Grup açık/kapalı durumu
    private List<ManualCollectionGroup> allGroups = new ArrayList<>(); // Tüm grupları sakla (dolly arama için)
    private boolean isScanningDolly = false; // Dolly arama işlemi devam ediyor mu

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_group);

        groupContainer = findViewById(R.id.groupContainer);
        progressBar = findViewById(R.id.progressBar);
        tvEmpty = findViewById(R.id.tvEmpty);
        etHiddenScanner = findViewById(R.id.etHiddenScanner); // Hidden input for barcode

        apiClient = new ApiClient(this);
        keyboardHandler = new Handler(Looper.getMainLooper());

        // Check session validity
        if (!SessionManager.isValid(this)) {
            Toast.makeText(this, "Oturum süresi doldu. Lütfen tekrar giriş yapın.", Toast.LENGTH_LONG).show();
            Intent i = new Intent(this, AuthActivity.class);
            startActivity(i);
            finish();
            return;
        }

        // Display welcome message
        TextView tvWelcome = findViewById(R.id.tvWelcome);
        if (tvWelcome != null) {
            tvWelcome.setText(SessionManager.display(this));
        }

        // Setup barcode scanner for quick navigation
        setupBarcodeScanner();
        showScannerKeyboardDelayed(100);

        // Setup auto-refresh every 1 second (ilk yüklemeyi de yapar)
        setupAutoRefresh();
    }

    private void setupAutoRefresh() {
        autoRefreshHandler = new Handler(Looper.getMainLooper());
        autoRefreshRunnable = new Runnable() {
            @Override
            public void run() {
                if (SessionManager.isValid(GroupActivity.this)) {
                    // Telemetri verilerini ÖNCE yükle (hızlı yanıt için)
                    loadEOLStatus();
                    // Sonra grupları yükle
                    loadEOLGroups();
                }
                autoRefreshHandler.postDelayed(this, REFRESH_INTERVAL);
            }
        };
        // İlk yüklemeyi hemen yap
        autoRefreshHandler.post(autoRefreshRunnable);
    }

    private void loadEOLStatus() {
        apiClient.getService().getEOLStatus().enqueue(new Callback<EOLStatusResponse>() {
            @Override
            public void onResponse(Call<EOLStatusResponse> call, Response<EOLStatusResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    EOLStatusResponse statusResponse = response.body();
                    if (statusResponse.getEolGroups() != null) {
                        // Status'ları map'e kaydet
                        eolStatusMap.clear();
                        for (EOLGroupStatus status : statusResponse.getEolGroups()) {
                            eolStatusMap.put(status.getEolName(), status);
                        }
                    }
                }
            }

            @Override
            public void onFailure(Call<EOLStatusResponse> call, Throwable t) {
                // Sessizce devam et, status bilgisi opsiyonel
            }
        });
    }

    private void loadEOLGroups() {
        // Sadece ilk yüklemede progressBar göster
        if (isFirstLoad) {
            progressBar.setVisibility(View.VISIBLE);
            groupContainer.setVisibility(View.GONE);
            tvEmpty.setVisibility(View.GONE);
        }

        apiClient.getService().getManualCollectionGroups().enqueue(new Callback<List<ManualCollectionGroup>>() {
            @Override
            public void onResponse(Call<List<ManualCollectionGroup>> call, Response<List<ManualCollectionGroup>> response) {
                if (isFirstLoad) {
                    progressBar.setVisibility(View.GONE);
                    isFirstLoad = false;
                }

                if (response.isSuccessful() && response.body() != null) {
                    List<ManualCollectionGroup> groups = response.body();
                    
                    // Tüm grupları sakla (dolly arama için)
                    allGroups = new ArrayList<>(groups);

                    // Smart refresh: sadece data değiştiyse UI güncelle
                    String newGroupsJson = groupsToJson(groups);
                    if (!newGroupsJson.equals(previousGroupsJson)) {
                        previousGroupsJson = newGroupsJson;

                        if (groups.isEmpty()) {
                            groupContainer.setVisibility(View.GONE);
                            tvEmpty.setVisibility(View.VISIBLE);
                            tvEmpty.setText("Henüz dolly yok.");
                            return;
                        }

                        tvEmpty.setVisibility(View.GONE);
                        groupContainer.setVisibility(View.VISIBLE);
                        displayGroups(groups);
                    }
                    // Değişiklik yoksa UI update yok, sadece arka planda kontrol etti

                } else {
                    // Handle error response
                    int code = response.code();

                    if (code == 401) {
                        tvEmpty.setVisibility(View.VISIBLE);
                        tvEmpty.setText("Oturum süresi doldu. Lütfen tekrar giriş yapın.");
                        SessionManager.clear(GroupActivity.this);
                        Intent i = new Intent(GroupActivity.this, AuthActivity.class);
                        startActivity(i);
                        finish();
                    } else {
                        String errorMsg = "Sunucu hatası (" + code + ")";
                        try {
                            if (response.errorBody() != null) {
                                String errorJson = response.errorBody().string();
                                JSONObject jsonError = new JSONObject(errorJson);
                                if (jsonError.has("error")) {
                                    errorMsg = jsonError.getString("error");
                                } else if (jsonError.has("message")) {
                                    errorMsg = jsonError.getString("message");
                                } else {
                                    errorMsg = errorJson;
                                }
                            }
                        } catch (Exception e) {
                            // Use default error message
                        }
                        tvEmpty.setVisibility(View.VISIBLE);
                        tvEmpty.setText(errorMsg);
                        Toast.makeText(GroupActivity.this, errorMsg, Toast.LENGTH_LONG).show();
                    }
                }
            }

            @Override
            public void onFailure(Call<List<ManualCollectionGroup>> call, Throwable t) {
                if (isFirstLoad) {
                    progressBar.setVisibility(View.GONE);
                    isFirstLoad = false;
                    groupContainer.setVisibility(View.GONE);
                    tvEmpty.setVisibility(View.VISIBLE);
                    tvEmpty.setText("Bağlantı hatası: " + t.getMessage());
                    Toast.makeText(GroupActivity.this, "Bağlantı hatası: " + t.getMessage(), Toast.LENGTH_LONG).show();
                }
                // Arka plan yenilemelerinde hata mesajı gösterme, sadece sessizce devam et
            }
        });
    }

    private void displayGroups(List<ManualCollectionGroup> groups) {
        groupContainer.removeAllViews();
        LayoutInflater inflater = LayoutInflater.from(this);

        for (ManualCollectionGroup group : groups) {
            int groupId = group.getGroupId();
            String groupName = group.getGroupName();
            String partNumber = group.getPartNumber();
            int totalDollyCount = group.getTotalDollyCount();
            int totalScannedCount = group.getTotalScannedCount();
            List<EOLInfo> eols = group.getEols();
            
            // Grup wrapper (header + EOL container birlikte)
            View groupWrapper = inflater.inflate(R.layout.item_group_wrapper, groupContainer, false);
            
            // Header içindeki view'ları bul
            TextView tvGroupName = groupWrapper.findViewById(R.id.tvGroupName);
            TextView tvPartNumber = groupWrapper.findViewById(R.id.tvPartNumber);
            TextView tvGroupProgress = groupWrapper.findViewById(R.id.tvGroupProgress);
            TextView tvExpandIcon = groupWrapper.findViewById(R.id.tvExpandIcon);
            TextView tvGroupTelemetry = groupWrapper.findViewById(R.id.tvGroupTelemetry);
            LinearLayout groupTelemetryRow = groupWrapper.findViewById(R.id.groupTelemetryRow);
            android.widget.ProgressBar groupProgressBar = groupWrapper.findViewById(R.id.groupProgressBar);
            TextView tvProgressInfo = groupWrapper.findViewById(R.id.tvProgressInfo);
            TextView tvGroupProgressPercent = groupWrapper.findViewById(R.id.tvProgressPercent);
            
            // EOL Container (grup kartının içinde)
            LinearLayout eolContainer = groupWrapper.findViewById(R.id.eolContainer);

            // Grup adı
            tvGroupName.setText(groupName);
            
            // PartNumber varsa göster
            if (partNumber != null && !partNumber.isEmpty()) {
                String[] parts = partNumber.split("-");
                if (parts.length > 0) {
                    String shortPart = parts[parts.length - 1];
                    if (shortPart.length() > 8) {
                        shortPart = shortPart.substring(shortPart.length() - 8);
                    }
                    tvPartNumber.setText("PN: " + shortPart);
                    tvPartNumber.setVisibility(View.VISIBLE);
                } else {
                    tvPartNumber.setVisibility(View.GONE);
                }
            } else {
                tvPartNumber.setVisibility(View.GONE);
            }
            
            // Toplam ilerleme
            tvGroupProgress.setText(totalScannedCount + "/" + totalDollyCount);
            
            // Progress bar hesapla
            int progressPercent = totalDollyCount > 0 ? (totalScannedCount * 100) / totalDollyCount : 0;
            groupProgressBar.setProgress(progressPercent);
            tvGroupProgressPercent.setText(progressPercent + "%");
            tvProgressInfo.setText(totalScannedCount + "/" + totalDollyCount + " DOLLY TARANDI");
            
            // İlerleme badge ve progress bar rengi
            float completionRate = totalDollyCount > 0 ? (float) totalScannedCount / totalDollyCount : 0;
            int textColor;
            int progressColor;
            if (completionRate >= 1.0f) {
                textColor = 0xFF4CAF50; // Yeşil
                progressColor = 0xFF4CAF50;
            } else if (completionRate >= 0.7f) {
                textColor = 0xFFFFA726; // Turuncu
                progressColor = 0xFFFFA726;
            } else if (completionRate >= 0.3f) {
                textColor = 0xFF42A5F5; // Mavi
                progressColor = 0xFF42A5F5;
            } else if (completionRate > 0) {
                textColor = 0xFF42A5F5; // Mavi
                progressColor = 0xFF42A5F5;
            } else {
                textColor = 0xFF78909C; // Gri
                progressColor = 0xFF78909C;
            }
            tvGroupProgress.setTextColor(textColor);
            tvGroupProgressPercent.setTextColor(progressColor);
            groupProgressBar.setProgressTintList(android.content.res.ColorStateList.valueOf(progressColor));
            
            // Telemetri özeti hesapla (tüm EOL'lerden)
            int totalVinCount = 0;
            int totalMaxCapacity = 0;
            int totalPending = 0;
            boolean hasAlmostFull = false;
            boolean hasFull = false;
            
            if (eols != null) {
                for (EOLInfo eol : eols) {
                    EOLGroupStatus status = eolStatusMap.get(eol.getEolName());
                    if (status != null) {
                        totalVinCount += status.getCurrentVinCount();
                        totalMaxCapacity += status.getMaxVinCapacity();
                        totalPending += status.getPendingDollys();
                        
                        String statusStr = status.getStatus();
                        if ("almost_full".equalsIgnoreCase(statusStr)) hasAlmostFull = true;
                        if ("full".equalsIgnoreCase(statusStr)) hasFull = true;
                    }
                }
            }
            
            // Telemetri metnini oluştur (NORMAL/DİKKAT/DOLU yazıları YOK)
            if (totalMaxCapacity > 0) {
                StringBuilder telemetryText = new StringBuilder();
                telemetryText.append("📦 ").append(totalVinCount).append("/").append(totalMaxCapacity).append(" VIN");
                
                if (totalPending > 0) {
                    telemetryText.append("  ·  ⚠️ ").append(totalPending).append(" Bekleyen");
                }
                
                tvGroupTelemetry.setText(telemetryText.toString());
                groupTelemetryRow.setVisibility(View.VISIBLE);
            } else {
                groupTelemetryRow.setVisibility(View.GONE);
            }
            
            // Expand durumunu kontrol et (varsayılan kapalı)
            boolean isExpanded = groupExpandedState.getOrDefault(groupId, false);
            tvExpandIcon.setText(isExpanded ? "▲" : "▼");
            eolContainer.setVisibility(isExpanded ? View.VISIBLE : View.GONE);
            
            // Wrapper'ı ekle
            groupContainer.addView(groupWrapper);

            // EOL Container içine EOL kartlarını ekle
            eolContainer.removeAllViews(); // Önce temizle
            
            // Her EOL için detaylı kart oluştur
            if (eols != null && !eols.isEmpty()) {
                for (EOLInfo eol : eols) {
                    // YENİ detaylı EOL layout'u kullan
                    View eolItem = inflater.inflate(R.layout.item_eol_detail_new, eolContainer, false);
                    
                    TextView tvEolName = eolItem.findViewById(R.id.tvEolName);
                    TextView tvPartNumberShort = eolItem.findViewById(R.id.tvPartNumberShort);
                    TextView tvDollyCount = eolItem.findViewById(R.id.tvDollyCount);
                    View statusIndicator = eolItem.findViewById(R.id.statusIndicator);
                    android.widget.ProgressBar progressBar = eolItem.findViewById(R.id.progressBar);
                    TextView tvProgressPercent = eolItem.findViewById(R.id.tvProgressPercent);
                    TextView tvProgressLabel = eolItem.findViewById(R.id.tvProgressLabel);
                    TextView tvRemainingInfo = eolItem.findViewById(R.id.tvRemainingInfo);
                    TextView tvVinInfo = eolItem.findViewById(R.id.tvVinInfo);
                    TextView tvPendingDollys = eolItem.findViewById(R.id.tvPendingDollys);
                    View pendingContainer = eolItem.findViewById(R.id.pendingContainer);
                    TextView tvStatusMessage = eolItem.findViewById(R.id.tvStatusMessage);

                    String eolName = eol.getEolName();
                    int dollyCount = eol.getDollyCount();
                    int scannedCount = eol.getScannedCount();

                    // EOL adı (temiz gösterim, bullet point kaldırıldı)
                    tvEolName.setText(eolName);
                    
                    // Dolly sayısı
                    tvDollyCount.setText(scannedCount + "/" + dollyCount);
                    
                    // Dolly sayısına göre renk
                    float dollyRate = dollyCount > 0 ? (float) scannedCount / dollyCount : 0;
                    int dollyColor;
                    if (dollyRate >= 1.0f) {
                        dollyColor = 0xFF4CAF50; // Yeşil
                    } else if (dollyRate >= 0.5f) {
                        dollyColor = 0xFFFFA726; // Turuncu
                    } else if (dollyRate > 0) {
                        dollyColor = 0xFF42A5F5; // Mavi
                    } else {
                        dollyColor = 0xFF78909C; // Gri
                    }
                    tvDollyCount.setTextColor(dollyColor);

                    // Dolma durumu bilgisi
                    EOLGroupStatus status = eolStatusMap.get(eolName);
                    
                    if (status != null) {
                        // VIN progress bar
                        int vinCount = status.getCurrentVinCount();
                        int maxCapacity = status.getMaxVinCapacity();
                        int progress = maxCapacity > 0 ? (vinCount * 100) / maxCapacity : 0;
                        
                        progressBar.setMax(100);
                        progressBar.setProgress(progress);
                        progressBar.setVisibility(View.VISIBLE);
                        
                        // Progress yüzdesi
                        tvProgressPercent.setText(vinCount + "/" + maxCapacity);
                        
                        // Progress label (% yerine net sayılar)
                        tvProgressLabel.setText(vinCount + "/" + maxCapacity + " VIN DOLU");
                        
                        // Kalan VIN sayısı
                        int remaining = maxCapacity - vinCount;
                        if (remaining > 0) {
                            tvRemainingInfo.setText(remaining + " VIN kaldı");
                            tvRemainingInfo.setVisibility(View.VISIBLE);
                        } else {
                            tvRemainingInfo.setVisibility(View.GONE);
                        }
                        
                        // Progress bar rengi
                        if (progress >= 90) {
                            progressBar.setProgressTintList(android.content.res.ColorStateList.valueOf(0xFFE53935)); // Kırmızı
                            tvProgressLabel.setTextColor(0xFFE53935);
                        } else if (progress >= 70) {
                            progressBar.setProgressTintList(android.content.res.ColorStateList.valueOf(0xFFFFA726)); // Turuncu
                            tvProgressLabel.setTextColor(0xFFFFA726);
                        } else {
                            progressBar.setProgressTintList(android.content.res.ColorStateList.valueOf(0xFF4CAF50)); // Yeşil
                            tvProgressLabel.setTextColor(0xFF4CAF50);
                        }
                        
                        // Status indicator (üst sol nokta)
                        int indicatorColor;
                        if (progress >= 90) {
                            indicatorColor = R.drawable.circle_red;
                        } else if (progress >= 70) {
                            indicatorColor = R.drawable.circle_yellow;
                        } else {
                            indicatorColor = R.drawable.circle_green;
                        }
                        statusIndicator.setBackgroundResource(indicatorColor);
                        
                        // Aktif dolly numarası (int olduğu için String'e çevir)
                        int dollyId = status.getCurrentDolly();
                        String dollyNumber = dollyId > 0 ? "#" + dollyId : "N/A";
                        tvVinInfo.setText(dollyNumber);
                        
                        // Bekleyen dolly sayısı
                        if (status.getPendingDollys() > 0) {
                            pendingContainer.setVisibility(View.VISIBLE);
                            tvPendingDollys.setText(String.valueOf(status.getPendingDollys()));
                        } else {
                            pendingContainer.setVisibility(View.GONE);
                        }
                        
                        // Durum mesajı (izin verilen emoji'ler: 📦,⚠️,🔴,🟡,✅)
                        if (status.getMessage() != null && !status.getMessage().isEmpty()) {
                            tvStatusMessage.setVisibility(View.VISIBLE);
                            String statusText = "";
                            
                            // Status'a göre mesaj ve renk
                            switch (status.getStatus() != null ? status.getStatus().toLowerCase() : "") {
                                case "full":
                                    statusText = "🔴 DOLU - " + status.getMessage().toUpperCase();
                                    tvStatusMessage.setTextColor(0xFFE53935); // Kırmızı
                                    break;
                                case "almost_full":
                                    statusText = "⚠️ DİKKAT - " + status.getMessage().toUpperCase();
                                    tvStatusMessage.setTextColor(0xFFFFA726); // Turuncu
                                    break;
                                case "filling":
                                    statusText = "🟡 " + status.getMessage().toUpperCase();
                                    tvStatusMessage.setTextColor(0xFFFFA726); // Turuncu
                                    break;
                                default:
                                    statusText = "✅ " + status.getMessage().toUpperCase();
                                    tvStatusMessage.setTextColor(0xFF66BB6A); // Yeşil
                            }
                            tvStatusMessage.setText(statusText);
                        } else {
                            tvStatusMessage.setVisibility(View.GONE);
                        }
                    } else {
                        // Status yoksa temel bilgileri göster
                        View telemetryRow = eolItem.findViewById(R.id.telemetryRow);
                        if (telemetryRow != null) {
                            telemetryRow.setVisibility(View.GONE);
                        }
                        
                        progressBar.setVisibility(View.GONE);
                        tvProgressPercent.setVisibility(View.GONE);
                        tvProgressLabel.setVisibility(View.GONE);
                        tvRemainingInfo.setVisibility(View.GONE);
                        statusIndicator.setBackgroundResource(R.drawable.circle_green);
                        
                        // Telemetri yok mesajı
                        tvVinInfo.setText("TELEMETRI YOK");
                        tvVinInfo.setTextColor(0xFF7F8FA6);
                        tvVinInfo.setTextSize(12);
                        
                        pendingContainer.setVisibility(View.GONE);
                        tvStatusMessage.setVisibility(View.GONE);
                    }

                    // EOL'a tıklandığında detay ekranına git
                    String groupPartNumber = partNumber;
                    int eolId = eol.getEolId();
                    EOLGroupStatus finalStatus = status; // Lambda için final referans
                    final int finalGroupId = groupId;
                    final String finalGroupName = groupName;
                    eolItem.setOnClickListener(v -> {
                        Intent intent = new Intent(GroupActivity.this, GroupDetailActivity.class);
                        intent.putExtra("group_id", finalGroupId);
                        intent.putExtra("group_name", finalGroupName);
                        intent.putExtra("part_number", groupPartNumber);
                        intent.putExtra("eol_id", eolId);
                        intent.putExtra("eol_name", eolName);
                        intent.putExtra("dolly_count", dollyCount);
                        intent.putExtra("scanned_count", scannedCount);
                        
                        // Dolma durumu bilgisini de gönder
                        if (finalStatus != null) {
                            intent.putExtra("vin_display", finalStatus.getVinDisplay());
                            intent.putExtra("current_dolly", finalStatus.getCurrentDolly());
                            intent.putExtra("pending_dollys", finalStatus.getPendingDollys());
                            intent.putExtra("can_scan", finalStatus.isCanScan());
                            intent.putExtra("status_message", finalStatus.getMessage());
                        }
                        
                        startActivity(intent);
                    });

                    eolContainer.addView(eolItem);
                }
            }
            
            // Grup başlığına tıklama eventi (expand/collapse)
            final int finalGroupId = groupId;
            groupWrapper.findViewById(R.id.groupHeaderRoot).setOnClickListener(v -> {
                boolean currentlyExpanded = groupExpandedState.getOrDefault(finalGroupId, false);
                boolean newState = !currentlyExpanded;
                groupExpandedState.put(finalGroupId, newState);
                
                // Animasyonlu aç/kapa
                eolContainer.setVisibility(newState ? View.VISIBLE : View.GONE);
                tvExpandIcon.setText(newState ? "▲" : "▼");
            });
        }
    }

    private String getStatusText(int scanned, int total) {
        if (scanned == 0)
            return "Bekliyor";
        if (scanned == total)
            return "Tamamlandı";
        return "Yükleniyor (" + scanned + "/" + total + ")";
    }

    private void applyStatus(TextView pill, String status) {
        pill.setText(status);

        if (status.contains("Tamamlandı")) {
            pill.setBackgroundResource(R.drawable.bg_pill_idle);
        } else if (status.contains("Bekliyor")) {
            pill.setBackgroundResource(R.drawable.bg_pill_waiting);
        } else {
            pill.setBackgroundResource(R.drawable.bg_pill_loading);
        }
    }

    private String getStatusColorFromAPI(String apiStatus) {
        if (apiStatus == null) return "Bekliyor";
        
        switch (apiStatus.toLowerCase()) {
            case "empty":
                return "Bekliyor";
            case "filling":
                return "Yükleniyor";
            case "almost_full":
                return "Neredeyse Dolu";
            case "full":
                return "Dolu";
            default:
                return "Yükleniyor";
        }
    }

    // Smart refresh helper: Grup listesini string'e çevir
    private String groupsToJson(List<ManualCollectionGroup> groups) {
        StringBuilder sb = new StringBuilder();
        for (ManualCollectionGroup group : groups) {
            sb.append(group.getGroupId()).append(":")
                    .append(group.getTotalDollyCount()).append(":")
                    .append(group.getTotalScannedCount()).append(";");
            if (group.getEols() != null) {
                for (EOLInfo eol : group.getEols()) {
                    sb.append(eol.getEolId()).append(":")
                            .append(eol.getDollyCount()).append(":")
                            .append(eol.getScannedCount()).append(",");
                }
            }
        }
        return sb.toString();
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) {
            showScannerKeyboardDelayed(150);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        // Reset scanning flag when returning to this activity
        isScanningDolly = false;
        // Restart auto-refresh
        if (autoRefreshHandler != null && autoRefreshRunnable != null) {
            autoRefreshHandler.removeCallbacks(autoRefreshRunnable);
            autoRefreshHandler.postDelayed(autoRefreshRunnable, REFRESH_INTERVAL);
        }
        if (SessionManager.isValid(this)) {
            loadEOLGroups();
        }
        // Barcode scanner'a focus ver ve klavyeyi aç
        showScannerKeyboardDelayed(150);
    }

    @Override
    protected void onPause() {
        super.onPause();
        // Stop auto-refresh when activity is paused
        if (autoRefreshHandler != null && autoRefreshRunnable != null) {
            autoRefreshHandler.removeCallbacks(autoRefreshRunnable);
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        // Clean up handler
        if (autoRefreshHandler != null && autoRefreshRunnable != null) {
            autoRefreshHandler.removeCallbacks(autoRefreshRunnable);
        }
    }

    // ============ BARCODE SCANNER ============

    private void showScannerKeyboardDelayed(int delayMs) {
        if (keyboardHandler != null) {
            keyboardHandler.removeCallbacks(showKeyboardRunnable);
            keyboardHandler.postDelayed(showKeyboardRunnable, delayMs);
        }
    }

    private void showScannerKeyboardNow() {
        if (etHiddenScanner == null) {
            return;
        }
        etHiddenScanner.requestFocus();
        etHiddenScanner.setSelection(etHiddenScanner.getText().length());
        InputMethodManager imm = (InputMethodManager) getSystemService(INPUT_METHOD_SERVICE);
        if (imm != null) {
            imm.showSoftInput(etHiddenScanner, InputMethodManager.SHOW_IMPLICIT);
        }
    }

    private void setupBarcodeScanner() {
        if (etHiddenScanner == null) return;
        
        etHiddenScanner.requestFocus();
        etHiddenScanner.setOnTouchListener((v, e) -> true); // Block manual input
        
        // ENTER key listener
        etHiddenScanner.setOnKeyListener((v, keyCode, event) -> {
            if (event.getAction() == KeyEvent.ACTION_DOWN && keyCode == KeyEvent.KEYCODE_ENTER) {
                String barcode = etHiddenScanner.getText().toString().trim();
                etHiddenScanner.setText(""); // Clear immediately
                if (!barcode.isEmpty()) {
                    handleBarcodeScanned(barcode);
                }
                return true;
            }
            return false;
        });
        
        // Text change listener (for barcode scanners that send newline)
        etHiddenScanner.addTextChangedListener(new TextWatcher() {
            int last = 0;
            
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            
            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {}
            
            @Override
            public void afterTextChanged(Editable s) {
                if (s.length() > last) {
                    char c = s.charAt(s.length() - 1);
                    if (c == '\n' || c == '\r') {
                        String barcode = s.toString().trim();
                        etHiddenScanner.setText(""); // Clear immediately
                        if (!barcode.isEmpty()) {
                            handleBarcodeScanned(barcode);
                        }
                    }
                }
                last = s.length();
            }
        });
    }
    
    private void handleBarcodeScanned(String barcode) {
        if (barcode.isEmpty()) return;
        
        // Çift tarama engelini koy
        if (isScanningDolly) {
            Toast.makeText(this, "⏳ Lütfen bekleyin...", Toast.LENGTH_SHORT).show();
            return;
        }
        
        // Dolly numarasını temizle (sanitize)
        String dollyNo = sanitizeDollyBarcode(barcode);
        
        if (dollyNo.isEmpty()) {
            Toast.makeText(this, "❌ Geçersiz barkod", Toast.LENGTH_SHORT).show();
            return;
        }
        
        // Dolly'nin hangi EOL'de olduğunu bul
        findDollyAndNavigate(dollyNo);
        
        // Klavyeyi tekrar aç
        showScannerKeyboardDelayed(150);
    }
    
    private String sanitizeDollyBarcode(String raw) {
        if (raw == null) return "";
        return raw.replaceAll("[^0-9A-Za-z-]", "").trim();
    }
    
    private void findDollyAndNavigate(String dollyNo) {
        if (allGroups == null || allGroups.isEmpty()) {
            Toast.makeText(this, "⚠️ Gruplar yüklenirken bekleyin...", Toast.LENGTH_SHORT).show();
            return;
        }
        
        isScanningDolly = true;
        Toast.makeText(this, "🔍 Dolly " + dollyNo + " aranıyor...", Toast.LENGTH_SHORT).show();
        
        // Tüm gruplarda ve EOL'lerde dolly'yi ara
        // Backend'e dolly scan denemesi yap, backend bize hangi grup/EOL olduğunu söyleyecek
        tryScansInAllEOLs(dollyNo, 0, 0);
    }
    
    private void tryScansInAllEOLs(String dollyNo, int groupIndex, int eolIndex) {
        if (groupIndex >= allGroups.size()) {
            // Hiçbir EOL'de bulunamadı
            isScanningDolly = false;
            Toast.makeText(this, "❌ Dolly \"" + dollyNo + "\" hiçbir EOL'de bulunamadı!", Toast.LENGTH_LONG).show();
            return;
        }
        
        ManualCollectionGroup group = allGroups.get(groupIndex);
        List<EOLInfo> eols = group.getEols();
        
        if (eols == null || eolIndex >= eols.size()) {
            // Bu grupta EOL kalmadı, sonraki gruba geç
            tryScansInAllEOLs(dollyNo, groupIndex + 1, 0);
            return;
        }
        
        EOLInfo eol = eols.get(eolIndex);
        
        // Bu EOL'de dolly var mı kontrol et (backend'e sor)
        com.magna.controltower.api.models.ManualScanRequest request = 
            new com.magna.controltower.api.models.ManualScanRequest(
                group.getGroupName(), 
                eol.getEolName(), 
                dollyNo
            );
        
        apiClient.getService().manualScan(request).enqueue(new Callback<com.magna.controltower.api.models.ManualScanResponse>() {
            @Override
            public void onResponse(Call<com.magna.controltower.api.models.ManualScanResponse> call, 
                                 Response<com.magna.controltower.api.models.ManualScanResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    // BAŞARILI! Dolly bu EOL'de bulundu ve tarandı
                    isScanningDolly = false;
                    Toast.makeText(GroupActivity.this, "✅ Dolly " + dollyNo + " bulundu ve tarandı!", Toast.LENGTH_SHORT).show();
                    
                    // EOL detay ekranına git
                    Intent intent = new Intent(GroupActivity.this, GroupDetailActivity.class);
                    intent.putExtra("group_id", group.getGroupId());
                    intent.putExtra("eol_id", eol.getEolId());
                    intent.putExtra("group_name", group.getGroupName());
                    intent.putExtra("eol_name", eol.getEolName());
                    intent.putExtra("part_number", group.getPartNumber());
                    startActivity(intent);
                } else {
                    // Hata var - backend'den mesajı kontrol et
                    try {
                        if (response.errorBody() != null) {
                            String errorJson = response.errorBody().string();
                            org.json.JSONObject jsonError = new org.json.JSONObject(errorJson);
                            String errorMsg = "";
                            
                            if (jsonError.has("error")) {
                                errorMsg = jsonError.getString("error");
                            } else if (jsonError.has("message")) {
                                errorMsg = jsonError.getString("message");
                            }
                            
                            // Eğer sıra hatasıysa (bu EOL'de değil), bir sonrakini dene
                            // Farklı grup hatasıysa da bir sonrakini dene
                            // Sadece "dolly yok" gibi kesin hatalarda durdur
                            if (errorMsg.contains("sıra") || errorMsg.contains("order") || 
                                errorMsg.contains("farklı") || errorMsg.contains("different") ||
                                errorMsg.contains("bulunamadı") || errorMsg.contains("not found")) {
                                // Bu EOL'de değil, devam et
                                tryScansInAllEOLs(dollyNo, groupIndex, eolIndex + 1);
                                return;
                            }
                        }
                    } catch (Exception e) {
                        // Parse hatası, bir sonrakini dene
                    }
                    
                    // Diğer hatalar için de bir sonrakini dene
                    tryScansInAllEOLs(dollyNo, groupIndex, eolIndex + 1);
                }
            }
            
            @Override
            public void onFailure(Call<com.magna.controltower.api.models.ManualScanResponse> call, Throwable t) {
                // Ağ hatası, bir sonrakini dene
                tryScansInAllEOLs(dollyNo, groupIndex, eolIndex + 1);
            }
        });
    }
}
