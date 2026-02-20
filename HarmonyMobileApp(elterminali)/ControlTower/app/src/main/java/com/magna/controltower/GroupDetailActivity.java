package com.magna.controltower;

import android.util.Log;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.KeyEvent;
import android.view.inputmethod.InputMethodManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.magna.controltower.adapter.KasaAdapter;
import com.magna.controltower.api.models.EOLDollysResponse;
import com.magna.controltower.api.models.GroupDolly;
import com.magna.controltower.api.models.GroupDollysResponse;
import com.magna.controltower.api.models.ManualScanRequest;
import com.magna.controltower.api.models.ManualScanResponse;
import com.magna.controltower.api.models.ManualSubmitRequest;
import com.magna.controltower.api.models.ManualSubmitResponse;
import com.magna.controltower.model.DollyHold;
import com.magna.controltower.model.KasaItem;

import org.json.JSONArray;
import org.json.JSONObject;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class GroupDetailActivity extends BaseActivity {

    private static final String TAG = "GroupDetailActivity";
    private int groupId;
    private String groupName;
    private String partNumber;
    private int eolId;
    private String eolName;
    private RecyclerView rvKasa;
    private KasaAdapter adapter;
    private EditText etHidden;
    private TextView tvRemoveMode;
    private TextView tvDollyStatus; // Dolma durumu TextView'i
    private ProgressBar progressBar;
    private boolean isLoading = false;
    private boolean isRemoveMode = false;
    private String lastScannedBarcode = ""; // Son taranan barkod
    private long lastScanTime = 0; // Son tarama zamanı
    private long lastSubmitTime = 0; // Son submit zamanı
    private Handler autoRefreshHandler;
    private Runnable autoRefreshRunnable;
    private final Handler keyboardHandler = new Handler(Looper.getMainLooper());
    private final Runnable showKeyboardRunnable = this::showScannerKeyboardNow;
    private static final long REFRESH_INTERVAL = 1000; // 1 saniye
    private ApiClient apiClient;
    private String previousDollysJson = ""; // Önceki dolly data'sını sakla
    private boolean isFirstLoad = true; // İlk yükleme kontrolü
    private int totalGroupScannedCount = 0; // Grup genelindeki taranan dolly sayısı

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_group_detail);

        groupId = getIntent().getIntExtra("group_id", 0);
        groupName = getIntent().getStringExtra("group_name");
        partNumber = getIntent().getStringExtra("part_number");
        eolId = getIntent().getIntExtra("eol_id", 0);
        eolName = getIntent().getStringExtra("eol_name");
        
        if (groupName == null)
            groupName = "Grup";
        if (eolName == null)
            eolName = "EOL";

        apiClient = new ApiClient(this);

        // Setup Toolbar
        androidx.appcompat.widget.Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            String title = eolName + " • Kasa Okuma";
            // PartNumber varsa kısaltılmış halini ekle
            if (partNumber != null && !partNumber.isEmpty()) {
                String[] parts = partNumber.split("-");
                if (parts.length > 0) {
                    String shortPart = parts[parts.length - 1];
                    if (shortPart.length() > 8) {
                        shortPart = shortPart.substring(shortPart.length() - 8);
                    }
                    title = eolName + " [" + shortPart + "] • Kasa Okuma";
                }
            }
            getSupportActionBar().setTitle(title);
        }

        tvDollyStatus = findViewById(R.id.tvDollyStatus); // Dolma durumu
        
        rvKasa = findViewById(R.id.rvKasa);
        progressBar = findViewById(R.id.progressBar);
        etHidden = findViewById(R.id.etHidden);
        tvRemoveMode = findViewById(R.id.tvRemoveMode);
        
        // Intent'ten gelen dolma durumu bilgisi
        String vinDisplay = getIntent().getStringExtra("vin_display");
        int currentDolly = getIntent().getIntExtra("current_dolly", 0);
        int pendingDollys = getIntent().getIntExtra("pending_dollys", 0);
        boolean initialCanScan = getIntent().getBooleanExtra("can_scan", true);
        String statusMessage = getIntent().getStringExtra("status_message");
        
        updateDollyStatusUI(currentDolly, vinDisplay, pendingDollys, statusMessage, initialCanScan);

        rvKasa.setLayoutManager(new LinearLayoutManager(this));
        adapter = new KasaAdapter(this, new ArrayList<>(), groupName);
        rvKasa.setAdapter(adapter);
        
        // RecyclerView scroll ederken EditText focus'unu korumak için
        rvKasa.setOnTouchListener((v, event) -> {
            // Scroll oluşabilir ama focus değişmesin
            etHidden.requestFocus();
            return false; // Event'i consume etme, scroll yapsın
        });

        setupBarcodeScanner();
        showScannerKeyboardDelayed(100);

        // Setup auto-refresh every 1 second (auto-refresh ilk yüklemeyi de yapacak)
        setupAutoRefresh();
        
        // Grup bazında scanned dolly sayısını başlangıçta da hesapla (submit butonu için)
        updateGroupScannedCount();
    }

    private void setupAutoRefresh() {
        autoRefreshHandler = new Handler(Looper.getMainLooper());
        autoRefreshRunnable = new Runnable() {
            @Override
            public void run() {
                if (!isRemoveMode && !isLoading) {
                    loadDollys();
                }
                autoRefreshHandler.postDelayed(this, REFRESH_INTERVAL);
            }
        };
        // İlk refresh'i hemen başlat
        autoRefreshHandler.post(autoRefreshRunnable);
    }

    private void exitRemoveMode() {
        isRemoveMode = false;
        tvRemoveMode.setVisibility(TextView.GONE);
    }

    private void setupBarcodeScanner() {
        etHidden.requestFocus();
        etHidden.setOnTouchListener((v, e) -> true);

        etHidden.setOnKeyListener((v, keyCode, event) -> {
            if (event.getAction() == KeyEvent.ACTION_DOWN && keyCode == KeyEvent.KEYCODE_ENTER) {
                String raw = etHidden.getText().toString();
                etHidden.setText(""); // Clear immediately
                if (!raw.trim().isEmpty()) {
                    handleBarcodeInput(raw);
                }
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
                        etHidden.setText(""); // Clear immediately
                        if (!raw.trim().isEmpty()) {
                            handleBarcodeInput(raw);
                        }
                    }
                }
                last = s.length();
            }
        });
    }

    private void handleBarcodeInput(String rawBarcode) {
        if (isRemoveMode) {
            removeLastDolly(rawBarcode);
        } else {
            scanDolly(rawBarcode);
        }
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

    private void loadDollys() {
        // İlk yüklemede progress göster, sonrasında sessizce güncelle
        if (isLoading && isFirstLoad) {
            return; // Sadece ilk yükleme sırasında bloke et
        }
        
        boolean wasLoading = isLoading;
        isLoading = true;
        
        // Sadece ilk yüklemede progressBar göster
        if (isFirstLoad) {
            progressBar.setVisibility(ProgressBar.VISIBLE);
        }

        Log.d(TAG, "loadDollys() called for groupId: " + groupId + ", eolId: " + eolId);
        apiClient.getService().getEOLDollys(groupId, eolId).enqueue(new Callback<EOLDollysResponse>() {
            @Override
            public void onResponse(Call<EOLDollysResponse> call, Response<EOLDollysResponse> response) {
                if (isFirstLoad) {
                    progressBar.setVisibility(ProgressBar.GONE);
                    isFirstLoad = false;
                }
                isLoading = false;

                if (response.isSuccessful() && response.body() != null) {
                    EOLDollysResponse responseBody = response.body();
                    
                    // 🔍 DEBUG: Raw JSON response'u logla
                    try {
                        com.google.gson.Gson gson = new com.google.gson.Gson();
                        String jsonResponse = gson.toJson(responseBody);
                        Log.d(TAG, "📄 RAW JSON Response: " + jsonResponse);
                    } catch (Exception e) {
                        Log.e(TAG, "JSON log hatası: " + e.getMessage());
                    }
                    
                    // PartNumber'ı backend'den al ve kaydet
                    String backendPartNumber = responseBody.getPartNumber();
                    if (backendPartNumber != null && !backendPartNumber.isEmpty()) {
                        partNumber = backendPartNumber;
                    }
                    
                    List<GroupDolly> dollys = responseBody.getDollys();
                    List<KasaItem> kasaItems = new ArrayList<>();

                    if (dollys != null) {
                        Log.d(TAG, "📦 Backend'den " + dollys.size() + " dolly alındı");
                        
                        // ✅ Backend'den gelen dolly_order_no'ya göre SIRALA (en küçükten büyüğe)
                        dollys.sort((d1, d2) -> {
                            try {
                                int order1 = Integer.parseInt(d1.getDollyOrderNo());
                                int order2 = Integer.parseInt(d2.getDollyOrderNo());
                                return Integer.compare(order1, order2);
                            } catch (Exception e) {
                                return 0; // Parse edilemezse sırayı değiştirme
                            }
                        });
                        Log.d(TAG, "✅ Dolly'ler backend order'a göre sıralandı (küçükten büyüğe)");
                        
                        for (GroupDolly dolly : dollys) {
                            String dollyNo = dolly.getDollyNo();
                            String dollyOrderNo = dolly.getDollyOrderNo();
                            String vinNo = dolly.getVinNo();
                            boolean scanned = dolly.isScanned();
                            
                            // Backend'den gelen order'ı aynen kullan
                            Log.d(TAG, "🔍 Dolly: " + dollyNo + " (Order: " + dollyOrderNo + ")");

                            Log.d(TAG, "Processing dolly: " + dollyNo + " (Order: " + dollyOrderNo + "), raw VIN: " + vinNo);

                            // Parse VIN numbers
                            String[] vins = vinNo.split("\\r?\\n");
                            List<String> vinList = new ArrayList<>();
                            for (String vin : vins) {
                                if (!vin.trim().isEmpty()) {
                                    vinList.add(vin.trim());
                                }
                            }

                            Log.d(TAG, "  Parsed " + vinList.size() + " VINs for dolly " + dollyNo);
                            for (int i = 0; i < vinList.size(); i++) {
                                Log.d(TAG, "    VIN[" + i + "]: " + vinList.get(i));
                            }

                            String firstVin = vinList.isEmpty() ? "" : vinList.get(0);
                            String lastVin = vinList.isEmpty() ? "" : vinList.get(vinList.size() - 1);

                            // Backend'den gelen dollyOrderNo'yu aynen kullan
                            KasaItem item = new KasaItem(dollyNo, dollyOrderNo, firstVin, lastVin, vinList);
                            if (scanned) {
                                item.setStatus(KasaItem.Status.SCANNED);
                            }

                            kasaItems.add(item);
                        }
                    }

                    Log.d(TAG, "Total KasaItems created: " + kasaItems.size());

                    // Smart refresh: sadece data değiştiyse UI güncelle
                    String newDollysJson = dollysToJson(kasaItems);
                    if (!newDollysJson.equals(previousDollysJson)) {
                        previousDollysJson = newDollysJson;
                        adapter.updateData(kasaItems);
                        updateButtonState(kasaItems);
                    }
                    // Değişiklik yoksa UI update yok, sadece arka planda kontrol etti

                } else {
                    int code = response.code();

                    if (code == 401) {
                        Toast.makeText(GroupDetailActivity.this, "Oturum süresi doldu", Toast.LENGTH_LONG).show();
                        SessionManager.clear(GroupDetailActivity.this);
                        Intent i = new Intent(GroupDetailActivity.this, AuthActivity.class);
                        startActivity(i);
                        finish();
                    } else {
                        String errorMsg = "Yükleme hatası (" + code + ")";
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
                        Toast.makeText(GroupDetailActivity.this, errorMsg, Toast.LENGTH_LONG).show();
                    }
                }
            }

            @Override
            public void onFailure(Call<EOLDollysResponse> call, Throwable t) {
                if (isFirstLoad) {
                    progressBar.setVisibility(ProgressBar.GONE);
                    isFirstLoad = false;
                    Toast.makeText(GroupDetailActivity.this, "Yükleme hatası: " + t.getMessage(), Toast.LENGTH_LONG).show();
                }
                isLoading = false;
                // Arka plan yenilemelerinde hata mesajı gösterme
            }
        });
    }

    private void updateButtonState(List<KasaItem> items) {
        // Menu'yu yenile - onPrepareOptionsMenu otomatik çağrılacak
        invalidateOptionsMenu();
    }

    private void scanDolly(String rawBarcode) {
        String barcode = sanitize(rawBarcode);
        if (barcode.isEmpty()) {
            Toast.makeText(this, "❌ Boş barkod. Lütfen tekrar okutun.", Toast.LENGTH_SHORT).show();
            return;
        }
        
        // Basit debounce: Aynı barkodu 500ms içinde tekrar okutmayı engelle
        long currentTime = System.currentTimeMillis();
        if (barcode.equals(lastScannedBarcode) && (currentTime - lastScanTime) < 500) {
            return; // Çift okuma, sessizce görmezden gel
        }
        lastScannedBarcode = barcode;
        lastScanTime = currentTime;

        // ✅ GRUP MANTIĞI: Multi-EOL okutma destekleniyor
        // Backend'de EOL bazlı sıra kontrolü yapılıyor
        // Her EOL kendi içinde sıralı, EOL'lar arası geçiş serbest

        progressBar.setVisibility(ProgressBar.VISIBLE);

        // Doğru grup ve EOL adlarını gönder
        ManualScanRequest request = new ManualScanRequest(groupName, eolName, barcode);

        apiClient.getService().manualScan(request).enqueue(new Callback<ManualScanResponse>() {
            @Override
            public void onResponse(Call<ManualScanResponse> call, Response<ManualScanResponse> response) {
                progressBar.setVisibility(ProgressBar.GONE);

                if (response.isSuccessful() && response.body() != null) {
                    // Başarılı - sessizce yenile
                    Toast.makeText(GroupDetailActivity.this, "✅ Dolly okutuldu: " + response.body().getDollyNo(), Toast.LENGTH_SHORT).show();
                    loadDollys();
                    updateGroupScannedCount(); // Submit butonu için grup sayacını güncelle
                } else {
                    // Hata durumu - API'den gelen hatayı göster
                    final String[] errorMsgHolder = {"Okutma hatası"}; // Array kullan (effectively final)
                    String expectedDollyFromAPI = null;
                    String receivedDollyFromAPI = null;
                    String dialogTitle = "⚠️ Okutma Hatası";
                    
                    try {
                        if (response.errorBody() != null) {
                            String errorJson = response.errorBody().string();
                            org.json.JSONObject jsonError = new org.json.JSONObject(errorJson);
                            
                            if (jsonError.has("error")) {
                                errorMsgHolder[0] = jsonError.getString("error");
                            } else if (jsonError.has("message")) {
                                errorMsgHolder[0] = jsonError.getString("message");
                            }
                            
                            // Hata detaylarını al
                            if (jsonError.has("expected_dolly")) {
                                expectedDollyFromAPI = jsonError.getString("expected_dolly");
                                // Backend'den null veya empty gelirse "BİLİNMİYOR" gösterme
                                if (expectedDollyFromAPI == null || expectedDollyFromAPI.trim().isEmpty() || 
                                    expectedDollyFromAPI.equalsIgnoreCase("null")) {
                                    expectedDollyFromAPI = null; // Backend hatası var demektir
                                }
                            }
                            if (jsonError.has("received_dolly")) {
                                receivedDollyFromAPI = jsonError.getString("received_dolly");
                            }
                            
                            // Farklı grup hatası kontrolü
                            if (errorMsgHolder[0].contains("grubuna ait") || errorMsgHolder[0].contains("farklı grup")) {
                                dialogTitle = "⛔ Farklı Grup!";
                            }
                            
                            // Sıra hatası kontrolü
                            if (errorMsgHolder[0].contains("sıra") || errorMsgHolder[0].contains("order")) {
                                dialogTitle = "⚠️ Dolly Sırası Yanlış!";
                            }
                        }
                    } catch (Exception e) {
                        errorMsgHolder[0] = "Okutma başarısız (" + response.code() + ")";
                    }
                    
                    final String errorMsg = errorMsgHolder[0]; // Final reference
                    
                    // Detaylı hata mesajı göster
                    String fullErrorMsg = errorMsg;
                    
                    // Farklı grup hatası için özel mesaj
                    if (errorMsg.contains("grubuna ait") || errorMsg.contains("farklı grup") || errorMsg.contains("değil")) {
                        // Grup adını parse etmeye çalış
                        String correctGroup = "";
                        if (errorMsg.contains("'") && errorMsg.split("'").length >= 2) {
                            correctGroup = errorMsg.split("'")[1]; // İlk tırnak içindeki grup adı
                        }
                        
                        fullErrorMsg = "⛔ FARKLI GRUP HATASI!\n\n" +
                                      "Bu dolly başka bir gruba ait ve okutulamaz.\n\n" +
                                      "📍 Şu an açık grup: " + groupName + "\n" +
                                      "📍 EOL: " + eolName;
                        
                        if (!correctGroup.isEmpty()) {
                            fullErrorMsg += "\n\n✅ Dolly'nin ait olduğu grup:\n   \"" + correctGroup + "\"\n\n" +
                                          "💡 Grup listesine dönüp doğru grubu seçin.";
                        } else {
                            fullErrorMsg += "\n\n" + errorMsg + "\n\n" +
                                          "💡 Grup listesine dönüp doğru grubu seçin.";
                        }
                    } else if (errorMsg.contains("sıra") || errorMsg.contains("order")) {
                        // Dolly sırası hatası
                        dialogTitle = "⚠️ Dolly Sırası Yanlış!";
                        
                        // Backend detay göndermemişse fallback kullan
                        String expectedDolly = expectedDollyFromAPI;
                        String receivedDolly = receivedDollyFromAPI != null ? receivedDollyFromAPI : barcode;
                        
                        if (expectedDolly == null || expectedDolly.trim().isEmpty()) {
                            // Backend expected_dolly göndermemiş, liste view'dan bul
                            expectedDolly = getNextPendingDolly();
                        }
                        
                        // Temiz hata mesajı oluştur
                        fullErrorMsg = "⚠️ DOLLY SIRASI HATASI!\n\n" +
                                      eolName + " EOL'de dolly sırayı atlayamazsın!\n\n";
                        
                        if (expectedDolly != null && !expectedDolly.trim().isEmpty()) {
                            fullErrorMsg += "❌ Okutulan: " + receivedDolly + "\n" +
                                          "✅ Sıradaki: " + expectedDolly + "\n\n";
                        } else {
                            // Hiç dolly bulunamadıysa (bu durumda olmaz ama yine de)
                            fullErrorMsg += "❌ Okutulan: " + receivedDolly + "\n\n";
                        }
                        
                        fullErrorMsg += "📍 EOL: " + eolName + "\n\n" +
                                       "Lütfen sıradaki dolly'yi okutun.";
                    }
                    
                    new androidx.appcompat.app.AlertDialog.Builder(GroupDetailActivity.this)
                            .setTitle(dialogTitle)
                            .setMessage(fullErrorMsg)
                            .setPositiveButton("✅ Tamam", (dialog, which) -> {
                                // Farklı grup hatası ise grup listesine dön
                                if (errorMsg.contains("grubuna ait") || errorMsg.contains("farklı grup") || errorMsg.contains("değil")) {
                                    new androidx.appcompat.app.AlertDialog.Builder(GroupDetailActivity.this)
                                            .setTitle("📋 Grup Listesine Dön?")
                                            .setMessage("Bu dolly farklı bir gruba ait.\n\n" +
                                                       "Doğru grubu seçmek için grup listesine dönmek ister misiniz?")
                                            .setPositiveButton("✅ Evet, Dön", (d, w) -> finish())
                                            .setNegativeButton("❌ Hayır, Kal", null)
                                            .show();
                                }
                            })
                            .setIcon(android.R.drawable.ic_dialog_alert)
                            .show();
                    
                    loadDollys();
                }
            }

            @Override
            public void onFailure(Call<ManualScanResponse> call, Throwable t) {
                progressBar.setVisibility(ProgressBar.GONE);
                Toast.makeText(GroupDetailActivity.this, "❌ Bağlantı hatası: " + t.getMessage(), Toast.LENGTH_LONG).show();
            }
        });
    }

    private void removeLastDolly(String rawBarcode) {
        String barcode = sanitize(rawBarcode);
        if (barcode.isEmpty()) {
            Toast.makeText(this, "Boş barkod. Lütfen tekrar okutun.", Toast.LENGTH_SHORT).show();
            return;
        }
        
        // Basit debounce: Aynı barkodu 500ms içinde tekrar okutmayı engelle
        long currentTime = System.currentTimeMillis();
        if (barcode.equals(lastScannedBarcode) && (currentTime - lastScanTime) < 500) {
            return;
        }
        lastScannedBarcode = barcode;
        lastScanTime = currentTime;

        progressBar.setVisibility(ProgressBar.VISIBLE);

        // Doğru grup ve EOL adlarını gönder
        ManualScanRequest request = new ManualScanRequest(groupName, eolName, barcode);

        apiClient.getService().manualRemoveLast(request).enqueue(new Callback<ManualScanResponse>() {
            @Override
            public void onResponse(Call<ManualScanResponse> call, Response<ManualScanResponse> response) {
                progressBar.setVisibility(ProgressBar.GONE);

                if (response.isSuccessful() && response.body() != null) {
                    ManualScanResponse scanResponse = response.body();
                    Toast.makeText(GroupDetailActivity.this, "✓ Son kasa çıkartıldı: " + scanResponse.getDollyNo(),
                            Toast.LENGTH_SHORT).show();
                    exitRemoveMode();
                    loadDollys();

                } else {
                    int code = response.code();

                    if (code == 401) {
                        Toast.makeText(GroupDetailActivity.this, "Oturum süresi doldu", Toast.LENGTH_LONG).show();
                        SessionManager.clear(GroupDetailActivity.this);
                        Intent i = new Intent(GroupDetailActivity.this, AuthActivity.class);
                        startActivity(i);
                        finish();
                    } else {
                        String errorMsg = "Çıkartma hatası (" + code + ")";
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
                        Toast.makeText(GroupDetailActivity.this, errorMsg, Toast.LENGTH_LONG).show();
                    }
                    exitRemoveMode();
                }
            }

            @Override
            public void onFailure(Call<ManualScanResponse> call, Throwable t) {
                progressBar.setVisibility(ProgressBar.GONE);
                Toast.makeText(GroupDetailActivity.this, "Çıkartma hatası: " + t.getMessage(), Toast.LENGTH_LONG)
                        .show();
                exitRemoveMode();
            }
        });
    }

    private void submitGroup() {
        if (isLoading)
            return;

        isLoading = true;
        progressBar.setVisibility(ProgressBar.VISIBLE);

        ManualSubmitRequest request = new ManualSubmitRequest(eolName);

        apiClient.getService().manualSubmit(request).enqueue(new Callback<ManualSubmitResponse>() {
            @Override
            public void onResponse(Call<ManualSubmitResponse> call, Response<ManualSubmitResponse> response) {
                progressBar.setVisibility(ProgressBar.GONE);
                isLoading = false;

                if (response.isSuccessful() && response.body() != null) {
                    ManualSubmitResponse submitResponse = response.body();

                    // Show success message
                    new androidx.appcompat.app.AlertDialog.Builder(GroupDetailActivity.this)
                            .setTitle("Başarılı!")
                            .setMessage(submitResponse.getMessage() + "\n\n" +
                                    "Dolly Sayısı: " + submitResponse.getSubmittedCount() + "\n" +
                                    "VIN Sayısı: " + submitResponse.getVinCount() + "\n" +
                                    "Part Number: " + submitResponse.getPartNumber())
                            .setPositiveButton("Tamam", (dialog, which) -> {
                                // Go back to group list
                                finish();
                            })
                            .setCancelable(false)
                            .show();

                } else {
                    int code = response.code();

                    if (code == 401) {
                        Toast.makeText(GroupDetailActivity.this, "Oturum süresi doldu", Toast.LENGTH_LONG).show();
                        SessionManager.clear(GroupDetailActivity.this);
                        Intent i = new Intent(GroupDetailActivity.this, AuthActivity.class);
                        startActivity(i);
                        finish();
                    } else {
                        String errorMsg = "Submit hatası (" + code + ")";
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

                        new androidx.appcompat.app.AlertDialog.Builder(GroupDetailActivity.this)
                                .setTitle("Hata")
                                .setMessage(errorMsg)
                                .setPositiveButton("Tamam", null)
                                .show();
                    }
                }
            }

            @Override
            public void onFailure(Call<ManualSubmitResponse> call, Throwable t) {
                progressBar.setVisibility(ProgressBar.GONE);
                isLoading = false;

                new androidx.appcompat.app.AlertDialog.Builder(GroupDetailActivity.this)
                        .setTitle("Bağlantı Hatası")
                        .setMessage(t.getMessage())
                        .setPositiveButton("Tamam", null)
                        .show();
            }
        });
    }
    
    // Grup genelindeki scanned dolly sayısını hesapla (submit butonu için)
    private void updateGroupScannedCount() {
        apiClient.getService().getGroupDollys(groupId).enqueue(new Callback<GroupDollysResponse>() {
            @Override
            public void onResponse(Call<GroupDollysResponse> call, Response<GroupDollysResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    GroupDollysResponse groupResponse = response.body();
                    
                    int totalScanned = 0;
                    if (groupResponse.getEols() != null) {
                        for (GroupDollysResponse.EolGroup eolGroup : groupResponse.getEols()) {
                            List<GroupDolly> dollys = eolGroup.getDollys();
                            if (dollys != null) {
                                for (GroupDolly dolly : dollys) {
                                    if (dolly.isScanned()) {
                                        totalScanned++;
                                    }
                                }
                            }
                        }
                    }
                    
                    totalGroupScannedCount = totalScanned;
                    invalidateOptionsMenu(); // Menu'yu güncelle
                    
                    Log.d(TAG, "updateGroupScannedCount: " + totalGroupScannedCount + " dollies scanned in group");
                }
            }

            @Override
            public void onFailure(Call<GroupDollysResponse> call, Throwable t) {
                Log.e(TAG, "Failed to update group scanned count: " + t.getMessage());
            }
        });
    }
    
    // Tüm gruptaki EOL'leri al ve submit özeti göster
    private void fetchGroupSummaryAndSubmit() {
        // Basit debounce: 1 saniye içinde tekrar submit'e basmayı engelle
        long currentTime = System.currentTimeMillis();
        if (currentTime - lastSubmitTime < 1000) {
            return; // Çok hızlı ard arda basma, sessizce görmezden gel
        }
        lastSubmitTime = currentTime;
        
        // Zaten yükleniyorsa kullanıcıya bildir
        if (isLoading) {
            Toast.makeText(this, "⏳ Lütfen bekleyin...", Toast.LENGTH_SHORT).show();
            return;
        }

        isLoading = true;
        progressBar.setVisibility(ProgressBar.VISIBLE);

        // Grup içindeki tüm EOL'lerin dolly bilgilerini al
        apiClient.getService().getGroupDollys(groupId).enqueue(new Callback<GroupDollysResponse>() {
            @Override
            public void onResponse(Call<GroupDollysResponse> call, Response<GroupDollysResponse> response) {
                progressBar.setVisibility(ProgressBar.GONE);
                isLoading = false;

                if (response.isSuccessful() && response.body() != null) {
                    GroupDollysResponse groupResponse = response.body();
                    
                    Log.d(TAG, "Group Response: " + groupResponse);
                    Log.d(TAG, "EOLs count: " + (groupResponse.getEols() != null ? groupResponse.getEols().size() : "null"));
                    
                    // Part number'ı backend'den al
                    String backendPartNumber = groupResponse.getPartNumber();
                    if (backendPartNumber != null && !backendPartNumber.isEmpty()) {
                        partNumber = backendPartNumber;
                    }
                    
                    // Her EOL için okutulan dolly sayısını hesapla
                    StringBuilder eolSummary = new StringBuilder();
                    int totalScanned = 0;
                    int totalDollys = 0;
                    
                    if (groupResponse.getEols() == null || groupResponse.getEols().isEmpty()) {
                        Log.e(TAG, "Backend'den EOL listesi gelmedi!");
                        Toast.makeText(GroupDetailActivity.this, 
                            "Backend hatası: EOL listesi boş", Toast.LENGTH_LONG).show();
                        return;
                    }
                    
                    for (GroupDollysResponse.EolGroup eolGroup : groupResponse.getEols()) {
                        String eolNameStr = eolGroup.getEolName();
                        List<GroupDolly> dollys = eolGroup.getDollys();
                        
                        Log.d(TAG, "EOL: " + eolNameStr + ", Dolly count: " + (dollys != null ? dollys.size() : "null"));
                        
                        int scannedInEol = 0;
                        for (GroupDolly dolly : dollys) {
                            totalDollys++;
                            if (dolly.isScanned()) {
                                scannedInEol++;
                                totalScanned++;
                                Log.d(TAG, "Scanned dolly: " + dolly.getDollyNo());
                            }
                        }
                        
                        Log.d(TAG, "EOL " + eolNameStr + " scanned: " + scannedInEol + "/" + dollys.size());
                        
                        if (scannedInEol > 0) {
                            eolSummary.append("📍 ").append(eolNameStr).append(": ")
                                     .append(scannedInEol).append(" / ").append(dollys.size())
                                     .append(" dolly\n");
                        }
                    }
                    
                    Log.d(TAG, "Total scanned: " + totalScanned + "/" + totalDollys);
                    
                    // Global değişkeni güncelle (menu için)
                    totalGroupScannedCount = totalScanned;
                    invalidateOptionsMenu(); // Menu'yu yenile
                    
                    // Submit onay dialogunu göster
                    showGroupSubmitConfirmation(totalScanned, totalDollys, eolSummary.toString(), partNumber);
                    
                } else {
                    int code = response.code();
                    Log.e(TAG, "Failed to get group dollys. Code: " + code);
                    
                    // Error body'yi oku
                    try {
                        if (response.errorBody() != null) {
                            String errorJson = response.errorBody().string();
                            Log.e(TAG, "Error response: " + errorJson);
                        }
                    } catch (Exception e) {
                        Log.e(TAG, "Error reading error body", e);
                    }
                    
                    if (code == 401) {
                        Toast.makeText(GroupDetailActivity.this, "Oturum süresi doldu", Toast.LENGTH_LONG).show();
                        SessionManager.clear(GroupDetailActivity.this);
                        Intent i = new Intent(GroupDetailActivity.this, AuthActivity.class);
                        startActivity(i);
                        finish();
                    } else {
                        Toast.makeText(GroupDetailActivity.this, "Grup bilgisi alınamadı (" + code + ")", Toast.LENGTH_SHORT).show();
                    }
                }
            }

            @Override
            public void onFailure(Call<GroupDollysResponse> call, Throwable t) {
                progressBar.setVisibility(ProgressBar.GONE);
                isLoading = false;
                Toast.makeText(GroupDetailActivity.this, "Bağlantı hatası: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }
    
    // Grup submit onay dialogu (EOL özeti ile)
    private void showGroupSubmitConfirmation(int totalScanned, int totalDollys, String eolSummary, String partNum) {
        if (totalScanned == 0) {
            new androidx.appcompat.app.AlertDialog.Builder(this)
                    .setTitle("⚠️ Uyarı")
                    .setMessage("Hiç dolly okutulmamış!\n\nEn az 1 dolly okutmalısınız.")
                    .setPositiveButton("Tamam", null)
                    .show();
            return;
        }
        
        String partInfo = "";
        if (partNum != null && !partNum.isEmpty()) {
            partInfo = "\n📋 Part Number: " + partNum + "\n";
        }
        
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("✅ Submit Onayı")
                .setMessage("🚛 " + groupName + " grubunu submit etmek istiyor musunuz?\n" +
                           partInfo + "\n" +
                           "📦 Toplam: " + totalScanned + " / " + totalDollys + " dolly\n\n" +
                           "🔍 EOL Detayı:\n" + eolSummary)
                .setPositiveButton("✅ Submit", (dialog, which) -> submitGroupWithPartNumber(partNum))
                .setNegativeButton("❌ İptal", null)
                .show();
    }
    
    // Grup submit (part number ile)
    private void submitGroupWithPartNumber(String partNum) {
        if (isLoading)
            return;

        isLoading = true;
        progressBar.setVisibility(ProgressBar.VISIBLE);

        // Grup bazlı submit: group_id + group_name + part_number
        ManualSubmitRequest request = new ManualSubmitRequest(groupId, groupName, partNum);

        apiClient.getService().manualSubmit(request).enqueue(new Callback<ManualSubmitResponse>() {
            @Override
            public void onResponse(Call<ManualSubmitResponse> call, Response<ManualSubmitResponse> response) {
                progressBar.setVisibility(ProgressBar.GONE);
                isLoading = false;

                if (response.isSuccessful() && response.body() != null) {
                    ManualSubmitResponse submitResponse = response.body();

                    new androidx.appcompat.app.AlertDialog.Builder(GroupDetailActivity.this)
                            .setTitle("✅ Başarılı!")
                            .setMessage(submitResponse.getMessage() + "\n\n" +
                                    "📦 Dolly Sayısı: " + submitResponse.getSubmittedCount() + "\n" +
                                    "🔖 VIN Sayısı: " + submitResponse.getVinCount() + "\n" +
                                    "📋 Part Number: " + submitResponse.getPartNumber())
                            .setPositiveButton("Tamam", (dialog, which) -> {
                                finish(); // Grup listesine dön
                            })
                            .setCancelable(false)
                            .show();

                } else {
                    int code = response.code();

                    if (code == 401) {
                        Toast.makeText(GroupDetailActivity.this, "Oturum süresi doldu", Toast.LENGTH_LONG).show();
                        SessionManager.clear(GroupDetailActivity.this);
                        Intent i = new Intent(GroupDetailActivity.this, AuthActivity.class);
                        startActivity(i);
                        finish();
                    } else {
                        String errorMsg = "Submit hatası (" + code + ")";
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

                        new androidx.appcompat.app.AlertDialog.Builder(GroupDetailActivity.this)
                                .setTitle("❌ Hata")
                                .setMessage(errorMsg)
                                .setPositiveButton("Tamam", null)
                                .show();
                    }
                }
            }

            @Override
            public void onFailure(Call<ManualSubmitResponse> call, Throwable t) {
                progressBar.setVisibility(ProgressBar.GONE);
                isLoading = false;

                new androidx.appcompat.app.AlertDialog.Builder(GroupDetailActivity.this)
                        .setTitle("⚠️ Bağlantı Hatası")
                        .setMessage(t.getMessage())
                        .setPositiveButton("Tamam", null)
                        .show();
            }
        });
    }

    // Smart refresh helper: Dolly listesini string'e çevir
    private String dollysToJson(List<KasaItem> items) {
        StringBuilder sb = new StringBuilder();
        for (KasaItem item : items) {
            sb.append(item.getKasaNo()).append(":")
                    .append(item.getStatus().name()).append(";");
        }
        return sb.toString();
    }

    private String sanitize(String s) {
        if (s == null)
            return "";
        return s.replaceAll("[\\r\\n\\t\\u0000-\\u001F]", "").trim();
    }

    /**
     * GRUP MANTIĞI: Aynı EOL içinde sıradaki PENDING dolly'yi bul
     * @return Sıradaki dolly numarası veya null (tüm dollyler tarandıysa)
     */
    private String getNextPendingDolly() {
        if (adapter == null || adapter.getData() == null) {
            return null;
        }
        
        for (KasaItem item : adapter.getData()) {
            if (item.getStatus() == KasaItem.Status.PENDING) {
                // Sıra numarası varsa "SEQ-32008: 1070949" formatında döndür
                if (item.getDollyOrderNo() != null && !item.getDollyOrderNo().isEmpty()) {
                    return "SEQ-" + item.getDollyOrderNo() + ": " + item.getKasaNo();
                } else {
                    return item.getKasaNo();
                }
            }
        }
        
        return null; // Tüm dollyler tarandı
    }

    @Override
    protected void onResume() {
        super.onResume();
        etHidden.requestFocus();
        showScannerKeyboardDelayed(150);
        // Restart auto-refresh
        if (autoRefreshHandler != null && autoRefreshRunnable != null) {
            autoRefreshHandler.removeCallbacks(autoRefreshRunnable);
            autoRefreshHandler.postDelayed(autoRefreshRunnable, REFRESH_INTERVAL);
        }
    }

    @Override    public boolean onCreateOptionsMenu(android.view.Menu menu) {
        getMenuInflater().inflate(R.menu.menu_group_detail, menu);
        return true;
    }

    @Override
    public boolean onPrepareOptionsMenu(android.view.Menu menu) {
        // Remove butonu için sadece bu EOL'deki scanned sayısına bak
        int currentEolScannedCount = 0;
        if (adapter != null && adapter.getData() != null) {
            for (KasaItem item : adapter.getData()) {
                if (item.getStatus() == KasaItem.Status.SCANNED) {
                    currentEolScannedCount++;
                }
            }
        }
        
        android.view.MenuItem submitItem = menu.findItem(R.id.action_submit);
        android.view.MenuItem removeItem = menu.findItem(R.id.action_remove_last);
        
        // Submit butonu: GRUP genelinde en az 1 dolly taranmış olmalı
        // (totalGroupScannedCount fetchGroupSummaryAndSubmit çağrısından güncellenir)
        if (submitItem != null) {
            // İlk yüklemede her zaman etkin, sonra grup kontrolüne göre
            submitItem.setEnabled(totalGroupScannedCount > 0);
        }
        // Remove butonu: Sadece bu EOL'de en az 1 dolly taranmış olmalı
        if (removeItem != null) {
            removeItem.setEnabled(currentEolScannedCount > 0);
        }
        
        return super.onPrepareOptionsMenu(menu);
    }

    @Override
    public boolean onOptionsItemSelected(android.view.MenuItem item) {
        int id = item.getItemId();
        
        if (id == R.id.action_manual_add) {
            // Manuel dolly ekle
            showManualDollyDialog();
            return true;
        } else if (id == R.id.action_submit) {
            // Submit action - Grup bazlı (tüm EOL'lerden)
            // Önce tüm gruptaki EOL'leri ve okutulan dolly sayılarını al
            fetchGroupSummaryAndSubmit();
            return true;
        } else if (id == R.id.action_remove_last) {
            // Remove last action
            if (!isRemoveMode) {
                isRemoveMode = true;
                tvRemoveMode.setVisibility(TextView.VISIBLE);
                Toast.makeText(this, "Çıkartılacak kasanın barkodunu okutun", Toast.LENGTH_SHORT).show();
            } else {
                exitRemoveMode();
            }
            return true;
        }
        
        return super.onOptionsItemSelected(item);
    }

    @Override    protected void onPause() {
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

    // Manuel dolly ekleme - özel sayısal klavye ile
    private void showManualDollyDialog() {
        // Custom numeric keyboard layout'u inflate et
        View keyboardView = getLayoutInflater().inflate(R.layout.dialog_numeric_keyboard, null);
        
        // Display textview
        final TextView tvDisplay = keyboardView.findViewById(R.id.tvDollyDisplay);
        final StringBuilder dollyNumber = new StringBuilder();
        
        // Sayı butonları
        int[] numberButtonIds = {
            R.id.btn0, R.id.btn1, R.id.btn2, R.id.btn3, R.id.btn4,
            R.id.btn5, R.id.btn6, R.id.btn7, R.id.btn8, R.id.btn9
        };
        
        for (int i = 0; i < numberButtonIds.length; i++) {
            final String number = String.valueOf(i);
            Button btn = keyboardView.findViewById(numberButtonIds[i]);
            btn.setOnClickListener(v -> {
                dollyNumber.append(number);
                tvDisplay.setText(dollyNumber.toString());
            });
        }
        
        // Backspace butonu (son karakteri sil)
        Button btnBackspace = keyboardView.findViewById(R.id.btnBackspace);
        btnBackspace.setOnClickListener(v -> {
            if (dollyNumber.length() > 0) {
                dollyNumber.deleteCharAt(dollyNumber.length() - 1);
                tvDisplay.setText(dollyNumber.length() > 0 ? dollyNumber.toString() : "0");
            }
        });
        
        // Clear butonu (tümünü temizle)
        Button btnClear = keyboardView.findViewById(R.id.btnClear);
        btnClear.setOnClickListener(v -> {
            dollyNumber.setLength(0);
            tvDisplay.setText("0");
        });
        
        // Dialog oluştur
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("📦 Manuel Dolly Ekle")
                .setMessage("📋 Grup: " + groupName + "\n" +
                           "📍 EOL: " + eolName + "\n\n" +
                           "💡 Her EOL kendi içinde sıralı okutulmalı\n" +
                           "💡 EOL'lar arası geçiş serbesttir\n\n" +
                           "Dolly numarasını girin:")
                .setView(keyboardView)
                .setPositiveButton("✅ Ekle", (dialog, which) -> {
                    String enteredDolly = dollyNumber.toString().trim();
                    
                    if (enteredDolly.isEmpty() || enteredDolly.equals("0")) {
                        Toast.makeText(this, "❌ Dolly numarası boş olamaz!", Toast.LENGTH_SHORT).show();
                        return;
                    }
                    
                    // Backend'de validasyon yapılacak - direkt gönder
                    scanDolly(enteredDolly);
                })
                .setNegativeButton("❌ İptal", null)
                .show();
    }

    // Eski admin barkod dialog - artık kullanılmıyor, silinebilir
    private void showAdminBarcodeDialog(String dollyNo) {
        // Custom layout için EditText oluştur
        final EditText input = new EditText(this);
        input.setHint("� Dolly numarasını girin (örn: 1062279)");
        input.setSingleLine(true);
        input.setTextSize(18);
        input.setTextColor(0xFF000000);
        input.setHintTextColor(0xFF757575);
        input.setPadding(40, 30, 40, 30);
        input.setBackgroundResource(android.R.drawable.edit_text);
        input.setInputType(android.text.InputType.TYPE_CLASS_NUMBER);
        
        // EditText için container (margin eklemek için)
        android.widget.LinearLayout container = new android.widget.LinearLayout(this);
        container.setOrientation(android.widget.LinearLayout.VERTICAL);
        android.widget.LinearLayout.LayoutParams params = new android.widget.LinearLayout.LayoutParams(
            android.widget.LinearLayout.LayoutParams.MATCH_PARENT,
            android.widget.LinearLayout.LayoutParams.WRAP_CONTENT
        );
        params.setMargins(50, 20, 50, 20);
        input.setLayoutParams(params);
        container.addView(input);
        
        androidx.appcompat.app.AlertDialog dialog = new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("📝 Manuel Dolly Ekle")
                .setMessage("⚠️ Etiket silinmiş veya okunamıyor mu?\n\nDolly numarasını manuel olarak girin:")
                .setView(container)
                .setPositiveButton("✓ Ekle", null)
                .setNegativeButton("✕ İptal", null)
                .setCancelable(true)
                .create();
        
        dialog.setOnShowListener(dialogInterface -> {
            Button btnPositive = dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE);
            Button btnNegative = dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_NEGATIVE);
            
            // Buton renklerini ayarla
            btnPositive.setTextColor(0xFF4CAF50); // Yeşil
            btnNegative.setTextColor(0xFFE53935); // Kırmızı
            
            btnPositive.setOnClickListener(v -> {
                String manualDollyNo = input.getText().toString().trim();
                if (manualDollyNo.isEmpty()) {
                    Toast.makeText(this, "⚠️ Dolly numarası gerekli", Toast.LENGTH_SHORT).show();
                    input.setError("Boş bırakılamaz");
                    return;
                }
                
                // Dolly numarasını ekle
                dialog.dismiss();
                performManualScan(manualDollyNo);
            });
        });
        
        dialog.show();
        input.requestFocus();
        
        // Klavyeyi otomatik göster
        input.postDelayed(() -> {
            InputMethodManager imm = (InputMethodManager) getSystemService(INPUT_METHOD_SERVICE);
            if (imm != null) {
                imm.showSoftInput(input, InputMethodManager.SHOW_IMPLICIT);
            }
        }, 100);
    }

    // Manuel scan işlemi
    private void performManualScan(String dollyNo) {
        progressBar.setVisibility(ProgressBar.VISIBLE);
        
        // Doğru grup ve EOL adlarını gönder
        ManualScanRequest request = new ManualScanRequest(groupName, eolName, dollyNo);
        
        apiClient.getService().manualScan(request).enqueue(new Callback<ManualScanResponse>() {
            @Override
            public void onResponse(Call<ManualScanResponse> call, Response<ManualScanResponse> response) {
                progressBar.setVisibility(ProgressBar.GONE);
                
                if (response.isSuccessful() && response.body() != null) {
                    ManualScanResponse scanResponse = response.body();
                    Toast.makeText(GroupDetailActivity.this, 
                            "✅ Manuel eklendi: " + scanResponse.getDollyNo(), 
                            Toast.LENGTH_SHORT).show();
                    loadDollys();
                } else {
                    int code = response.code();
                    String errorMsg = "Manuel ekleme hatası (" + code + ")";
                    
                    if (code == 401) {
                        Toast.makeText(GroupDetailActivity.this, "Oturum süresi doldu", Toast.LENGTH_LONG).show();
                        SessionManager.clear(GroupDetailActivity.this);
                        Intent i = new Intent(GroupDetailActivity.this, AuthActivity.class);
                        startActivity(i);
                        finish();
                    } else {
                        try {
                            if (response.errorBody() != null) {
                                String errorJson = response.errorBody().string();
                                JSONObject jsonError = new JSONObject(errorJson);
                                if (jsonError.has("error")) {
                                    errorMsg = jsonError.getString("error");
                                } else if (jsonError.has("message")) {
                                    errorMsg = jsonError.getString("message");
                                }
                            }
                        } catch (Exception e) {
                            // Use default error message
                        }
                        Toast.makeText(GroupDetailActivity.this, errorMsg, Toast.LENGTH_LONG).show();
                    }
                }
            }
            
            @Override
            public void onFailure(Call<ManualScanResponse> call, Throwable t) {
                progressBar.setVisibility(ProgressBar.GONE);
                Toast.makeText(GroupDetailActivity.this, 
                        "Bağlantı hatası: " + t.getMessage(), 
                        Toast.LENGTH_LONG).show();
            }
        });
    }

    // Dolly dolma durumunu göster
    private void updateDollyStatusUI(int currentDolly, String vinDisplay, int pendingDollys, String message, boolean canScan) {
        if (tvDollyStatus == null) return;
        
        View statusCard = findViewById(R.id.statusCard);
        
        if (currentDolly > 0 && vinDisplay != null) {
            statusCard.setVisibility(View.VISIBLE);
            
            String statusText = "📦 Dolly: " + currentDolly + " | VIN: " + vinDisplay;
            if (pendingDollys > 0) {
                statusText += " | ⏳ Bekleyen: " + pendingDollys;
            }
            if (message != null && !message.isEmpty()) {
                statusText += "\n" + message;
            }
            if (!canScan) {
                statusText += " 🔴 ";
                tvDollyStatus.setBackgroundColor(0xFFD32F2F); // Kırmızı arka plan
            } else {
                tvDollyStatus.setBackgroundColor(0xFF1E2329); // Normal arka plan
            }
            
            tvDollyStatus.setText(statusText);
        } else {
            statusCard.setVisibility(View.GONE);
        }
    }
}
