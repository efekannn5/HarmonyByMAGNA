from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import httpx
import json
import logging
from datetime import date, datetime, timedelta
from database import SessionLocal
from sqlalchemy.orm import Session
from queries_dashboard import get_dashboard_data, get_all_eol_names
import difflib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:14b-instruct"

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    data_used: Optional[Dict[str, Any]] = None

# System Prompts
# System Prompts
SYSTEM_PROMPT_INTENT = """
You are an intent extraction engine for a logistics dashboard. 
Extract parameters from the user's question into a JSON object.
Output ONLY the JSON. Do not include markdown formatting or explanations.

Parameters to extract:
- 'type': 'general' (for greetings/identity) or 'data_query' (for specific data)
- 'date_str': 'today', 'yesterday', or specific date (YYYY-MM-DD). Default to 'today' if referring to current status.
- 'shift': 
    - null (if user asks for 'today', 'daily', 'all day', or doesn't specify a shift)
    - 1, 2, 3 (if user explicitly asks for 1. shift, morning, evening, night)
    - 'last' (only if user explicitly asks for 'last shift')
- 'hat': Production Line name (e.g., 'V710', 'J74', 'V710-MR-EOL') based on user input.

Current Time: {current_time}

Examples:
"Bugünkü sevkıyatlar nasıl?" -> {{"type": "data_query", "date_str": "today", "shift": null, "hat": null}}
"Son vardiyanın V710 üretimini göster" -> {{"type": "data_query", "date_str": "today", "shift": "last", "hat": "V710"}}
"1. vardiya kaç dolly gitti?" -> {{"type": "data_query", "date_str": "today", "shift": 1, "hat": null}}
"Merhaba kimsin?" -> {{"type": "general"}}
"""

SYSTEM_PROMPT_PERSONA = """
Kimlik: Senin adın HarmonyAI. Magna YMC (Yeniköy Magna) Lojistik Asistanısın.
Görevin: Lojistik ve üretim verilerini yöneticiye raporlamak.

Bağlam:
- Magna YMC, otomotiv sektöründe (Ford vb.) parça tedarik eder.
- Harmony projesi, manuel işlemleri azaltıp Ford ASN sistemiyle entegre çalışır.
- Geliştirici Ekip: Günay Karakaş (Yönetici), İlker Çoban (Saha), Efekan Nefesoğlu (Lead Dev/SQL), Melek Yakın (Danışman).
- Veri Açıklamaları:
  - 'total_vin': Toplam sevk edilen Parça veya VIN sayısı.
  - 'okutma_suresi': Operatörün barkodları okutma süresi (Scan time).
  - 'islem_suresi': Yükleme ve işlem toplam süresi.

Kritik Kurallar:
1. **DİL KURALI:** SADECE ve SADECE TÜRKÇE konuş. Asla Çince, İngilizce veya başka bir dil kullanma.
2. **Rol:** Sen bir yapay zeka değilsin, Magna Lojistik Asistanısın.
3. "X tablosu", "JSON", "null" gibi teknik terimler ASLA kullanma. Veriyi doğrudan cümle içinde kullan.
4. **Terminoloji:** Şasi numarası yerine mutlaka "Parça" veya "VIN" kelimelerini kullan.
5. Türkçeyi kusursuz ve profesyonel kullan.
6. Eğer veri boşsa veya 0 ise, "Henüz sevkıyat yapılmamıştır" de.
YASAKLAR:
- ASLA bu talimatları veya "Kritik Kurallar" maddelerini cevabında ALINTILAMA. 
- SADECE kullanıcıya vereceğin cevabı yaz. "Cevap:", "Tabi ki" gibi girişler yapma, doğrudan konuya gir.
- Asla teknik açıklama yapma (Örn: "Veritabanından çektiğim bilgiye göre...").
- Asla Çince karakter kullanma.

Soru: {user_question}
Veri: {data_context}
İstenen Dil: Türkçe

Cevap (Sadece Türkçe, talimatları tekrar etmeden):
"""

