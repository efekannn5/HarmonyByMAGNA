package com.magna.controltower;

import android.app.admin.DeviceAdminReceiver;
import android.content.Context;
import android.content.Intent;
import android.widget.Toast;

/**
 * Device Admin Receiver - Kiosk modu için gerekli
 * 
 * Kullanım:
 * 1. Cihazda hiçbir Google hesabı olmamalı
 * 2. Cihazı fabrika ayarlarına döndür
 * 3. USB debugging aç
 * 4. ADB komutu çalıştır:
 *    adb shell dpm set-device-owner com.magna.controltower/.KioskModeReceiver
 * 5. Uygulama artık Device Owner olarak çalışacak
 */
public class KioskModeReceiver extends DeviceAdminReceiver {
    
    @Override
    public void onEnabled(Context context, Intent intent) {
        super.onEnabled(context, intent);
        Toast.makeText(context, "Kiosk modu etkinleştirildi", Toast.LENGTH_SHORT).show();
    }
    
    @Override
    public void onDisabled(Context context, Intent intent) {
        super.onDisabled(context, intent);
        Toast.makeText(context, "Kiosk modu devre dışı bırakıldı", Toast.LENGTH_SHORT).show();
    }
    
    @Override
    public CharSequence onDisableRequested(Context context, Intent intent) {
        return "Device Owner modunu devre dışı bırakmak istiyor musunuz?";
    }
}
