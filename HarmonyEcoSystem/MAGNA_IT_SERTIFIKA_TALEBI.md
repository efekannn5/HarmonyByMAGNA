# SSL Sertifika Talebi - Magna IT

**Konu:** Internal Web Server için SSL Sertifikası Talebi

---

## Talep Detayları

**Proje:** Harmony EcoSystem Dashboard  
**Domain:** `ymcharmony.magna.global`  
**IP Adresi:** `10.19.236.29`  
**Port:** 8181 (internal)  
**Amaç:** Dashboard kullanıcılarının HTTPS ile güvenli erişimi

---

## Sertifika Bilgileri

### Common Name (CN):
```
ymcharmony.magna.global
```

### Subject Alternative Names (SAN):
```
DNS: ymcharmony.magna.global
DNS: ymclnxharmony01.magna.global (sunucu hostname)
IP: 10.19.236.29
```

### Sertifika Tipi:
- Internal web server SSL/TLS sertifikası
- Magna Internal CA tarafından imzalanmış

### Validity Period:
- Minimum 1 yıl (önerilen: 2 yıl)

---

## İhtiyacımız Olan Dosyalar

Lütfen aşağıdaki dosyaları sağlayın:

1. **Server Certificate** (`.crt` veya `.pem`)
2. **Private Key** (`.key` veya `.pem`)
3. **Intermediate Certificate Chain** (varsa)
4. **Root CA Certificate** (Magna Internal CA)

---

## Teknik Bilgiler

**Sunucu İşletim Sistemi:** Linux (Ubuntu/Debian)  
**Web Server:** Nginx  
**Mevcut Durum:** Self-signed sertifika kullanılıyor (tarayıcılar uyarı veriyor)  
**Hedef:** Şirket bilgisayarlarında uyarı vermeden HTTPS erişimi  

---

## CSR (Certificate Signing Request)

Eğer CSR gerekiyorsa, aşağıdaki komutu çalıştırarak oluşturabiliriz:

```bash
openssl req -new -newkey rsa:2048 -nodes \
  -keyout harmony.key \
  -out harmony.csr \
  -subj "/C=TR/ST=Istanbul/L=Istanbul/O=Magna/OU=IT/CN=ymcharmony.magna.global"
```

CSR dosyasını size ileteceğiz, siz de Magna CA ile imzalayıp sertifikayı geri gönderebilirsiniz.

---

## İletişim

**Proje Sorumlusu:** [İsim]  
**E-posta:** [Email]  
**Telefon:** [Telefon]  

---

**Not:** Bu sertifika sadece Magna internal network üzerinde kullanılacaktır. External erişim planlanmamaktadır.
