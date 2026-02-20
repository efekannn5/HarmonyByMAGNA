package com.magna.controltower;

import android.content.Intent;
import android.os.Bundle;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.view.WindowCompat;

public class MainActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // Bu activity artık sadece AuthActivity'ye yönlendirir
        startActivity(new Intent(this, AuthActivity.class));
        finish();
    }
}