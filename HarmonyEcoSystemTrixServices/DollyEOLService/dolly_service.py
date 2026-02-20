import json
import logging
from pathlib import Path
from datetime import datetime

import pyodbc
from flask import Flask, request, jsonify

CONFIG_PATH = Path(__file__).parent / "config.json"

# ----------------- Config & Logging ----------------- #

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def setup_logging(base_dir: str):
    """Ayın tarihine göre klasör açıp log dosyasını oraya yazar (YYYY-MM formatında)."""
    today_str = datetime.now().strftime("%Y-%m")
    log_dir = Path(base_dir) / today_str
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "service.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    logging.info("Logging initialized. Log file: %s", log_file)


def build_connection_string(db_cfg: dict) -> str:
    return (
        f"DRIVER={db_cfg['driver']};"
        f"SERVER={db_cfg['server']};"
        f"DATABASE={db_cfg['database']};"
        f"UID={db_cfg['username']};"
        f"PWD={db_cfg['password']};"
        "TrustServerCertificate=yes;"
    )

# ----------------- DB İşlemleri ----------------- #

def map_json_to_db_columns(payload: dict, mapping_cfg: dict) -> dict:
    """
    mapping_cfg: {"RECEIPTID": "EOLDollyBarcode", ...}
    return: {"EOLDollyBarcode": 6743700, ...}
    Eksik alanlar atlanır, sadece gelen alanlar map edilir (esnek sistem).
    """
    mapped = {}
    for src_field, dst_column in mapping_cfg.items():
        if src_field in payload:
            mapped[dst_column] = payload[src_field]
            logging.debug(f"Mapped: {src_field} -> {dst_column} = {payload[src_field]}")
        else:
            logging.warning(f"Alan JSON'da yok, atlandı: {src_field}")

    # DollyNo geldiyse ve EOLDollyBarcode boşsa, barcode'a da aynı değeri yaz
    if "DollyNo" in mapped and "EOLDollyBarcode" not in mapped:
        mapped["EOLDollyBarcode"] = mapped["DollyNo"]
        logging.debug("EOLDollyBarcode eksikti, DollyNo değeri ile dolduruldu.")
    return mapped


def upsert_dolly_eol_info(mapped_values: dict, db_cfg: dict):
    """
    primary_key_column üzerinden:
      - varsa UPDATE
      - yoksa INSERT yapar
    """
    table = db_cfg["target_table"]
    key_col = db_cfg["primary_key_column"]

    if key_col not in mapped_values:
        raise ValueError(f"Primary key alanı '{key_col}' mapped_values içinde yok.")

    columns = list(mapped_values.keys())
    non_key_cols = [c for c in columns if c != key_col]

    # Dinamik SQL (parametreler ? ile)
    update_set_clause = ", ".join(f"{col} = ?" for col in non_key_cols)
    insert_columns_clause = ", ".join(columns)
    insert_values_placeholders = ", ".join("?" for _ in columns)

    sql = f"""
IF EXISTS (SELECT 1 FROM {table} WHERE {key_col} = ?)
    UPDATE {table}
    SET {update_set_clause}
    WHERE {key_col} = ?;
ELSE
BEGIN
    IF COLUMNPROPERTY(OBJECT_ID('{table}'), '{key_col}', 'IsIdentity') = 1
    BEGIN
        SET IDENTITY_INSERT {table} ON;
        INSERT INTO {table} ({insert_columns_clause})
        VALUES ({insert_values_placeholders});
        SET IDENTITY_INSERT {table} OFF;
    END
    ELSE
    BEGIN
        INSERT INTO {table} ({insert_columns_clause})
        VALUES ({insert_values_placeholders});
    END
END
"""

    # Parametre sırası: EXISTS key, UPDATE set values..., WHERE key, INSERT (identity on) values..., INSERT (identity off) values...
    params = []
    params.append(mapped_values[key_col])                 # EXISTS
    params.extend(mapped_values[c] for c in non_key_cols) # UPDATE SET
    params.append(mapped_values[key_col])                 # UPDATE WHERE
    insert_values = [mapped_values[c] for c in columns]
    params.extend(insert_values)                          # INSERT (IDENTITY ON) values
    params.extend(insert_values)                          # INSERT (IDENTITY OFF) values

    conn_str = build_connection_string(db_cfg)
    logging.debug("Connecting to SQL Server...")
    logging.debug(f"SQL: {sql}")
    logging.debug(f"Params: {params}")
    
    try:
        with pyodbc.connect(conn_str) as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
        logging.info(
            "✅ DB upsert OK. Table=%s, %s=%s, Kolonlar=%s",
            table, key_col, mapped_values[key_col], list(mapped_values.keys())
        )
    except Exception as db_error:
        logging.error(f"❌ DB upsert HATA! Table={table}, Key={key_col}={mapped_values.get(key_col)}")
        logging.error(f"SQL: {sql}")
        logging.error(f"Params: {params}")
        logging.exception(f"Detay: {db_error}")
        raise

# ----------------- Backup INSERT İşlemi ----------------- #

