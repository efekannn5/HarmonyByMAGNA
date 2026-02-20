# SSL Sertifikası Güvenilir Yapma Rehberi

Harmony EcoSystem self-signed (kendi imzalı) SSL sertifikası kullandığı için, tarayıcılar "güvenilir değil" uyarısı verir. Bu uyarıyı kaldırmak için:

## 🍎 macOS (Safari, Chrome için)

### Adım 1: Sertifikayı İndirin
1. Sunucudan `cert.pem` dosyasını indirin:
   - Dosya yolu: `/home/ymc_harmony/Harmony/HarmonyEcoSystem/HarmonyEcoSystem/ssl/cert.pem`

### Adım 2: Keychain'e Ekleyin
1. İndirdiğiniz `cert.pem` dosyasına çift tıklayın
2. "Keychain Access" açılacak
3. "System" keychain'i seçin (veya "login")
4. Sertifikayı bulun (localhost veya ymcharmony.magna.global)
5. Sertifikaya çift tıklayın
6. "Trust" (Güven) bölümünü açın
7. "When using this certificate" → **"Always Trust"** seçin
8. Pencereyi kapatın (şifrenizi girmeniz istenecek)

### Adım 3: Tarayıcıyı Yeniden Başlatın
- Safari veya Chrome'u tamamen kapatıp açın

## 🪟 Windows (Chrome, Edge için)

### Adım 1: Sertifikayı İndirin
1. Sunucudan `cert.pem` dosyasını indirin

### Adım 2: Sertifikayı Yükleyin
1. `cert.pem` dosyasına sağ tıklayın
2. **"Install Certificate"** seçin
3. "Store Location" → **"Local Machine"** (Yönetici hakları gerekir)
4. "Next" tıklayın
5. **"Place all certificates in the following store"** seçin
6. "Browse" tıklayın
7. **"Trusted Root Certification Authorities"** seçin
8. "Next" ve "Finish" tıklayın
9. Uyarıyı kabul edin

### Adım 3: Tarayıcıyı Yeniden Başlatın
- Tarayıcıyı tamamen kapatıp açın

## 🦊 Firefox (Tüm İşletim Sistemleri)

Firefox kendi sertifika deposunu kullanır:

1. Firefox'u açın
2. Ayarlar → Privacy & Security
3. "Certificates" bölümünde **"View Certificates"** tıklayın
4. "Authorities" sekmesine gidin
5. **"Import"** tıklayın
6. `cert.pem` dosyasını seçin
7. **"Trust this CA to identify websites"** işaretleyin
8. "OK" tıklayın
9. Firefox'u yeniden başlatın

## 🚀 Hızlı Test (Geçici Çözüm)

Sertifikayı yüklemeden test etmek için:
- **Safari**: "Ayrıntılar" → "Web Sitesini Ziyaret Et"
- **Chrome**: "Advanced" → "Proceed to ymcharmony.magna.global"
- **Firefox**: "Advanced" → "Accept the Risk and Continue"

⚠️ Bu geçici çözüm sadece o oturum için geçerlidir.

## ✅ Doğrulama

Sertifika doğru yüklendiyse:
- Adres çubuğunda 🔒 (kilit) simgesi görünür
- "Bağlantı güvenli" mesajı gelir
- Uyarı mesajı kalkmış olur

## 🏢 Şirket Geneli Dağıtım

IT yöneticileri için:
- Group Policy (Windows) veya MDM (Mac) ile tüm bilgisayarlara otomatik dağıtım yapılabilir
- Sertifika dosyası: `/home/ymc_harmony/Harmony/HarmonyEcoSystem/HarmonyEcoSystem/ssl/cert.pem`

---

**Not**: Bu adımlar kullanıcıların kendi bilgisayarlarında yapılmalıdır. Sunucu tarafı zaten yapılandırılmıştır.
