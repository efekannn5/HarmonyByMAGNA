"""
HARMONYVIEW - SQL View Tabanlı Sorgular
Bu dosya SQL View'ları kullanarak süre analizi yapar.
View'lar oluşturulduktan sonra bu fonksiyonlar kullanılabilir.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List
from pydantic import BaseModel

# =====================================================
# PYDANTIC MODELLER
# =====================================================

class DollyTimeline(BaseModel):
    """Dolly bazında süreç zaman çizelgesi"""
    dolly_no: str
    vin_no: Optional[str]
    part_number: Optional[str]
    adet: int = 1
    eol_name: Optional[str]
    group_name: Optional[str]
    sefer_numarasi: Optional[str]
    plaka_no: Optional[str]
    forklift_operator: Optional[str]
    data_entry_operator: Optional[str]
    
    # Zaman noktaları
    eol_cikis_zamani: Optional[str]
    terminal_okutma_zamani: Optional[str]
    asn_gonderim_zamani: Optional[str]
    irsaliye_gonderim_zamani: Optional[str]
    
    # Süreler (dakika)
    eol_to_terminal_min: Optional[int]
    terminal_to_asn_min: Optional[int]
    terminal_to_irsaliye_min: Optional[int]
    toplam_sure_min: Optional[int]
    
    vardiya: Optional[int]
    islem_tarihi: Optional[str]


class SeferSummary(BaseModel):
    """Sefer bazında özet"""
    sefer_numarasi: str
    plaka_no: Optional[str]
    forklift_operator: Optional[str]
    data_entry_operator: Optional[str]
    
    toplam_dolly: int
    toplam_vin: int
    toplam_adet: int
    farkli_parca_sayisi: int
    
    ilk_okutma: Optional[str]
    son_okutma: Optional[str]
    asn_zamani: Optional[str]
    irsaliye_zamani: Optional[str]
    
    okutma_suresi_min: Optional[int]
    bekleme_suresi_min: Optional[int]
    toplam_sure_min: Optional[int]
    
    vardiya: Optional[int]
    islem_tarihi: Optional[str]


class PartPerformance(BaseModel):
    """Parça bazında performans"""
    part_number: str
    group_name: Optional[str]
    eol_name: Optional[str]
    
    toplam_dolly: int
    toplam_sefer: int
    toplam_vin: int
    toplam_adet: int
    
    ort_sure_min: Optional[float]
    min_sure_min: Optional[int]
    max_sure_min: Optional[int]
    ort_terminal_to_asn_min: Optional[float]


class GroupPerformance(BaseModel):
    """Grup bazında performans"""
    group_name: str
    
    farkli_parca_sayisi: int
    toplam_dolly: int
    toplam_sefer: int
    toplam_vin: int
    toplam_adet: int
    
    ort_toplam_sure_min: Optional[float]
    ort_terminal_to_asn_min: Optional[float]
    ort_eol_to_terminal_min: Optional[float]
    min_sure_min: Optional[int]
    max_sure_min: Optional[int]


class OperatorPerformance(BaseModel):
    """Operatör bazında performans"""
    forklift_operator: str
    
    toplam_sefer: int
    toplam_dolly: int
    toplam_vin: int
    toplam_adet: int
    
    ort_toplam_sure_min: Optional[float]
    ort_terminal_to_asn_min: Optional[float]
    en_hizli_sure_min: Optional[int]
    en_yavas_sure_min: Optional[int]
    
    son_islem_tarihi: Optional[str]


class DailySummary(BaseModel):
    """Günlük özet"""
    islem_tarihi: str
    vardiya: int
    
    toplam_sefer: int
    toplam_dolly: int
    toplam_vin: int
    toplam_adet: int
    aktif_operator_sayisi: int
    
    v710_dolly: int
    j74_dolly: int
    ontampon_dolly: int
    
    ort_toplam_sure_min: Optional[float]
    ort_terminal_to_asn_min: Optional[float]
    en_hizli_sure_min: Optional[int]
    en_yavas_sure_min: Optional[int]


class PendingShipment(BaseModel):
    """Bekleyen sevkiyat"""
    loading_session_id: Optional[str]
    sefer_numarasi: Optional[str]
    plaka_no: Optional[str]
    forklift_operator: Optional[str]
    status: Optional[str]
    
    toplam_dolly: int
    toplam_vin: int
    
    ilk_okutma_zamani: Optional[str]
    son_okutma_zamani: Optional[str]
    yukleme_baslangic: Optional[str]
    yukleme_bitis: Optional[str]
    
    toplam_bekleme_suresi_min: Optional[int]
    veri_girisci_bekleme_suresi_min: Optional[int]
    okutma_suresi_min: Optional[int]


class HourlyThroughput(BaseModel):
    """Saatlik verimlilik"""
    tarih: str
    saat: int
    vardiya: int
    
    sefer_sayisi: int
    dolly_sayisi: int
    vin_sayisi: int
    toplam_adet: int
    
    v710_vin: int
    j74_vin: int


# =====================================================
# VIEW TABANLI SORGULAR
# =====================================================

def get_dolly_timeline(
    db: Session, 
    start_date: date, 
    end_date: date, 
    shift: Optional[int] = None,
    limit: int = 500
) -> List[DollyTimeline]:
    """
    VW_DollyProcessTimeline view'ından dolly bazında zaman çizelgesi
    """
    shift_filter = ""
    if shift:
        shift_filter = f"AND Vardiya = {shift}"
    
    query = text(f"""
        SELECT TOP (:limit)
            DollyNo, VinNo, PartNumber, Adet, EOLName, GroupName,
            SeferNumarasi, PlakaNo, ForkliftOperator, DataEntryOperator,
            EOL_CikisZamani, TerminalOkutmaZamani, ASN_GonderimZamani, Irsaliye_GonderimZamani,
            EOL_To_Terminal_Min, Terminal_To_ASN_Min, Terminal_To_Irsaliye_Min, ToplamSure_Min,
            Vardiya, IslemTarihi
        FROM VW_DollyProcessTimeline WITH (NOLOCK)
        WHERE IslemTarihi BETWEEN :start_date AND :end_date
        {shift_filter}
        ORDER BY TerminalOkutmaZamani DESC
    """)
    
    results = db.execute(query, {
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit
    }).fetchall()
    
    return [DollyTimeline(
        dolly_no=r.DollyNo,
        vin_no=r.VinNo,
        part_number=r.PartNumber,
        adet=r.Adet or 1,
        eol_name=r.EOLName,
        group_name=r.GroupName,
        sefer_numarasi=r.SeferNumarasi,
        plaka_no=r.PlakaNo,
        forklift_operator=r.ForkliftOperator,
        data_entry_operator=r.DataEntryOperator,
        eol_cikis_zamani=str(r.EOL_CikisZamani) if r.EOL_CikisZamani else None,
        terminal_okutma_zamani=str(r.TerminalOkutmaZamani) if r.TerminalOkutmaZamani else None,
        asn_gonderim_zamani=str(r.ASN_GonderimZamani) if r.ASN_GonderimZamani else None,
        irsaliye_gonderim_zamani=str(r.Irsaliye_GonderimZamani) if r.Irsaliye_GonderimZamani else None,
        eol_to_terminal_min=r.EOL_To_Terminal_Min,
        terminal_to_asn_min=r.Terminal_To_ASN_Min,
        terminal_to_irsaliye_min=r.Terminal_To_Irsaliye_Min,
        toplam_sure_min=r.ToplamSure_Min,
        vardiya=r.Vardiya,
        islem_tarihi=str(r.IslemTarihi) if r.IslemTarihi else None
    ) for r in results]


def get_sefer_summary(
    db: Session,
    start_date: date,
    end_date: date,
    shift: Optional[int] = None
) -> List[SeferSummary]:
    """
    VW_SeferSummary view'ından sefer bazında özet
    """
    shift_filter = ""
    if shift:
        shift_filter = f"AND Vardiya = {shift}"
    
    query = text(f"""
        SELECT 
            SeferNumarasi, PlakaNo, ForkliftOperator, DataEntryOperator,
            ToplamDolly, ToplamVIN, ToplamAdet, FarkliParcaSayisi,
            IlkOkutma, SonOkutma, ASNZamani, IrsaliyeZamani,
            OkutmaSuresi_Min, BeklemeSuresi_Min, ToplamSure_Min,
            Vardiya, IslemTarihi
        FROM VW_SeferSummary WITH (NOLOCK)
        WHERE IslemTarihi BETWEEN :start_date AND :end_date
        {shift_filter}
        ORDER BY IlkOkutma DESC
    """)
    
    results = db.execute(query, {
        "start_date": start_date,
        "end_date": end_date
    }).fetchall()
    
    return [SeferSummary(
        sefer_numarasi=r.SeferNumarasi,
        plaka_no=r.PlakaNo,
        forklift_operator=r.ForkliftOperator,
        data_entry_operator=r.DataEntryOperator,
        toplam_dolly=r.ToplamDolly or 0,
        toplam_vin=r.ToplamVIN or 0,
        toplam_adet=r.ToplamAdet or 0,
        farkli_parca_sayisi=r.FarkliParcaSayisi or 0,
        ilk_okutma=str(r.IlkOkutma) if r.IlkOkutma else None,
        son_okutma=str(r.SonOkutma) if r.SonOkutma else None,
        asn_zamani=str(r.ASNZamani) if r.ASNZamani else None,
        irsaliye_zamani=str(r.IrsaliyeZamani) if r.IrsaliyeZamani else None,
        okutma_suresi_min=r.OkutmaSuresi_Min,
        bekleme_suresi_min=r.BeklemeSuresi_Min,
        toplam_sure_min=r.ToplamSure_Min,
        vardiya=r.Vardiya,
        islem_tarihi=str(r.IslemTarihi) if r.IslemTarihi else None
    ) for r in results]


def get_part_performance(
    db: Session,
    start_date: date,
    end_date: date
) -> List[PartPerformance]:
    """
    VW_PartPerformance view'ından parça bazında performans
    """
    query = text("""
        SELECT 
            PartNumber, GroupName, EOLName,
            ToplamDolly, ToplamSefer, ToplamVIN, ToplamAdet,
            OrtSure_Min, MinSure_Min, MaxSure_Min, OrtTerminalToASN_Min
        FROM VW_PartPerformance WITH (NOLOCK)
        WHERE IlkIslemTarihi >= :start_date 
          AND SonIslemTarihi <= :end_date
        ORDER BY ToplamAdet DESC
    """)
    
    results = db.execute(query, {
        "start_date": start_date,
        "end_date": end_date
    }).fetchall()
    
    return [PartPerformance(
        part_number=r.PartNumber,
        group_name=r.GroupName,
        eol_name=r.EOLName,
        toplam_dolly=r.ToplamDolly or 0,
        toplam_sefer=r.ToplamSefer or 0,
        toplam_vin=r.ToplamVIN or 0,
        toplam_adet=r.ToplamAdet or 0,
        ort_sure_min=r.OrtSure_Min,
        min_sure_min=r.MinSure_Min,
        max_sure_min=r.MaxSure_Min,
        ort_terminal_to_asn_min=r.OrtTerminalToASN_Min
    ) for r in results]


def get_group_performance(db: Session) -> List[GroupPerformance]:
    """
    VW_GroupPerformance view'ından grup bazında performans
    """
    query = text("""
        SELECT 
            GroupName,
            FarkliParcaSayisi, ToplamDolly, ToplamSefer, ToplamVIN, ToplamAdet,
            OrtToplamSure_Min, OrtTerminalToASN_Min, OrtEOLToTerminal_Min,
            MinSure_Min, MaxSure_Min
        FROM VW_GroupPerformance WITH (NOLOCK)
        ORDER BY ToplamAdet DESC
    """)
    
    results = db.execute(query).fetchall()
    
    return [GroupPerformance(
        group_name=r.GroupName or 'Diğer',
        farkli_parca_sayisi=r.FarkliParcaSayisi or 0,
        toplam_dolly=r.ToplamDolly or 0,
        toplam_sefer=r.ToplamSefer or 0,
        toplam_vin=r.ToplamVIN or 0,
        toplam_adet=r.ToplamAdet or 0,
        ort_toplam_sure_min=r.OrtToplamSure_Min,
        ort_terminal_to_asn_min=r.OrtTerminalToASN_Min,
        ort_eol_to_terminal_min=r.OrtEOLToTerminal_Min,
        min_sure_min=r.MinSure_Min,
        max_sure_min=r.MaxSure_Min
    ) for r in results]


def get_operator_performance(
    db: Session,
    start_date: date,
    end_date: date
) -> List[OperatorPerformance]:
    """
    VW_OperatorPerformance view'ından operatör bazında performans
    """
    query = text("""
        SELECT 
            ForkliftOperator,
            ToplamSefer, ToplamDolly, ToplamVIN, ToplamAdet,
            OrtToplamSure_Min, OrtTerminalToASN_Min,
            EnHizliSure_Min, EnYavasSure_Min, SonIslemTarihi
        FROM VW_OperatorPerformance WITH (NOLOCK)
        WHERE SonIslemTarihi BETWEEN :start_date AND :end_date
        ORDER BY ToplamAdet DESC
    """)
    
    results = db.execute(query, {
        "start_date": start_date,
        "end_date": end_date
    }).fetchall()
    
    return [OperatorPerformance(
        forklift_operator=r.ForkliftOperator or 'Bilinmiyor',
        toplam_sefer=r.ToplamSefer or 0,
        toplam_dolly=r.ToplamDolly or 0,
        toplam_vin=r.ToplamVIN or 0,
        toplam_adet=r.ToplamAdet or 0,
        ort_toplam_sure_min=r.OrtToplamSure_Min,
        ort_terminal_to_asn_min=r.OrtTerminalToASN_Min,
        en_hizli_sure_min=r.EnHizliSure_Min,
        en_yavas_sure_min=r.EnYavasSure_Min,
        son_islem_tarihi=str(r.SonIslemTarihi) if r.SonIslemTarihi else None
    ) for r in results]


def get_daily_summary(
    db: Session,
    start_date: date,
    end_date: date
) -> List[DailySummary]:
    """
    VW_DailySummary view'ından günlük özet
    """
    query = text("""
        SELECT 
            IslemTarihi, Vardiya,
            ToplamSefer, ToplamDolly, ToplamVIN, ToplamAdet, AktifOperatorSayisi,
            V710_Dolly, J74_Dolly, Ontampon_Dolly,
            OrtToplamSure_Min, OrtTerminalToASN_Min,
            EnHizliSure_Min, EnYavasSure_Min
        FROM VW_DailySummary WITH (NOLOCK)
        WHERE IslemTarihi BETWEEN :start_date AND :end_date
        ORDER BY IslemTarihi DESC, Vardiya ASC
    """)
    
    results = db.execute(query, {
        "start_date": start_date,
        "end_date": end_date
    }).fetchall()
    
    return [DailySummary(
        islem_tarihi=str(r.IslemTarihi),
        vardiya=r.Vardiya or 1,
        toplam_sefer=r.ToplamSefer or 0,
        toplam_dolly=r.ToplamDolly or 0,
        toplam_vin=r.ToplamVIN or 0,
        toplam_adet=r.ToplamAdet or 0,
        aktif_operator_sayisi=r.AktifOperatorSayisi or 0,
        v710_dolly=r.V710_Dolly or 0,
        j74_dolly=r.J74_Dolly or 0,
        ontampon_dolly=r.Ontampon_Dolly or 0,
        ort_toplam_sure_min=r.OrtToplamSure_Min,
        ort_terminal_to_asn_min=r.OrtTerminalToASN_Min,
        en_hizli_sure_min=r.EnHizliSure_Min,
        en_yavas_sure_min=r.EnYavasSure_Min
    ) for r in results]


def get_pending_shipments(db: Session) -> List[PendingShipment]:
    """
    VW_PendingShipments view'ından bekleyen sevkiyatlar
    """
    query = text("""
        SELECT 
            LoadingSessionId, SeferNumarasi, PlakaNo, ForkliftOperator, Status,
            ToplamDolly, ToplamVIN,
            IlkOkutmaZamani, SonOkutmaZamani, YuklemeBaslangic, YuklemeBitis,
            ToplamBeklemeSuresi_Min, VeriGirisciBeklemeSuresi_Min, OkutmaSuresi_Min
        FROM VW_PendingShipments WITH (NOLOCK)
        ORDER BY ToplamBeklemeSuresi_Min DESC
    """)
    
    results = db.execute(query).fetchall()
    
    return [PendingShipment(
        loading_session_id=r.LoadingSessionId,
        sefer_numarasi=r.SeferNumarasi,
        plaka_no=r.PlakaNo,
        forklift_operator=r.ForkliftOperator,
        status=r.Status,
        toplam_dolly=r.ToplamDolly or 0,
        toplam_vin=r.ToplamVIN or 0,
        ilk_okutma_zamani=str(r.IlkOkutmaZamani) if r.IlkOkutmaZamani else None,
        son_okutma_zamani=str(r.SonOkutmaZamani) if r.SonOkutmaZamani else None,
        yukleme_baslangic=str(r.YuklemeBaslangic) if r.YuklemeBaslangic else None,
        yukleme_bitis=str(r.YuklemeBitis) if r.YuklemeBitis else None,
        toplam_bekleme_suresi_min=r.ToplamBeklemeSuresi_Min,
        veri_girisci_bekleme_suresi_min=r.VeriGirisciBeklemeSuresi_Min,
        okutma_suresi_min=r.OkutmaSuresi_Min
    ) for r in results]


def get_hourly_throughput(
    db: Session,
    target_date: date
) -> List[HourlyThroughput]:
    """
    VW_HourlyThroughput view'ından saatlik verimlilik
    """
    query = text("""
        SELECT 
            Tarih, Saat, Vardiya,
            SeferSayisi, DollySayisi, VINSayisi, ToplamAdet,
            V710_VIN, J74_VIN
        FROM VW_HourlyThroughput WITH (NOLOCK)
        WHERE Tarih = :target_date
        ORDER BY Saat ASC
    """)
    
    results = db.execute(query, {"target_date": target_date}).fetchall()
    
    return [HourlyThroughput(
        tarih=str(r.Tarih),
        saat=r.Saat,
        vardiya=r.Vardiya,
        sefer_sayisi=r.SeferSayisi or 0,
        dolly_sayisi=r.DollySayisi or 0,
        vin_sayisi=r.VINSayisi or 0,
        toplam_adet=r.ToplamAdet or 0,
        v710_vin=r.V710_VIN or 0,
        j74_vin=r.J74_VIN or 0
    ) for r in results]


# =====================================================
# VIEW KONTROL FONKSİYONLARI
# =====================================================

def check_views_exist(db: Session) -> dict:
    """
    Gerekli view'ların veritabanında var olup olmadığını kontrol eder
    """
    required_views = [
        'VW_DollyProcessTimeline',
        'VW_SeferSummary',
        'VW_PartPerformance',
        'VW_GroupPerformance',
        'VW_OperatorPerformance',
        'VW_DailySummary',
        'VW_PendingShipments',
        'VW_HourlyThroughput'
    ]
    
    query = text("""
        SELECT name 
        FROM sys.views 
        WHERE name LIKE 'VW_%'
    """)
    
    existing = {r[0] for r in db.execute(query).fetchall()}
    
    return {
        'existing': list(existing),
        'missing': [v for v in required_views if v not in existing],
        'all_present': all(v in existing for v in required_views)
    }
