"""
CEVA DT Supplier Web Service Integration
SOAP XML based ASN submission service
"""

from __future__ import annotations

import logging
import ssl
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
from lxml import etree
from flask import current_app


logger = logging.getLogger(__name__)


class TLSAdapter(HTTPAdapter):
    """Custom HTTP Adapter to enforce TLS 1.2+ only"""
    
    def init_poolmanager(self, *args, **kwargs):
        """Initialize pool manager with TLS 1.2+ enforcement"""
        ctx = create_urllib3_context()
        # Enforce minimum TLS 1.2 (disable TLS 1.0 and 1.1)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        # Allow TLS 1.2 and TLS 1.3
        ctx.maximum_version = ssl.TLSVersion.MAXIMUM_SUPPORTED
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)


@dataclass
class ASNItemDetail:
    """Single VIN/Part detail for ASN"""
    dolly_number: Optional[str]
    vin_number: str
    part_number: str
    qty: int
    process_time: datetime
    waybill_number: str  # İrsaliye numarası
    trip_reason_code: str = "TRC-00"  # Hata kodu (default: Problemsiz Sefer)
    dolly_eye: int = 1  # Dolly göz numarası


@dataclass
class ASNResponse:
    """CEVA API Response"""
    successful: bool
    result_description: str
    raw_response: Optional[str] = None