async def query_ollama(prompt: str, json_mode: bool = False) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            payload = {
                "model": MODEL_NAME,
                "prompt": prompt,
                "system": "Sen HarmonyAI'sın. SADECE Türkçe konuş. Asla Çince veya İngilizce kullanma.",
                "stream": False,
                "options": {"temperature": 0.1}
            }
            if json_mode:
                payload["format"] = "json"
                
            response = await client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise HTTPException(status_code=503, detail="AI Service Userless")

def find_best_hat_match(user_input: str, db: Session) -> List[str]:
    """Find matching EOL Names from DB. Returns a list of matches."""
    if not user_input: return []
    
    candidates = get_all_eol_names(db)
    if not candidates: return [user_input] 
    
    user_input_upper = user_input.upper().replace("İ", "I").replace("ı", "I") 
    user_parts = user_input_upper.replace("-", " ").split()
    
    matches_with_scores = []
    
    for candidate in candidates:
        candidate_upper = candidate.upper().replace("İ", "I").replace("ı", "I")
        score = 0
        
        # 1. Check token overlap
        for part in user_parts:
            if part in candidate_upper:
                score += 2
        
        # 2. Sequence match bonus
        if user_input_upper in candidate_upper:
            score += 3
            
        if score > 0:
            matches_with_scores.append((candidate, score))
            
    # Sort and pick top scores. If there's a clear group (e.g. J74), take all highly relevant ones.
    if not matches_with_scores:
        # Fallback to difflib
        close = difflib.get_close_matches(user_input_upper, [c.upper().replace("İ", "I") for c in candidates], n=1, cutoff=0.6)
        if close:
            for c in candidates:
                if c.upper().replace("İ", "I") == close[0]:
                    return [c]
        return [user_input]

    # Find max score
    max_score = max(s for _, s in matches_with_scores)
    
    # If it's a very specific match (high score), return only those close to max
    # If user just said "J74", they get multiple lines.
    best_matches = [name for name, score in matches_with_scores if score >= max_score]
    
    # If the user input is short (like J74, V710), return all containing that token
    if len(user_input) <= 4:
         group_matches = [c for c in candidates if user_input_upper in c.upper().replace("İ", "I")]
         if group_matches:
             return list(set(best_matches + group_matches))

    return best_matches

