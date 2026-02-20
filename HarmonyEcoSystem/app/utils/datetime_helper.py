"""
Datetime helper utilities - Türkiye yerel saati (Europe/Istanbul) için
"""
from datetime import datetime
from zoneinfo import ZoneInfo

# Türkiye saat dilimi
TURKEY_TZ = ZoneInfo("Europe/Istanbul")


def now_turkey():
    """
    Türkiye yerel saatini döndürür (timezone-aware)
    
    Returns:
        datetime: Türkiye saat diliminde şu anki zaman
    """
    return datetime.now(TURKEY_TZ)


def now_turkey_naive():
    """
    Türkiye yerel saatini döndürür (timezone-naive, eski kod uyumluluğu için)
    
    Not: Veritabanında timezone bilgisi yoksa bu kullanılmalı
    
    Returns:
        datetime: Türkiye saat diliminde şu anki zaman (timezone bilgisi olmadan)
    """
    return datetime.now(TURKEY_TZ).replace(tzinfo=None)


# Geriye uyumluluk için alias
get_local_time = now_turkey_naive