class CevaService:
    """CEVA DT Supplier Web Service Client"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize CEVA service with config
        
        Args:
            config: Application config dictionary containing 'ceva' section
        """
        self.config = config.get('ceva', {})
        
        if not self.config.get('enabled', False):
            logger.warning("CEVA service is disabled in config")
            return
        
        # Get environment-specific settings
        env = self.config.get('environment', 'uat')
        env_config = self.config.get(env, {})
        
        self.url = env_config.get('url')
        self.username = env_config.get('username')
        self.password = env_config.get('password')
        self.supplier_code = env_config.get('supplier_code')
        self.user_id = env_config.get('user_id', '0')  # UserId (default: 0)
        self.timeout = self.config.get('timeout', 30)
        self.retry_count = self.config.get('retry_count', 2)
        
        if not all([self.url, self.username, self.password, self.supplier_code]):
            logger.error("CEVA service configuration is incomplete")
            raise ValueError("CEVA service configuration missing required fields")
        
        # Create session with TLS 1.2+ enforcement
        self.session = requests.Session()
        self.session.mount('https://', TLSAdapter())
        
        logger.info(f"CEVA Service initialized: env={env}, url={self.url}")
        logger.info(f"🔒 TLS Security: Minimum TLS 1.2 enforced (TLS 1.0/1.1 disabled)")

    def send_asn(
        self, 
        trip_code: str, 
        asn_details: List[ASNItemDetail]
    ) -> ASNResponse:
        """
        Send ASN to CEVA system
        
        Args:
            trip_code: Sefer numarası (TripCode)
            asn_details: List of VIN/Part details in ORDER
            
        Returns:
            ASNResponse with success status and message
        """
        if not self.config.get('enabled', False):
            logger.warning("CEVA service disabled - returning mock success")
            return ASNResponse(
                successful=True,
                result_description="CEVA servisi devre dışı (test modu)"
            )
        
        if not asn_details:
            return ASNResponse(
                successful=False,
                result_description="ASN detayları boş - en az 1 VIN gerekli"
            )
        
        logger.info(f"📤 CEVA ASN gönderimi başlatılıyor: TripCode={trip_code}, VIN Count={len(asn_details)}")
        
        # Build SOAP XML
        soap_xml = self._build_soap_request(trip_code, asn_details)
        
        # LOG: Gönderilecek XML'i tam olarak logla
        logger.info(f"📨 CEVA'ya Gönderilecek FULL XML:\n{soap_xml}")
        
        # Send with retry logic
        for attempt in range(1, self.retry_count + 2):
            try:
                logger.info(f"🌐 CEVA API çağrısı yapılıyor (attempt {attempt}/{self.retry_count + 1})...")
                logger.info(f"🔗 URL: {self.url}")
                logger.info(f"🔒 TLS: Minimum 1.2 enforced")
                
                response = self.session.post(
                    self.url,
                    data=soap_xml,
                    headers={
                        'Content-Type': 'text/xml; charset=utf-8',
                        'Accept': 'text/xml',
                        'SOAPAction': '"http://tempuri.org/InsertEntDtAsn"'
                    },
                    timeout=self.timeout
                )
                
                logger.info(f"📥 CEVA API yanıtı alındı: HTTP Status={response.status_code}")
                
                if response.status_code == 200:
                    return self._parse_response(response.text)
                else:
                    logger.error(f"❌ CEVA API HTTP Hatası: {response.status_code}")
                    logger.error(f"📄 Response Body:\n{response.text}")
                    
                    if attempt <= self.retry_count:
                        logger.info(f"🔄 Tekrar deneniyor ({attempt}/{self.retry_count})...")
                        continue
                    
                    return ASNResponse(
                        successful=False,
                        result_description=f"HTTP {response.status_code}: CEVA servisi yanıt vermedi",
                        raw_response=response.text[:1000]
                    )
                    
            except requests.Timeout:
                logger.error(f"CEVA API timeout (attempt {attempt})")
                if attempt <= self.retry_count:
                    continue
                return ASNResponse(
                    successful=False,
                    result_description=f"CEVA servisi zaman aşımına uğradı ({self.timeout}s)"
                )
                
            except Exception as e:
                logger.error(f"CEVA API hatası: {e}")
                if attempt <= self.retry_count:
                    continue
                return ASNResponse(
                    successful=False,
                    result_description=f"CEVA servisi hatası: {str(e)}"
                )
        
        return ASNResponse(
            successful=False,
            result_description="CEVA servisi yanıt vermedi (tüm denemeler başarısız)"
        )

    def _build_soap_request(self, trip_code: str, asn_details: List[ASNItemDetail]) -> str:
        """
        Build SOAP XML request for InsertEntDtAsn (YENİ YAPI)
        
        Args:
            trip_code: Sefer kodu
            asn_details: VIN detayları (SIRALI!)
            
        Returns:
            SOAP XML string
        """
        # SOAP Envelope with soapenv and tem namespaces
        soap_env = etree.Element(
            '{http://schemas.xmlsoap.org/soap/envelope/}Envelope',
            nsmap={
                'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
                'tem': 'http://tempuri.org/'
            }
        )
        
        # SOAP Header (empty)
        etree.SubElement(soap_env, '{http://schemas.xmlsoap.org/soap/envelope/}Header')
        
        # SOAP Body
        soap_body = etree.SubElement(soap_env, '{http://schemas.xmlsoap.org/soap/envelope/}Body')
        
        # tem:InsertEntDtAsn
        insert_asn = etree.SubElement(soap_body, '{http://tempuri.org/}InsertEntDtAsn')
        
        # tem:dtasnItem container
        dtasn_item_container = etree.SubElement(insert_asn, '{http://tempuri.org/}dtasnItem')
        
        # tem:DTASNItem
        dtasn_item = etree.SubElement(dtasn_item_container, '{http://tempuri.org/}DTASNItem')
        
        # tem:TripCode
        trip_code_elem = etree.SubElement(dtasn_item, '{http://tempuri.org/}TripCode')
        trip_code_elem.text = trip_code
        
        # tem:SupplierCode
        supplier_code_elem = etree.SubElement(dtasn_item, '{http://tempuri.org/}SupplierCode')
        supplier_code_elem.text = self.supplier_code
        
        # tem:UserId
        user_id_elem = etree.SubElement(dtasn_item, '{http://tempuri.org/}UserId')
        user_id_elem.text = str(self.user_id)
        
        # tem:DTASNItemDetails container
        dtasn_details_container = etree.SubElement(dtasn_item, '{http://tempuri.org/}DTASNItemDetails')
        
        # Add each VIN detail IN ORDER
        for detail in asn_details:
            dtasn_detail = etree.SubElement(dtasn_details_container, '{http://tempuri.org/}DTASNItemDetail')
            
            # tem:DollyNumber (ÇOK ÖNEMLİ: Bu DollyOrderNo - veritabanındaki benzersiz dolly sipariş numarası!)
            if detail.dolly_number:
                dolly_elem = etree.SubElement(dtasn_detail, '{http://tempuri.org/}DollyNumber')
                dolly_elem.text = str(detail.dolly_number)  # DollyOrderNo gönderiliyor (örn: 54920, 54921...)
            
            # tem:VINNumber (required)
            vin_elem = etree.SubElement(dtasn_detail, '{http://tempuri.org/}VINNumber')
            vin_elem.text = detail.vin_number
            
            # tem:PartNumber (required)
            part_elem = etree.SubElement(dtasn_detail, '{http://tempuri.org/}PartNumber')
            part_elem.text = detail.part_number
            
            # tem:QTY (required)
            qty_elem = etree.SubElement(dtasn_detail, '{http://tempuri.org/}QTY')
            qty_elem.text = str(detail.qty)
            
            # tem:ProcessTime (required) - YYYY-MM-DD format
            process_time_elem = etree.SubElement(dtasn_detail, '{http://tempuri.org/}ProcessTime')
            process_time_elem.text = detail.process_time.strftime('%Y-%m-%d')
            
            # tem:WaybillNumber (required) - İrsaliye numarası
            waybill_elem = etree.SubElement(dtasn_detail, '{http://tempuri.org/}WaybillNumber')
            waybill_elem.text = detail.waybill_number
            
            # tem:TripReasonCode (required) - Hata kodu
            trip_reason_elem = etree.SubElement(dtasn_detail, '{http://tempuri.org/}TripReasonCode')
            trip_reason_elem.text = detail.trip_reason_code
            
            # tem:DollyEye (required) - Dolly göz numarası
            dolly_eye_elem = etree.SubElement(dtasn_detail, '{http://tempuri.org/}DollyEye')
            dolly_eye_elem.text = str(detail.dolly_eye)
        
        # tem:userName (direkt, küçük harf)
        username_elem = etree.SubElement(insert_asn, '{http://tempuri.org/}userName')
        username_elem.text = self.username
        
        # tem:password (direkt, küçük harf)
        password_elem = etree.SubElement(insert_asn, '{http://tempuri.org/}password')
        password_elem.text = self.password
        
        # Convert to string
        xml_string = etree.tostring(
            soap_env, 
            pretty_print=True, 
            xml_declaration=True, 
            encoding='utf-8'
        ).decode('utf-8')
        
        logger.debug(f"SOAP Request XML:\n{xml_string}")
        
        return xml_string

    def _parse_response(self, response_xml: str) -> ASNResponse:
        """
        Parse CEVA SOAP response
        
        Expected format:
        <soap:Envelope>
          <soap:Body>
            <InsertEntDtAsnResponse>
              <InsertEntDtAsnResult>
                <Successful>true</Successful>
                <ResultDescription />
              </InsertEntDtAsnResult>
            </InsertEntDtAsnResponse>
          </soap:Body>
        </soap:Envelope>
        
        Args:
            response_xml: SOAP response XML string
            
        Returns:
            ASNResponse
        """
        try:
            # FULL XML LOG - Tüm response'u logla
            logger.info(f"📥 CEVA FULL Response XML:\n{response_xml}")
            
            # Parse XML
            root = etree.fromstring(response_xml.encode('utf-8'))
            
            # Define namespaces
            namespaces = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'ns': 'http://tempuri.org/'
            }
            
            # Find InsertEntDtAsnResult
            result = root.find('.//ns:InsertEntDtAsnResult', namespaces)
            
            if result is None:
                # LOG: Beklenen format bulunamadı
                logger.error("❌ CEVA Response Parse Hatası: InsertEntDtAsnResult bulunamadı!")
                logger.error(f"📄 Gelen XML yapısı:\n{response_xml}")
                
                return ASNResponse(
                    successful=False,
                    result_description="CEVA yanıtı beklenmeyen formatta - InsertEntDtAsnResult elementi bulunamadı",
                    raw_response=response_xml
                )
            
            # Extract Successful
            successful_elem = result.find('ns:Successful', namespaces)
            
            if successful_elem is None:
                # LOG: Successful elementi yok
                logger.error("❌ CEVA Response Parse Hatası: Successful elementi bulunamadı!")
                logger.error(f"📄 InsertEntDtAsnResult içeriği: {etree.tostring(result, encoding='unicode')}")
                
                return ASNResponse(
                    successful=False,
                    result_description="CEVA yanıtı beklenmeyen formatta - Successful elementi bulunamadı",
                    raw_response=response_xml
                )
            
            successful = successful_elem.text.lower() == 'true' if successful_elem.text else False
            
            # Extract ResultDescription
            desc_elem = result.find('ns:ResultDescription', namespaces)
            description = desc_elem.text if desc_elem is not None and desc_elem.text else ""
            
            # LOG SUCCESS or FAIL
            if successful:
                logger.info(f"✅ CEVA ASN BAŞARILI: Successful=true, Message='{description}'")
            else:
                logger.error(f"❌ CEVA ASN REDDEDİLDİ: Successful=false, Message='{description}'")
                logger.error(f"📄 Tam Response:\n{response_xml}")
            
            return ASNResponse(
                successful=successful,
                result_description=description or "İşlem tamamlandı",
                raw_response=response_xml
            )
            
        except Exception as e:
            # LOG: Parse exception
            logger.error(f"❌ CEVA Response Parse Exception: {e}")
            logger.error(f"📄 XML içeriği:\n{response_xml}")
            import traceback
            logger.error(f"🔍 Stack trace:\n{traceback.format_exc()}")
            
            return ASNResponse(
                successful=False,
                result_description=f"CEVA yanıtı işlenemedi: {str(e)}",
                raw_response=response_xml
            )

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test CEVA service connection
        
        Returns:
            (success, message) tuple
        """
        try:
            if not self.config.get('enabled', False):
                return False, "CEVA servisi config'de devre dışı"
            
            logger.info(f"Testing CEVA connection to {self.url}...")
            
            # Simple GET request to check if service is reachable
            response = requests.get(self.url, timeout=10)
            
            if response.status_code in [200, 405]:  # 405 is OK (GET not allowed but service is up)
                return True, f"CEVA servisi erişilebilir (HTTP {response.status_code})"
            else:
                return False, f"CEVA servisi yanıt vermedi (HTTP {response.status_code})"
                
        except Exception as e:
            logger.error(f"CEVA connection test failed: {e}")
            return False, f"CEVA servisi erişilemez: {str(e)}"