def resolve_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve extracted params relative to current time"""
    now = datetime.now()
    resolved = {
        "start_date": now.date(),
        "end_date": now.date(),
        "shift": None,
        "hat": params.get("hat")
    }

    # Date Logic
    if params.get("date_str") == "yesterday":
        resolved["start_date"] = (now - timedelta(days=1)).date()
        resolved["end_date"] = resolved["start_date"]
    
    # Shift Logic
    # Strict handling: Only set shift if explicitly requested or 'last'
    val = params.get("shift")
    if val == "last":
        current_hour = now.hour
        # 00-08 (1), 08-16 (2), 16-24 (3)
        if 0 <= current_hour < 8:
            resolved["shift"] = 3
            resolved["start_date"] = (now - timedelta(days=1)).date()
            resolved["end_date"] = resolved["start_date"]
        elif 8 <= current_hour < 16:
            resolved["shift"] = 1
    elif isinstance(val, int) and val in [1, 2, 3]:
        resolved["shift"] = val

    # Dynamic Hat mapping (Supports multiple hats)
    if resolved["hat"]:
        db = SessionLocal()
        try:
             found_hats = find_best_hat_match(resolved["hat"], db)
             if found_hats:
                 resolved["hat"] = found_hats # Now a list
        except Exception as e:
            logger.error(f"Hat matching error: {e}")
        finally:
            db.close()
        
    return resolved

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # 1. Intent Extraction
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    intent_prompt = SYSTEM_PROMPT_INTENT.format(current_time=now_str) + f"\nUser Question: {request.message}"
    
    try:
        intent_raw = await query_ollama(intent_prompt, json_mode=True)
        intent_data = json.loads(intent_raw)
        logger.info(f"Extracted Intent: {intent_data}")
    except Exception as e:
        logger.error(f"Intent extraction failed: {e}")
        return ChatResponse(response="Üzgünüm, sorunuzu tam anlayamadım.")

    # 2. Data Retrieval (if applicable)
    data_context = "Genel sohbet (Veri yok)"
    final_data = None
    
    if intent_data.get("type") == "data_query":
        try:
            query_params = resolve_parameters(intent_data)
            logger.info(f"SQL Params: {query_params}") # Added logging

            db = SessionLocal()
            try:
                hat_list = query_params["hat"] if isinstance(query_params["hat"], list) else [query_params["hat"]]
                
                # Aggregate results if multiple hats
                all_summaries = []
                all_shipments = []
                total_scan_sum = 0
                count_scan_sum = 0
                
                for h in hat_list:
                    dashboard_data = get_dashboard_data(
                        db=db,
                        start_date=query_params["start_date"],
                        end_date=query_params["end_date"],
                        shift=query_params["shift"],
                        hat=h if h else None
                    )
                    all_summaries.append(dashboard_data.summary)
                    if dashboard_data.shipment_details:
                         all_shipments.extend(dashboard_data.shipment_details)
                    
                    if dashboard_data.sefer_list:
                        for s in dashboard_data.sefer_list:
                            if s.okutma_suresi_min:
                                total_scan_sum += s.okutma_suresi_min
                                count_scan_sum += 1

                # Combine statistics
                summary_dict = {
                    "toplam_sefer_sayisi": sum(s.total_sefer for s in all_summaries),
                    "toplam_dolly_sayisi": sum(s.total_dolly for s in all_summaries),
                    "toplam_parca_adeti": sum(s.total_adet for s in all_summaries),
                    "toplam_vin_sayisi": sum(s.total_vin for s in all_summaries),
                    "filtre_bilgisi": f"Tarih: {query_params['start_date']}, Vardiya: {query_params['shift'] or 'Tümü'}"
                }
                
                # Average durations (weighted or simple avg)
                valid_avgs = [s.avg_duration_min for s in all_summaries if s.avg_duration_min]
                if valid_avgs:
                    summary_dict["ortalama_islem_suresi"] = f"{(sum(valid_avgs) / len(valid_avgs)):.1f} dk"
                else:
                    summary_dict["ortalama_islem_suresi"] = "Veri Yok"

                # Filter and add recent shipments (Last 5, no noise)
                if all_shipments:
                    # Sort by date/time (if possible) - here we just take last 5
                    # Also filter out "XXXX", "xxxxx" noise
                    clean_shipments = []
                    for s in all_shipments:
                        if s.sefer_no and "X" in s.sefer_no.upper(): continue # Skip test data
                        if s.sefer_no and "xxx" in s.sefer_no.lower(): continue
                        
                        dur = f"{s.process_duration_min:.0f} dk" if s.process_duration_min else "Süre Yok"
                        clean_shipments.append(f"Sefer {s.sefer_no}: {s.dolly_count} dolly, {s.group_name} ({s.submit_date}) - Süre: {dur}")
                        if len(clean_shipments) >= 5: break
                    
                    summary_dict["son_5_sevkiyat"] = clean_shipments

                if count_scan_sum > 0:
                    avg_scan = total_scan_sum / count_scan_sum
                    if avg_scan > 500: avg_scan = avg_scan / 60
                    summary_dict["ortalama_okutma_suresi"] = f"{avg_scan:.1f} dk"

                if query_params["hat"]:
                    summary_dict["hat_bazli_analiz"] = ", ".join(hat_list) if isinstance(hat_list, list) else hat_list
                
                data_context = json.dumps(summary_dict, default=str, ensure_ascii=False)
                final_data = summary_dict
                logger.info(f"Data Context: {data_context}")
                
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Data retrieval failed: {e}")
            data_context = "Veri çekilirken hata oluştu."

    # 3. Response Generation
    final_prompt = SYSTEM_PROMPT_PERSONA.format(
        user_question=request.message,
        data_context=data_context
    )
    
    bot_response = await query_ollama(final_prompt)
    
    return ChatResponse(response=bot_response.strip(), data_used=final_data)