def insert_backup_dolly_eol_info(mapped_values: dict, db_cfg: dict, mapping_name: str = "backup"):
    """
    Backup tablosuna direkt INSERT yapar (primary key kontrolü yok)
    """
    backup_table = db_cfg.get("backup_table")
    if not backup_table:
        logging.warning("⚠️ Backup tablo tanımlı değil, backup atlandı")
        return

    if len(mapped_values) == 0:
        logging.warning(f"⚠️ Backup için mapped_values boş, atlandı")
        return

    columns = list(mapped_values.keys())
    insert_columns_clause = ", ".join(columns)
    insert_values_placeholders = ", ".join("?" for _ in columns)

    sql = f"""
INSERT INTO {backup_table} ({insert_columns_clause})
VALUES ({insert_values_placeholders});
"""

    params = [mapped_values[c] for c in columns]

    conn_str = build_connection_string(db_cfg)
    logging.debug(f"Backup INSERT - SQL: {sql}")
    logging.debug(f"Backup INSERT - Params: {params}")
    
    try:
        with pyodbc.connect(conn_str) as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
        logging.info(
            f"✅ Backup INSERT OK. Table={backup_table}, Kolonlar={list(mapped_values.keys())}"
        )
    except Exception as db_error:
        logging.error(f"❌ Backup INSERT HATA! Table={backup_table}")
        logging.error(f"SQL: {sql}")
        logging.error(f"Params: {params}")
        logging.exception(f"Detay: {db_error}")
        # Backup hatası ana işlemi durdurmasın, sadece logla

# ----------------- Flask Uygulaması ----------------- #

config = load_config()
setup_logging(config["logging"]["base_dir"])

app = Flask(__name__)
db_cfg = config["database"]
mapping_cfg = config["mapping"]
mapping2_cfg = config.get("mapping2", config["mapping"])  # mapping2 yoksa mapping kullan
endpoint = config["server"].get("endpoint", "/dolly-eol")


@app.route(endpoint, methods=["POST"])
def handle_dolly_eol():
    client_ip = request.remote_addr
    raw_data = request.data.decode("utf-8", errors="ignore")
    logging.info(f"📥 İstek geldi [{client_ip}]: {raw_data}")

    try:
        payload = request.get_json(silent=True)
        if payload is None:
            logging.error(f"❌ Geçersiz JSON formatı. Body: {raw_data}")
            response = {"RECEIPTID": "00000", "STATUS": 0}
            logging.error(f"📤 Response [{client_ip}]: {response}")
            return jsonify(response)

        # RECEIPTID kontrolü - MUTLAKA OLMALI
        receipt_id = payload.get("RECEIPTID")
        if receipt_id is None or receipt_id == "":
            logging.error(f"❌ RECEIPTID alanı yok veya boş! Payload: {payload}")
            response = {"RECEIPTID": "00000", "STATUS": 0}
            logging.error(f"📤 Response [{client_ip}]: {response}")
            return jsonify(response)
        logging.info(f"🔄 İşleniyor: RECEIPTID={receipt_id}, Toplam {len(payload)} alan")
        
        # JSON -> DB kolon eşlemesi (sadece olan alanlar)
        mapped_values = map_json_to_db_columns(payload, mapping_cfg)
        
        if len(mapped_values) == 0:
            logging.warning(f"⚠️ Hiçbir alan eşleşmedi ama STATUS=1 dönüyoruz")
        else:
            logging.info(f"✅ Mapping başarılı: {len(mapped_values)} kolon eşleşti")
            # 1) Ana tabloya yaz (UPSERT)
            try:
                upsert_dolly_eol_info(mapped_values, db_cfg)
                logging.info(f"✅ DB işlem başarılı: RECEIPTID={receipt_id}")
            except Exception as db_error:
                # DB hatası olsa bile karşı tarafa başarılı dön
                logging.error(f"❌ DB HATASI (Karşı tarafa yine de STATUS=1 dönüyoruz): RECEIPTID={receipt_id}")
                logging.exception(f"DB Hata Detay: {db_error}")
            
            # 2) Backup tablosuna yaz (INSERT) - mapping2 kullan
            try:
                mapped_values_backup = map_json_to_db_columns(payload, mapping2_cfg)
                insert_backup_dolly_eol_info(mapped_values_backup, db_cfg, "backup")
                logging.info(f"✅ Backup işlem başarılı: RECEIPTID={receipt_id}")
            except Exception as backup_error:
                # Backup hatası ana işlemi etkilemesin
                logging.error(f"❌ BACKUP HATASI (Ana işlem devam ediyor): RECEIPTID={receipt_id}")
                #logging.exception(f"Backup Hata Detay: {backupafa yine de STATUS=1 dönüyoruz): RECEIPTID={receipt_id}")
                logging.exception(f"DB Hata Detay: {db_error}")

    except Exception as exc:
        # Herhangi bir hata olsa bile karşı tarafa başarılı dön
        logging.error(f"❌ GENEL HATA (Karşı tarafa yine de STATUS=1 dönüyoruz): RECEIPTID={receipt_id}")
        logging.exception(f"Hata Detay: {exc}")

    # Her durumda başarılı response dön
    response = {"RECEIPTID": receipt_id, "STATUS": 1}
    logging.info(f"📤 Response [{client_ip}]: {response}")
    return jsonify(response)


if __name__ == "__main__":
    srv = config["server"]
    host = srv.get("host", "0.0.0.0")
    port = int(srv.get("port", 5000))
    logging.info("Service starting on %s:%s endpoint=%s", host, port, endpoint)
    app.run(host=host, port=port)
