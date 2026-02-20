package com.magna.controltower;

import android.os.Bundle;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.view.WindowCompat;

public class NextActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_next);

        TextView tv = findViewById(R.id.tvNext);
        String tag = getIntent().getStringExtra("user_tag");
        tv.setText("Next screen\nDoğrulama durumu: " + (tag == null ? "—" : tag));
    }
}
