package com.magna.controltower;

import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.view.WindowCompat;

public class SettingsActivity extends BaseActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_settings);

        // Admin kontrolü
        if (!SessionManager.isValid(this)) {
            Toast.makeText(this, "Oturum süresi doldu", Toast.LENGTH_LONG).show();
            Intent i = new Intent(this, AuthActivity.class);
            startActivity(i);
            finish();
            return;
        }

        if (!SessionManager.isAdmin(this)) {
            Toast.makeText(this, "Bu sayfaya erişim yetkiniz yok", Toast.LENGTH_LONG).show();
            Intent i = new Intent(this, GroupActivity.class);
            startActivity(i);
            finish();
            return;
        }

        // Admin bilgisini göster
        TextView tvWelcome = findViewById(R.id.tvWelcomeAdmin);
        if (tvWelcome != null) {
            tvWelcome.setText("Admin Panel - " + SessionManager.display(this));
        }

        EditText et = findViewById(R.id.etBaseUrl);
        et.setText(Prefs.getBaseUrl(this));

        Button btnSave = findViewById(R.id.btnSave);
        btnSave.setOnClickListener(v -> {
            String newUrl = et.getText().toString().trim();
            if (newUrl.isEmpty()) {
                Toast.makeText(this, "URL boş olamaz", Toast.LENGTH_SHORT).show();
                return;
            }
            Prefs.setBaseUrl(this, newUrl);
            Toast.makeText(this, "Ayarlar kaydedildi", Toast.LENGTH_SHORT).show();
        });

        // Logout butonu
        Button btnLogout = findViewById(R.id.btnLogout);
        if (btnLogout != null) {
            btnLogout.setOnClickListener(v -> {
                SessionManager.clear(this);
                Toast.makeText(this, "Çıkış yapıldı", Toast.LENGTH_SHORT).show();
                Intent i = new Intent(this, AuthActivity.class);
                startActivity(i);
                finish();
            });
        }
    }
}
