from dataclasses import asdict
from typing import List, Optional
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from flask_login import login_required, current_user

from ..extensions import db
from ..services import DollyService
from ..services.realtime_service import RealtimeService
from ..utils.forklift_auth import (
    require_forklift_auth,
    get_current_forklift_user,
    create_forklift_session,
    logout_forklift_session
)

api_bp = Blueprint("api", __name__)


def _service() -> DollyService:
    config = current_app.config.get("APP_CONFIG", {})
    return DollyService(config)


@api_bp.get("/health")
def health_check():
    return jsonify({"status": "ok", "app": current_app.config.get("APP_CONFIG", {}).get("app", {}).get("name")})


# ==================== FORKLIFT AUTHENTICATION ====================

@api_bp.post("/forklift/login")
def forklift_login():
    """Forklift operator login with barcode scan
    
    Request:
    {
        "operatorBarcode": "EMP12345",
        "operatorName": "Mehmet Yılmaz",  # Optional, can be looked up from barcode
        "deviceId": "android-device-123"  # Optional
    }
    
    Response - Normal User:
    {
        "success": true,
        "sessionToken": "eyJhbGc...",
        "operatorName": "Mehmet Yılmaz",
        "operatorBarcode": "EMP12345",
        "expiresAt": "2025-12-23T16:00:00Z",
        "message": "Hoş geldiniz Mehmet Yılmaz",
        "isAdmin": false,
        "role": "forklift"
    }
    
    Response - Admin User:
    {
        "success": true,
        "sessionToken": "eyJhbGc...",
        "operatorName": "Admin User",
        "operatorBarcode": "ADMIN001",
        "expiresAt": "2025-12-23T16:00:00Z",
        "message": "Hoş geldiniz Admin User",
        "isAdmin": true,
        "role": "admin"
    }
    """
    payload = request.get_json(force=True, silent=True) or {}
    
    operator_barcode = payload.get("operatorBarcode")
    if not operator_barcode:
        return jsonify({
            "success": False,
            "message": "Operatör barkodu gerekli"
        }), 400
    
    # Get or validate operator name
    operator_name = payload.get("operatorName")
    device_id = payload.get("deviceId")
    
    # Check if user is admin by barcode pattern or UserAccount lookup
    is_admin = False
    role = 'forklift'
    
    # PRIORITY 1: Check admin barcode patterns (fast, no DB required)
    if any(operator_barcode.upper().startswith(prefix) for prefix in ['ADMIN', 'ADM', 'SUPERUSER', 'SU']):
        is_admin = True
        role = 'admin'
        if not operator_name:
            operator_name = f"Admin_{operator_barcode}"
        
        current_app.logger.info(f"✅ Admin detected by prefix: {operator_barcode}")
    
    # PRIORITY 2: Fallback - Check TerminalBarcodeSession by Token
    elif not is_admin:
        try:
            from ..models.user import UserAccount, UserRole, TerminalBarcodeSession
            
            # Find user by TerminalBarcodeSession Token (primary method for terminal login)
            session = TerminalBarcodeSession.query.filter_by(Token=operator_barcode).first()
            
            user = None
            if session and session.user:
                user = session.user
                current_app.logger.info(f"✅ User found via TerminalBarcodeSession: {session.user.Username}")
            else:
                # Fallback: try Username if not found by session token
                user = UserAccount.query.filter_by(Username=operator_barcode, IsActive=True).first()
                if user:
                    current_app.logger.info(f"✅ User found via Username: {user.Username}")
            
            if user and user.role:
                role_name = user.role.Name.lower()
                if role_name in ['admin', 'administrator', 'superuser']:
                    is_admin = True
                    role = 'admin'
                else:
                    role = role_name
                
                # Use DisplayName if available, fallback to Username
                if not operator_name:
                    operator_name = user.DisplayName or user.Username
                    
                current_app.logger.info(f"✅ User authenticated: {operator_name} (input: {operator_barcode})")
            else:
                # User not found in database - REJECT LOGIN
                current_app.logger.warning(f"❌ Geçersiz barkod/token: {operator_barcode}")
                return jsonify({
                    'success': False,
                    'message': f'Geçersiz barkod/token. Kullanıcı bulunamadı: {operator_barcode}'
                }), 401
        except Exception as e:
            current_app.logger.error(f"UserAccount lookup error: {e}")
            return jsonify({
                'success': False,
                'message': f'Veritabanı hatası: {str(e)}'
            }), 500
    
    # At this point, operator_name should be set (either by admin check or DB lookup)
    if not operator_name:
        current_app.logger.error(f"❌ operator_name bulunamadı: {operator_barcode}")
        return jsonify({
            'success': False,
            'message': 'Kullanıcı doğrulaması başarısız'
        }), 401
    
    try:
        # Create session with admin flag and role
        session = create_forklift_session(
            operator_barcode=operator_barcode,
            operator_name=operator_name,
            device_id=device_id,
            session_hours=8,  # 8 hours validity
            is_admin=is_admin,
            role=role
        )
        
        # Log to audit
        from ..services.audit_service import AuditService
        audit = AuditService()
        audit.log(
            action="forklift.login",
            resource="session",
            resource_id=str(session.Id),
            actor_name=operator_name,
            metadata={
                "barcode": operator_barcode,
                "deviceId": device_id,
                "isAdmin": is_admin,
                "role": role
            }
        )
        
        return jsonify({
            "success": True,
            "sessionToken": session.SessionToken,
            "operatorName": session.OperatorName,
            "operatorBarcode": session.OperatorBarcode,
            "expiresAt": session.ExpiresAt.isoformat(),
            "message": f"Hoş geldiniz {operator_name}",
            "isAdmin": is_admin,
            "role": role
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Forklift login error: {e}")
        return jsonify({
            "success": False,
            "message": "Giriş yapılamadı. Lütfen tekrar deneyin."
        }), 500


@api_bp.post("/forklift/logout")
@require_forklift_auth
def forklift_logout():
    """Forklift operator logout
    
    Headers:
        Authorization: Bearer <sessionToken>
    
    Response:
    {
        "success": true,
        "message": "Çıkış yapıldı"
    }
    """
    session = get_current_forklift_user()
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if logout_forklift_session(token):
        # Log to audit
        from ..services.audit_service import AuditService
        audit = AuditService()
        audit.log(
            action="forklift.logout",
            resource="session",
            actor_name=session,
            metadata={}
        )
        
        return jsonify({
            "success": True,
            "message": "Çıkış yapıldı. Güle güle!"
        }), 200
    else:
        return jsonify({
            "success": False,
            "message": "Oturum bulunamadı"
        }), 404


@api_bp.get("/forklift/session/validate")
@require_forklift_auth
def validate_session():
    """Validate current forklift session
    
    Headers:
        Authorization: Bearer <sessionToken>
    
    Response:
    {
        "valid": true,
        "operatorName": "Mehmet Yılmaz",
        "expiresAt": "2025-11-26T23:30:00Z"
    }
    """
    from ..utils.forklift_auth import get_current_forklift_session
    session = get_current_forklift_session()
    
    return jsonify({
        "valid": True,
        "operatorName": session.OperatorName,
        "operatorBarcode": session.OperatorBarcode,
        "loginAt": session.LoginAt.isoformat(),
        "expiresAt": session.ExpiresAt.isoformat()
    }), 200


@api_bp.get("/groups")
def list_groups():
    groups = _service().list_groups()
    return jsonify([asdict(group) for group in groups])


@api_bp.get("/group-sequences")
def list_group_sequences():
    sequences = _service().list_group_sequences()
    return jsonify(
        [
            {
                "definition": asdict(sequence.definition),
                "queue": [asdict(entry) for entry in sequence.queue],
            }
            for sequence in sequences
        ]
    )


@api_bp.get("/groups/<vin_no>")
def group_by_vin(vin_no: str):
    group = _service().group_by_vin(vin_no)
    if not group:
        return jsonify({"message": "Group not found"}), 404
    return jsonify(asdict(group))


@api_bp.post("/groups/<dolly_no>/ack")
def acknowledge_group(dolly_no: str):
    payload = request.get_json(silent=True) or {}
    terminal_user = payload.get("terminalUser", "unknown")
    success = _service().acknowledge_group(dolly_no, terminal_user)
    if not success:
        return jsonify({"message": "Group not found"}), 404
    return jsonify({"status": "acknowledged", "dollyNo": dolly_no})


@api_bp.get("/holds")
def list_hold_entries():
    status = request.args.get("status")
    entries = _service().list_hold_entries(status=status)
    return jsonify([asdict(entry) for entry in entries])


# ==================== FORKLIFT OPERATIONS ====================
# All forklift endpoints require authentication

@api_bp.post("/forklift/scan")
@require_forklift_auth
def forklift_scan_dolly():
    """Forklift scans a dolly barcode (step 1: loading to truck)
    
    Headers:
        Authorization: Bearer <sessionToken>
    
    Request:
    {
        "dollyNo": "DL-5170427",
        "loadingSessionId": "LOAD_20251126_MEHMET",  # Optional, auto-generated if not provided
        "barcode": "BARCODE123"  # Optional, for validation
    }
    """
    payload = request.get_json(force=True, silent=True) or {}
    dolly_no = payload.get("dollyNo")
    if not dolly_no:
        return jsonify({"message": "dollyNo is required"}), 400
    
    # Get authenticated user from session
    forklift_user = get_current_forklift_user()
    loading_session_id = payload.get("loadingSessionId")  # Group multiple scans
    barcode = payload.get("barcode")
    
    try:
        entry = _service().forklift_scan_dolly(
            dolly_no=dolly_no,
            forklift_user=forklift_user,
            loading_session_id=loading_session_id,
            barcode=barcode
        )
        return jsonify(asdict(entry)), 201
    except ValueError as exc:
        return jsonify({"error": str(exc), "retryable": True}), 400
    except RuntimeError as exc:
        return jsonify({"error": str(exc), "retryable": False}), 500
    except Exception as exc:
        return jsonify({"error": "Beklenmeyen hata", "message": str(exc), "retryable": False}), 500


@api_bp.post("/forklift/remove-last")
@require_forklift_auth
def forklift_remove_last_dolly():
    """Remove last scanned dolly from loading session (LIFO - Last In First Out)
    
    Headers:
        Authorization: Bearer <sessionToken>
    
    Request:
    {
        "loadingSessionId": "LOAD_20251126_MEHMET",
        "dollyBarcode": "BARCODE123"  # Barcode to verify correct dolly
    }
    
    Response:
    {
        "dollyNo": "DL-5170427",
        "vinNo": "VIN123",
        "scanOrder": 15,
        "removedAt": "2025-11-26T10:30:00"
    }
    """
    payload = request.get_json(force=True, silent=True) or {}
    loading_session_id = payload.get("loadingSessionId")
    dolly_barcode = payload.get("dollyBarcode")
    
    if not loading_session_id:
        return jsonify({"message": "loadingSessionId is required"}), 400
    if not dolly_barcode:
        return jsonify({"message": "dollyBarcode is required"}), 400
    
    # Get authenticated user from session
    forklift_user = get_current_forklift_user()
    
    try:
        result = _service().forklift_remove_last_dolly(
            loading_session_id=loading_session_id,
            dolly_barcode=dolly_barcode,
            forklift_user=forklift_user
        )
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": str(exc), "retryable": True}), 400
    except RuntimeError as exc:
        return jsonify({"error": str(exc), "retryable": False}), 500
    except Exception as exc:
        return jsonify({"error": "Beklenmeyen hata", "message": str(exc), "retryable": False}), 500


@api_bp.post("/forklift/complete-loading")
@require_forklift_auth
def forklift_complete_loading():
    """Forklift completes loading session (step 2: all dollys loaded to truck)
    
    Headers:
        Authorization: Bearer <sessionToken>
    
    Request:
    {
        "loadingSessionId": "LOAD_20251126_MEHMET"
    }
    """
    payload = request.get_json(force=True, silent=True) or {}
    loading_session_id = payload.get("loadingSessionId")
    if not loading_session_id:
        return jsonify({"message": "loadingSessionId is required"}), 400
    
    # Get authenticated user from session
    forklift_user = get_current_forklift_user()
    
    try:
        result = _service().forklift_complete_loading(
            loading_session_id=loading_session_id,
            forklift_user=forklift_user
        )
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": str(exc), "retryable": True}), 400
    except RuntimeError as exc:
        return jsonify({"error": str(exc), "retryable": False}), 500
    except Exception as exc:
        return jsonify({"error": "Beklenmeyen hata", "message": str(exc), "retryable": False}), 500


@api_bp.get("/forklift/sessions")
@require_forklift_auth
def list_forklift_sessions():
    """List all loading sessions (active and completed)
    
    Headers:
        Authorization: Bearer <sessionToken>
    
    Query Params:
        ?status=scanned|loading_completed|completed
    """
    status = request.args.get("status")  # scanned, loading_completed, etc.
    sessions = _service().list_loading_sessions(status=status)
    return jsonify(sessions)


# LEGACY endpoint - keep for backward compatibility
@api_bp.post("/groups/<dolly_no>/hold")
def enqueue_hold_entry(dolly_no: str):
    """DEPRECATED: Use /forklift/scan instead"""
    payload = request.get_json(force=True, silent=True) or {}
    vin_no = payload.get("vinNo")
    if not vin_no:
        return jsonify({"message": "vinNo is required"}), 400
    terminal_user = payload.get("terminalUser")
    metadata = payload.get("metadata") or {}
    try:
        entry = _service().enqueue_hold_entry(dolly_no, vin_no, terminal_user, metadata)
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    return jsonify(asdict(entry)), 201


# Web Operator Shipment endpoints
@api_bp.get("/operator/pending-shipments")
def list_pending_shipments():
    """List all loading sessions waiting for operator to process"""
    shipments = _service().list_pending_shipments()
    return jsonify(shipments)


@api_bp.get("/operator/shipment/<loading_session_id>")
def get_shipment_details(loading_session_id: str):
    """Get details of a specific loading session"""
    shipment = _service().get_shipment_details(loading_session_id)
    if not shipment:
        return jsonify({"message": "Shipment not found"}), 404
    return jsonify(shipment)


@api_bp.post("/operator/complete-shipment")
def operator_complete_shipment():
    """Web operator completes shipment with Sefer No, Plaka, and ASN/Irsaliye"""
    payload = request.get_json(force=True, silent=True) or {}
    
    loading_session_id = payload.get("loadingSessionId")
    sefer_numarasi = payload.get("seferNumarasi")
    plaka_no = payload.get("plakaNo")
    shipping_type = payload.get("shippingType")  # "asn", "irsaliye", or "both"
    operator_user = payload.get("operatorUser") or (current_user.Username if current_user.is_authenticated else None)
    selected_dolly_ids = payload.get("selectedDollyIds")  # Optional: for partial shipment
    
    if not loading_session_id:
        return jsonify({"message": "loadingSessionId is required"}), 400
    if not sefer_numarasi:
        return jsonify({"message": "seferNumarasi is required"}), 400
    if not plaka_no:
        return jsonify({"message": "plakaNo is required"}), 400
    if not shipping_type or shipping_type not in ["asn", "irsaliye", "both"]:
        return jsonify({"message": "shippingType must be 'asn', 'irsaliye', or 'both'"}), 400
    
    try:
        result = _service().operator_complete_shipment(
            loading_session_id=loading_session_id,
            sefer_numarasi=sefer_numarasi,
            plaka_no=plaka_no,
            shipping_type=shipping_type,
            operator_user=operator_user,
            selected_dolly_ids=selected_dolly_ids
        )
        return jsonify(result), 200
    except ValueError as exc:
        # Validation errors - user can fix and retry
        return jsonify({"error": str(exc), "retryable": True}), 400
    except RuntimeError as exc:
        # System errors - transaction rolled back
        return jsonify({"error": str(exc), "retryable": True}), 500
    except Exception as exc:
        # Unexpected errors
        return jsonify({"error": "Beklenmeyen hata", "message": str(exc), "retryable": False}), 500


# LEGACY endpoint - keep for backward compatibility
@api_bp.post("/groups/<dolly_no>/submit")
def submit_hold_entry(dolly_no: str):
    """DEPRECATED: Use /operator/complete-shipment instead"""
    payload = request.get_json(force=True, silent=True) or {}
    terminal_user = payload.get("terminalUser")
    entry = _service().submit_hold_entry(dolly_no, terminal_user)
    if not entry:
        return jsonify({"message": "Hold entry not found"}), 404
    return jsonify(asdict(entry))


@api_bp.get("/pworkstations/eol")
def list_eol_candidates():
    stations = _service().list_eol_candidates()
    return jsonify([asdict(station) for station in stations])


@api_bp.get("/groups/definitions")
def list_group_definitions():
    definitions = _service().list_group_definitions()
    return jsonify([asdict(definition) for definition in definitions])


@api_bp.post("/groups")
def create_group():
    payload = request.get_json(force=True, silent=True) or {}
    name = payload.get("name")
    if not name:
        return jsonify({"message": "name is required"}), 400
    selections = _parse_eol_selections(payload)
    if not selections:
        return jsonify({"message": "Provide eolSelections or eolIds"}), 400
    description = payload.get("description")
    try:
        definition = _service().create_group(name, description, selections, actor_name="api")
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({"message": str(exc)}), 500
    return jsonify(asdict(definition)), 201


@api_bp.put("/groups/<int:group_id>")
def update_group(group_id: int):
    payload = request.get_json(force=True, silent=True) or {}
    selections = _parse_eol_selections(payload)
    if selections is None:
        return jsonify({"message": "Provide eolSelections or eolIds"}), 400
    try:
        definition = _service().update_group(
            group_id,
            payload.get("name"),
            payload.get("description"),
            selections,
            actor_name="api",
        )
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    if not definition:
        return jsonify({"message": "Group not found"}), 404
    return jsonify(asdict(definition))


@api_bp.post("/barcode/lookup")
def lookup_by_barcode():
    payload = request.get_json(force=True, silent=True) or {}
    barcode = payload.get("barcode")
    if not barcode:
        return jsonify({"message": "barcode is required"}), 400
    entry = _service().lookup_dolly_by_barcode(barcode)
    if not entry:
        return jsonify({"message": "Dolly not found for barcode"}), 404
    return jsonify(asdict(entry))


def _parse_eol_selections(payload: dict) -> Optional[List[dict]]:
    selections = payload.get("eolSelections")
    if selections:
        parsed = []
        for entry in selections:
            try:
                entry_id = int(entry.get("id"))
            except (TypeError, ValueError):
                continue
            tag = (entry.get("tag") or "both").lower()
            if tag not in {"asn", "irsaliye", "both"}:
                tag = "both"
            parsed.append({"id": entry_id, "tag": tag})
        return parsed
    eol_ids = payload.get("eolIds") or []
    if not eol_ids:
        return None
    parsed = []
    for entry_id in eol_ids:
        try:
            parsed.append({"id": int(entry_id), "tag": "both"})
        except (TypeError, ValueError):
            continue
    return parsed


# Web Operator API Endpoints
@api_bp.get("/operator/tasks")
def list_operator_tasks():
    status = request.args.get("status")
    tasks = _service().list_web_operator_tasks(status=status)
    return jsonify([asdict(task) for task in tasks])


@api_bp.get("/operator/tasks/<part_number>")
def get_operator_task(part_number: str):
    task = _service().get_web_operator_task(part_number)
    if not task:
        return jsonify({"message": "Task not found"}), 404
    return jsonify(asdict(task))


@api_bp.post("/operator/tasks/<part_number>/assign")
def assign_operator_task(part_number: str):
    payload = request.get_json(force=True, silent=True) or {}
    user_id = payload.get("userId")
    if not user_id:
        return jsonify({"message": "userId is required"}), 400
    
    success = _service().update_web_operator_task_status(part_number, "in_progress", user_id)
    if not success:
        return jsonify({"message": "Task not found"}), 404
    return jsonify({"status": "assigned", "partNumber": part_number})


@api_bp.post("/operator/tasks/<part_number>/add-dolly")
def add_dolly_to_task(part_number: str):
    payload = request.get_json(force=True, silent=True) or {}
    dolly_no = payload.get("dollyNo")
    vin_no = payload.get("vinNo")
    terminal_user = payload.get("terminalUser", "web_operator")
    
    if not dolly_no or not vin_no:
        return jsonify({"message": "dollyNo and vinNo are required"}), 400
    
    entry = _service().add_dolly_to_task(part_number, dolly_no, vin_no, terminal_user)
    if not entry:
        return jsonify({"message": "Task not found"}), 404
    return jsonify(asdict(entry)), 201


@api_bp.delete("/operator/tasks/<part_number>/remove-dolly/<dolly_no>")
def remove_dolly_from_task(part_number: str, dolly_no: str):
    payload = request.get_json(silent=True) or {}
    actor_name = payload.get("actorName", "web_operator")
    
    success = _service().remove_dolly_from_task(part_number, dolly_no, actor_name)
    if not success:
        return jsonify({"message": "Cannot remove dolly (not found or not the last one)"}), 400
    return jsonify({"status": "removed", "dollyNo": dolly_no})


@api_bp.post("/operator/tasks/<part_number>/submit/<tag_type>")
def submit_operator_task(part_number: str, tag_type: str):
    if tag_type not in ["asn", "irsaliye", "both"]:
        return jsonify({"message": "Invalid tag type"}), 400
    
    payload = request.get_json(force=True, silent=True) or {}
    user_id = payload.get("userId")
    if not user_id:
        return jsonify({"message": "userId is required"}), 400
    
    success = _service().submit_task_with_tag(part_number, tag_type, user_id)
    if not success:
        return jsonify({"message": "Task not found or cannot be submitted"}), 400
    
    # Realtime bildirim (el terminali submit'i)
    try:
        RealtimeService.emit_notification(
            message=f"✅ Görev {part_number} el terminalinden submit edildi ({tag_type.upper()})",
            notification_type="success"
        )
    except Exception as e:
        current_app.logger.warning(f"Realtime notification failed for API submit: {e}")
    
    return jsonify({"status": "submitted", "partNumber": part_number, "tagType": tag_type})


# Manual Queue Management API Endpoints  
@api_bp.get("/queue/grouped")
def list_queue_grouped():
    """Get queue dollys grouped by project"""
    grouped = _service().list_queue_dollys_grouped()
    return jsonify({
        project: [asdict(dolly) for dolly in dollys] 
        for project, dollys in grouped.items()
    })


@api_bp.get("/queue/stats") 
def get_queue_statistics():
    """Get queue statistics"""
    stats = _service().get_queue_stats()
    return jsonify(stats)


@api_bp.post("/queue/add-dolly")
def manual_add_dolly():
    """Manually add dolly to queue"""
    payload = request.get_json(force=True, silent=True) or {}
    
    required_fields = ["dollyNo", "vinNo", "customerRef", "eolName", "eolId"]
    for field in required_fields:
        if not payload.get(field):
            return jsonify({"message": f"{field} is required"}), 400
    
    actor_name = payload.get("actorName", "api_user")
    
    try:
        entry = _service().manual_add_dolly_to_queue(
            dolly_no=payload["dollyNo"],
            vin_no=payload["vinNo"], 
            customer_ref=payload["customerRef"],
            eol_name=payload["eolName"],
            eol_id=payload["eolId"],
            actor_name=actor_name
        )
        return jsonify(asdict(entry)), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400


@api_bp.post("/queue/submit-dolly/<dolly_no>")
def manual_submit_dolly(dolly_no: str):
    """Manually submit dolly from queue"""
    payload = request.get_json(silent=True) or {}
    actor_name = payload.get("actorName", "api_user")
    
    try:
        success = _service().manual_submit_dolly(dolly_no, actor_name)
        if success:
            return jsonify({"status": "submitted", "dollyNo": dolly_no})
        else:
            return jsonify({"message": "Submit failed"}), 400
    except ValueError as e:
        return jsonify({"message": str(e)}), 400


@api_bp.post("/queue/reorder")
def reorder_queue():
    """Reorder dollys in queue"""
    payload = request.get_json(force=True, silent=True) or {}
    dolly_orders = payload.get("dollyOrders", [])
    actor_name = payload.get("actorName", "api_user")
    
    if not dolly_orders:
        return jsonify({"message": "dollyOrders is required"}), 400
    
    success = _service().reorder_queue_dollys(dolly_orders, actor_name)
    if success:
        return jsonify({"status": "reordered", "count": len(dolly_orders)})
    else:
        return jsonify({"message": "Reorder failed"}), 400


@api_bp.post("/web-operator/create-manual-task")
def create_manual_web_operator_task():
    """Create manual web operator tasks"""
    try:
        # Get form data
        group_id = request.form.get('group_id')
        task_count = request.form.get('task_count', '1')
        shipping_tag = request.form.get('shipping_tag', 'both')
        
        if not group_id:
            return jsonify({"success": False, "message": "Grup seçimi zorunludur"}), 400
        
        try:
            group_id = int(group_id)
            task_count = int(task_count)
        except ValueError:
            return jsonify({"success": False, "message": "Geçersiz parametre"}), 400
        
        if not 1 <= task_count <= 50:
            return jsonify({"success": False, "message": "Görev sayısı 1-50 arasında olmalı"}), 400
        
        if shipping_tag not in ["asn", "irsaliye", "both"]:
            return jsonify({"success": False, "message": "Geçersiz etiket türü"}), 400
        
        # Create tasks
        created_tasks = _service().create_manual_web_operator_tasks(
            group_id=group_id,
            task_count=task_count,
            shipping_tag=shipping_tag,
            actor_name="web_operator"
        )
        
        return jsonify({
            "success": True,
            "message": f"{len(created_tasks)} görev başarıyla oluşturuldu",
            "created_count": len(created_tasks),
            "tasks": [{"part_number": task.part_number, "status": task.status} for task in created_tasks]
        })
        
    except Exception as e:
        current_app.logger.error(f"Manual task creation error: {e}")
        return jsonify({"success": False, "message": "Bir hata oluştu"}), 500


@api_bp.get("/group-dollys/<int:group_id>")
def get_group_dollys(group_id: int):
    """Get dollys for a specific group - with VIN breakdown"""
    try:
        service = _service()
        dollys = service.get_dollys_by_group(group_id)
        
        return jsonify({
            "success": True,
            "dollys": [
                {
                    "id": f"{dolly.dolly_no}_{dolly.vin_no}",  # Unique ID for VIN breakdown
                    "dolly_no": dolly.dolly_no,
                    "vin_no": dolly.vin_no,
                    "customer_ref": dolly.customer_ref,
                    "eol_name": dolly.eol_name,
                    "eol_date": dolly.eol_date.isoformat() if dolly.eol_date else None,
                    "status": dolly.status or "waiting",
                    "metadata": dolly.metadata if hasattr(dolly, 'metadata') else {}
                }
                for dolly in dollys
            ]
        })
        
    except Exception as e:
        current_app.logger.error(f"Get group dollys error: {e}")
        return jsonify({"success": False, "message": "Dollylar yüklenemedi"}), 500


@api_bp.get("/search-dolly/<dolly_no>")
def search_dolly(dolly_no: str):
    """Search for a dolly across all groups"""
    try:
        service = _service()
        
        # Search in all DollyEOLInfo for this dolly number
        from ..extensions import db
        from ..models.dolly import DollyEOLInfo
        from ..models.group import DollyGroup, DollyGroupEOL
        from ..models.dolly_hold import DollySubmissionHold
        
        # Get all dollys with this number (VIN breakdown)
        dollys = db.session.query(DollyEOLInfo).filter(
            DollyEOLInfo.DollyNo == dolly_no
        ).all()
        
        if not dollys:
            return jsonify({
                "success": True,
                "dollys": [],
                "message": f"Dolly {dolly_no} bulunamadı"
            })
        
        # Convert to queue entries with VIN breakdown
        queue_entries = []
        group_info = None
        
        for dolly in dollys:
            # Find which group this dolly belongs to
            if not group_info:
                # Try to find group by EOLID
                try:
                    if dolly.EOLID and dolly.EOLID.isdigit():
                        group_eol = db.session.query(DollyGroupEOL).filter(
                            DollyGroupEOL.PWorkStationId == int(dolly.EOLID)
                        ).first()
                        
                        if group_eol:
                            group = db.session.query(DollyGroup).filter(
                                DollyGroup.Id == group_eol.GroupId
                            ).first()
                            if group:
                                group_info = {
                                    "id": group.Id,
                                    "name": group.Name,
                                    "description": group.Description
                                }
                except (ValueError, AttributeError):
                    pass
            
            vin_list = service._split_vin_numbers(dolly.VinNo)
            if not vin_list:
                vin_list = [dolly.VinNo or dolly.DollyNo]
            
            for vin in vin_list:
                submitted_dolly = db.session.query(DollySubmissionHold).filter(
                    DollySubmissionHold.DollyNo == dolly.DollyNo,
                    DollySubmissionHold.VinNo == vin,
                    DollySubmissionHold.Status.in_(['submitted', 'completed'])
                ).first()
                
                entry = service._to_queue_entry(dolly)
                entry.vin_no = vin
                if submitted_dolly:
                    entry.status = "submitted"
                    entry.metadata["submitted_at"] = submitted_dolly.SubmittedAt.isoformat() if submitted_dolly.SubmittedAt else None
                
                queue_entries.append(entry)
        
        # Sort by VIN for consistent display
        queue_entries.sort(key=lambda x: x.vin_no)
        
        return jsonify({
            "success": True,
            "dollys": [
                {
                    "id": f"{dolly.dolly_no}_{dolly.vin_no}",
                    "dolly_no": dolly.dolly_no,
                    "vin_no": dolly.vin_no,
                    "customer_ref": dolly.customer_ref,
                    "eol_name": dolly.eol_name,
                    "eol_date": dolly.eol_date.isoformat() if dolly.eol_date else None,
                    "status": dolly.status or "waiting",
                    "metadata": dolly.metadata if hasattr(dolly, 'metadata') else {}
                }
                for dolly in queue_entries
            ],
            "group_info": group_info
        })
        
    except Exception as e:
        current_app.logger.error(f"Search dolly error: {e}")
        return jsonify({"success": False, "message": str(e)})


@api_bp.post("/manual-collection-submission")
def manual_collection_submission():
    """Submit manually selected dollys"""
    try:
        payload = request.get_json()
        
        group_id = payload.get('groupId') 
        group_name = payload.get('groupName')
        dollys = payload.get('dollys', [])
        
        if not all([group_id, group_name, dollys]):
            return jsonify({"success": False, "message": "Eksik parametreler"}), 400
        
        if not dollys:
            return jsonify({"success": False, "message": "Hiç dolly seçilmemiş"}), 400
        
        # Create manual collection submission
        result = _service().create_manual_collection_submission(
            group_id=group_id,
            group_name=group_name,
            dollys=dollys,
            actor_name="web_operator"
        )
        
        # Emit real-time update
        RealtimeService.emit_manual_collection(
            group_id=group_id,
            group_name=group_name,
            dolly_count=len(dollys),
            actor="web_operator"
        )
        
        return jsonify({
            "success": True,
            "message": f"{len(dollys)} dolly başarıyla submit edildi",
            "submitted_count": len(dollys),
            "part_number": result['part_number'],
            "task_id": result['task_id']
        })
        
    except Exception as e:
        current_app.logger.error(f"Manual collection submission error: {e}")
        return jsonify({"success": False, "message": "Submit işlemi başarısız"}), 500


@api_bp.route('/monitoring/status', methods=['GET'])
@login_required
def get_monitoring_status():
    """Database monitoring durumunu getir"""
    try:
        from ..services.database_monitor import db_monitor
        stats = db_monitor.get_monitoring_stats()
        
        return jsonify({
            'success': True,
            'monitoring': stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        current_app.logger.error(f"Monitoring status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.get("/manual-collection/check-updates")
def check_manual_collection_updates():
    """Check if there are new AVAILABLE dollys
    
    NOTE: Submit edilen dolly'ler DollyEOLInfo'dan silindiği için
    sadece DollyEOLInfo'yu saymak yeterli.
    
    Query params:
        last_count: Number of dollys client currently has
    
    Returns:
        has_updates: bool - Whether there are new dollys
        total_count: int - Current available dolly count
        new_count: int - Number of new dollys
    """
    try:
        from ..models.dolly import DollyEOLInfo
        
        last_count = request.args.get('last_count', type=int, default=0)
        
        # Count unique DollyNo values in DollyEOLInfo
        # (Her dolly'de birden fazla VIN olabilir, unique DollyNo sayısı önemli)
        current_count = db.session.query(
            db.func.count(db.distinct(DollyEOLInfo.DollyNo))
        ).scalar() or 0
        
        has_updates = current_count > last_count
        new_count = current_count - last_count if has_updates else 0
        
        # Only log and emit if there are actually new dollys
        if has_updates and new_count > 0:
            current_app.logger.info(f"📦 Yeni dolly tespit edildi: {new_count} yeni, toplam: {current_count}")
            
            # Emit real-time event
            RealtimeService.emit_dolly_update(
                event_type='new_dollys_available',
                data={
                    'new_count': new_count,
                    'total_count': current_count,
                    'message': f'{new_count} yeni dolly eklendi'
                }
            )
        
        return jsonify({
            'has_updates': has_updates,
            'total_count': current_count,
            'new_count': new_count
        })
        
    except Exception as e:
        current_app.logger.error(f"❌ Check updates error: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({'has_updates': False, 'total_count': 0, 'new_count': 0})


@api_bp.post("/manual-collection/submit")
@login_required
def submit_manual_collection():
    """Submit selected dollys for manual collection
    
    CRITICAL WORKFLOW:
    1. Validate sequential selection (1, 2, 3...)
    2. For each dolly+VIN:
       a) Read from DollyEOLInfo
       b) DELETE from DollyEOLInfo
       c) INSERT into DollySubmissionHold (Status: pending)
    3. Transaction: All or nothing (rollback on error)
    
    Request:
    {
        "dollys": [
            {
                "dollyNo": "1234567",
                "orderNumber": 1,
                "vins": ["VIN1", "VIN2"],
                "vinCount": 2,
                "eol": "EOL-A"
            }
        ]
    }
    
    Returns:
        success: bool
        message: str
        submitted_count: int
        error: str (if failed)
    """
    try:
        data = request.get_json()
        dollys = data.get('dollys', [])
        
        if not dollys:
            return jsonify({'success': False, 'error': 'Hiç dolly seçilmedi'}), 400
        
        # VALIDATION 1: Sequential order check PER EOL (Her EOL için ayrı ayrı sıralı kontrol)
        eol_groups = {}
        for dolly in dollys:
            eol = dolly.get('eol', 'UNKNOWN')
            if eol not in eol_groups:
                eol_groups[eol] = []
            eol_groups[eol].append(dolly['orderNumber'])
        
        # Her EOL için sıralı kontrol
        for eol, order_numbers in eol_groups.items():
            order_numbers_sorted = sorted(order_numbers)
            # Her EOL için kendi içinde sıralı olmalı (1,2,3 veya 5,6,7 vs.)
            for i in range(1, len(order_numbers_sorted)):
                if order_numbers_sorted[i] != order_numbers_sorted[i-1] + 1:
                    current_app.logger.error(f"❌ {eol} için sıralama hatası: {order_numbers_sorted}")
                    return jsonify({
                        'success': False, 
                        'error': f'{eol} için sıralı seçim zorunludur! Gelen: {order_numbers_sorted}'
                    }), 400
        
        current_app.logger.info(f"📋 Manuel toplama başlatıldı: {len(dollys)} dolly, {sum(d['vinCount'] for d in dollys)} VIN")
        current_app.logger.info(f"📊 EOL Dağılımı: {dict((eol, len(nums)) for eol, nums in eol_groups.items())}")
        
        
        # Transaction başlat
        from ..models.dolly import DollyEOLInfo
        from ..models.dolly_hold import DollySubmissionHold
        import uuid
        
        total_vins_processed = 0
        total_dollys_processed = 0
        
        # Generate SINGLE PartNumber for ENTIRE batch (TÜM seçilen dolly'ler için TEK PartNumber)
        # Yeni format: PART-{EOLAdı}-{İlkDolly}{SonDolly}-{DollyAdedi}
        
        # İlk dolly'den EOL bilgisi al
        first_dolly = dollys[0]
        first_vin = first_dolly['vins'][0]
        first_eol_record = db.session.query(DollyEOLInfo).filter_by(
            DollyNo=first_dolly['dollyNo'],
            VinNo=first_vin
        ).first()
        
        if not first_eol_record:
            return jsonify({'success': False, 'error': 'İlk VIN kaydı bulunamadı'}), 404
        
        # İlk ve son dolly'yi bul
        first_dolly_no = dollys[0]['dollyNo']
        last_dolly_no = dollys[-1]['dollyNo']
        total_dolly_count = len(dollys)
        
        # EOL adını temizle
        eol_clean = (first_eol_record.EOLName or 'EOL')[:20].replace(' ', '').upper()
        
        # SINGLE PartNumber for ALL dollys in this batch
        # Format: PART-{EOLAdı}-{İlkDolly}{SonDolly}-{DollyAdedi}
        # Örnek: PART-V710-D001D025-25
        single_part_number = f"PART-{eol_clean}-{first_dolly_no}{last_dolly_no}-{total_dolly_count}"
        
        current_app.logger.info(f"🏷️  TEK Batch PartNumber (TÜM {len(dollys)} dolly için): {single_part_number}")
        
        # 🔍 Grup ismi veya EOL ismi bul (display_name için CustomerReferans)
        from ..models.group import DollyGroup, DollyGroupEOL
        from ..models.pworkstation import PWorkStation
        
        # Tüm seçilen dolly'lerin EOL'lerini topla
        unique_eol_names = set()
        for dolly_data in dollys:
            # İlk VIN'den EOL bilgisini al
            if dolly_data['vins']:
                first_vin = dolly_data['vins'][0]
                temp_eol_record = db.session.query(DollyEOLInfo).filter_by(
                    DollyNo=dolly_data['dollyNo'],
                    VinNo=first_vin
                ).first()
                if temp_eol_record and temp_eol_record.EOLName:
                    unique_eol_names.add(temp_eol_record.EOLName)
        
        # Grup/EOL ismi belirle
        display_customer_referans = eol_clean  # Varsayılan
        
        if unique_eol_names:
            # EOL'ler için PWorkStation bul
            eol_stations = db.session.query(PWorkStation).filter(
                PWorkStation.PWorkStationName.in_(unique_eol_names)
            ).all()
            
            # Bu EOL'ler için grup isimleri bul
            group_names_set = set()
            for eol in eol_stations:
                group_eols = db.session.query(DollyGroupEOL).filter(
                    DollyGroupEOL.PWorkStationId == eol.Id
                ).all()
                
                for ge in group_eols:
                    if ge.GroupId:
                        group = db.session.query(DollyGroup).filter_by(Id=ge.GroupId).first()
                        if group and group.GroupName:
                            group_names_set.add(group.GroupName)
            
            # Eğer grup isimleri bulunduysa, join et
            if group_names_set:
                display_customer_referans = " / ".join(sorted(group_names_set))
            else:
                # Grup ismi yoksa, EOL isimlerini kullan
                display_customer_referans = " / ".join(sorted(unique_eol_names))
        
        current_app.logger.info(f"📛 Display Customer Referans: {display_customer_referans}")
        
        # Process each dolly
        for dolly_data in dollys:
            dolly_no = dolly_data['dollyNo']
            vins = dolly_data['vins']
            order_num = dolly_data['orderNumber']
            
            current_app.logger.info(f"  📦 Dolly {dolly_no}: {len(vins)} VIN işleniyor...")
            
            # Process each VIN
            for vin in vins:
                # 1. Read from DollyEOLInfo
                eol_record = db.session.query(DollyEOLInfo).filter_by(
                    DollyNo=dolly_no,
                    VinNo=vin
                ).first()
                
                if not eol_record:
                    # CRITICAL ERROR: VIN not found
                    db.session.rollback()
                    error_msg = f'VIN bulunamadı: DollyNo={dolly_no}, VinNo={vin}'
                    current_app.logger.error(f"❌ {error_msg}")
                    return jsonify({'success': False, 'error': error_msg}), 404
                
                # 2. Check if already in DollySubmissionHold (prevent duplicate)
                exists = db.session.query(DollySubmissionHold).filter_by(
                    DollyNo=dolly_no,
                    VinNo=vin
                ).first()
                
                if exists:
                    db.session.rollback()
                    error_msg = f'VIN zaten submit edilmiş: DollyNo={dolly_no}, VinNo={vin}'
                    current_app.logger.error(f"❌ {error_msg}")
                    return jsonify({'success': False, 'error': error_msg}), 409
                
                # 3. INSERT into DollySubmissionHold
                hold_record = DollySubmissionHold(
                    DollyNo=dolly_no,
                    VinNo=vin,
                    Status='pending',
                    DollyOrderNo=eol_record.DollyOrderNo,
                    CustomerReferans=display_customer_referans,  # ✅ Grup/EOL ismi
                    PartNumber=single_part_number,  # ✅ AYNI PartNumber (tüm seçilen dolly'ler için TEK)
                    EOLName=eol_record.EOLName,
                    EOLID=eol_record.EOLID,
                    Adet=eol_record.Adet,
                    ScanOrder=order_num,  # Dolly seçim sırası (1, 2, 3, ...)
                    TerminalUser=current_user.Username,
                    CreatedAt=datetime.now()  # ✅ Yerel saat
                )
                db.session.add(hold_record)
                
                current_app.logger.debug(f"    ✓ VIN={vin}, PartNumber={single_part_number}, ScanOrder={order_num}")
                
                # 4. DELETE from DollyEOLInfo
                db.session.delete(eol_record)
                
                total_vins_processed += 1
            
            total_dollys_processed += 1
        
        # Commit transaction
        db.session.commit()
        
        current_app.logger.info(f"✅ Manuel toplama tamamlandı: {total_dollys_processed} dolly, {total_vins_processed} VIN")
        
        return jsonify({
            'success': True,
            'message': f'{total_dollys_processed} dolly ({total_vins_processed} VIN) başarıyla submit edildi',
            'submitted_count': total_dollys_processed,
            'vin_count': total_vins_processed
        })
        
    except Exception as e:
        # Rollback on any error
        db.session.rollback()
        current_app.logger.error(f"❌ Submit manual collection error: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': f'Sistem hatası: {str(e)}'}), 500


@api_bp.route('/monitoring/start', methods=['POST'])
@login_required 
def start_monitoring():
    """Database monitoring'i başlat"""
    try:
        from ..services.database_monitor import db_monitor
        
        if db_monitor.is_running:
            return jsonify({
                'success': False,
                'message': 'Monitoring zaten çalışıyor'
            })
            
        db_monitor.start_monitoring()
        return jsonify({
            'success': True,
            'message': 'Database monitoring başlatıldı'
        })
    except Exception as e:
        current_app.logger.error(f"Start monitoring error: {e}")
        return jsonify({
            'success': False,
            'message': 'Monitoring başlatılamadı'
        }), 500


@api_bp.route('/monitoring/stop', methods=['POST'])
@login_required
def stop_monitoring():
    """Database monitoring'i durdur"""
    try:
        from ..services.database_monitor import db_monitor
        
        if not db_monitor.is_running:
            return jsonify({
                'success': False,
                'message': 'Monitoring zaten durmuş'
            })
            
        db_monitor.stop_monitoring()
        return jsonify({
            'success': True,
            'message': 'Database monitoring durduruldu'
        })
    except Exception as e:
        current_app.logger.error(f"Stop monitoring error: {e}")
        return jsonify({
            'success': False,
            'message': 'Monitoring durdurulamadı'
        }), 500


@api_bp.post("/manual-dolly-submission")
def manual_dolly_submission():
    """Submit manually collected dollys"""
    try:
        payload = request.get_json()
        
        session_id = payload.get('sessionId')
        group_id = payload.get('groupId') 
        group_name = payload.get('groupName')
        dollys = payload.get('dollys', [])
        
        if not all([session_id, group_id, group_name, dollys]):
            return jsonify({"success": False, "message": "Eksik parametreler"}), 400
        
        if not dollys:
            return jsonify({"success": False, "message": "Hiç dolly taranmamış"}), 400
        
        # Create manual submission
        result = _service().create_manual_dolly_submission(
            session_id=session_id,
            group_id=group_id,
            group_name=group_name,
            dollys=dollys,
            actor_name="web_operator"
        )
        
        return jsonify({
            "success": True,
            "message": f"{len(dollys)} dolly başarıyla submit edildi",
            "submitted_count": len(dollys),
            "part_number": result['part_number'],
            "task_id": result['task_id']
        })
        
    except Exception as e:
        current_app.logger.error(f"Manual dolly submission error: {e}")
        return jsonify({"success": False, "message": "Submit işlemi başarısız"}), 500


# ==================== MOBILE MANUAL COLLECTION API ====================

@api_bp.get("/manual-collection/groups")
@require_forklift_auth
def get_manual_collection_groups():
    """Get all groups with EOL details for mobile app
    
    Returns groups with their EOLs, allowing selection within same group
    without strict sequential order.
    
    Headers:
        Authorization: Bearer <sessionToken>
    
    Response:
    [
      {
        "group_id": 1,
        "group_name": "710grup",
        "eols": [
          {
            "eol_id": 1,
            "eol_name": "V710-LLS-EOL",
            "dolly_count": 14,
            "scanned_count": 0
          },
          {
            "eol_id": 5,
            "eol_name": "V710-MR-EOL",
            "dolly_count": 21,
            "scanned_count": 0
          }
        ],
        "total_dolly_count": 35,
        "total_scanned_count": 0
      }
    ]
    """
    try:
        from ..models.group import DollyGroup, DollyGroupEOL
        from ..models.pworkstation import PWorkStation
        from sqlalchemy.orm import joinedload
        
        # Get active groups with their EOLs - eagerly load relationships
        groups = DollyGroup.query.filter_by(IsActive=True).options(joinedload(DollyGroup.eols)).all()
        
        # Get all station IDs across all groups
        all_station_ids = []
        for group in groups:
            all_station_ids.extend([ge.PWorkStationId for ge in group.eols])
        
        # Fetch all stations in one query
        stations = {}
        if all_station_ids:
            stations = {s.Id: s for s in PWorkStation.query.filter(PWorkStation.Id.in_(all_station_ids)).all()}
        
        # Get all EOL names
        eol_names = [s.PWorkStationName for s in stations.values()]
        
        # Get all counts in ONE query
        eol_counts = {}
        if eol_names:
            count_query = """
            SELECT 
                d.EOLName,
                COUNT(DISTINCT d.DollyNo) as dolly_count,
                COUNT(DISTINCT CASE WHEN h.DollyNo IS NOT NULL THEN h.DollyNo END) as scanned_count
            FROM DollyEOLInfo d
            LEFT JOIN DollySubmissionHold h 
                ON d.DollyNo = h.DollyNo 
                AND h.Status = 'scanned'
            WHERE d.EOLName IN :eol_names
            GROUP BY d.EOLName
            """
            
            result_proxy = db.session.execute(
                db.text(count_query).bindparams(db.bindparam('eol_names', expanding=True)), 
                {"eol_names": tuple(eol_names)}
            )
            rows = result_proxy.fetchall()
            
            for row in rows:
                eol_counts[row[0]] = {
                    'dolly_count': row[1] if row[1] else 0,
                    'scanned_count': row[2] if row[2] else 0
                }
        
        result = []
        for group in groups:
            eol_dict = {}  # Use dict to avoid duplicates
            
            for group_eol in group.eols:
                # Get EOL name from pre-fetched stations
                station = stations.get(group_eol.PWorkStationId)
                if not station:
                    continue
                
                eol_name = station.PWorkStationName
                
                # Skip if already added
                if eol_name in eol_dict:
                    continue
                
                # Get counts from pre-fetched data
                counts = eol_counts.get(eol_name, {'dolly_count': 0, 'scanned_count': 0})
                dolly_count = counts['dolly_count']
                scanned_count = counts['scanned_count']
                
                if dolly_count > 0:  # Sadece dolly'si olan EOL'leri göster
                    eol_dict[eol_name] = {
                        "eol_id": group_eol.PWorkStationId,
                        "eol_name": eol_name,
                        "dolly_count": dolly_count,
                        "scanned_count": scanned_count
                    }
            
            if eol_dict:  # Sadece dolly'si olan grupları göster
                eol_list = list(eol_dict.values())
                total_dolly_count = sum(e['dolly_count'] for e in eol_list)
                total_scanned_count = sum(e['scanned_count'] for e in eol_list)
                
                result.append({
                    "group_id": group.Id,
                    "group_name": group.GroupName,
                    "eols": eol_list,
                    "total_dolly_count": total_dolly_count,
                    "total_scanned_count": total_scanned_count
                })
        
        return jsonify(result), 200
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"Get manual collection groups error: {e}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({"error": "Gruplar alınamadı", "retryable": True}), 500


@api_bp.get("/manual-collection/groups/<int:group_id>")
@require_forklift_auth
def get_group_with_eols_and_dollys(group_id):
    """Get group details with all EOLs and dollys
    
    Returns complete group information including all EOLs and their dollys.
    
    Headers:
        Authorization: Bearer <sessionToken>
    
    Response:
    {
      "group_id": 3,
      "group_name": "deneme1213",
      "part_number": "ABC-123-456",
      "eols": [
        {
          "eol_id": 11,
          "eol_name": "V710-LLS-EOL",
          "dollys": [
            {
              "dolly_no": 1071092,
              "dolly_order_no": 32012,
              "vin_no": "VIN123",
              "customer_referans": "PZ3117859AC",
              "adet": 14,
              "is_scanned": false
            }
          ]
        }
      ]
    }
    """
    try:
        from ..models.group import DollyGroup, DollyGroupEOL
        from ..models.pworkstation import PWorkStation
        
        current_app.logger.info(f"Getting group details for group_id={group_id}")
        
        # 1. Get group
        group = DollyGroup.query.filter_by(Id=group_id, IsActive=True).first()
        
        if not group:
            return jsonify({
                "error": f"Grup ID {group_id} bulunamadı",
                "retryable": True
            }), 404
        
        # 2. Get latest part number for this group (if any submitted)
        import hashlib
        group_hash = hashlib.md5(group.GroupName.encode()).hexdigest()[:8].upper()
        session_pattern = f"MANUAL-{group_hash}-%"
        
        part_number_query = """
        SELECT TOP 1 PartNumber
        FROM DollySubmissionHold
        WHERE LoadingSessionId LIKE :session_pattern
        ORDER BY CreatedAt DESC
        """
        part_result = db.session.execute(db.text(part_number_query), {"session_pattern": session_pattern}).fetchone()
        part_number = part_result[0] if part_result else None
        
        # 3. Get all EOLs in this group
        group_eols = DollyGroupEOL.query.filter_by(GroupId=group_id).all()
        
        if not group_eols:
            return jsonify({
                "group_id": group.Id,
                "group_name": group.GroupName,
                "part_number": part_number,
                "eols": []
            }), 200
        
        # 4. Get EOL details
        eol_ids = [ge.PWorkStationId for ge in group_eols]
        eols = PWorkStation.query.filter(PWorkStation.Id.in_(eol_ids)).all()
        eol_map = {e.Id: e for e in eols}
        
        # 5. Get all dollys for each EOL with scanned status
        eol_list = []
        for group_eol in group_eols:
            eol_id = group_eol.PWorkStationId
            eol = eol_map.get(eol_id)
            
            if not eol:
                continue
            
            # Get dollys for this EOL by EOLName (EOLID may not match PWorkStationId)
            # Note: DollyEOLInfo has multiple rows per dolly (one per VIN)
            # We group by DollyNo to get one row per dolly with aggregated data
            dolly_query = """
            SELECT 
                d.DollyNo,
                MAX(d.DollyOrderNo) as DollyOrderNo,
                MAX(d.VinNo) as VinNo,
                MAX(d.CustomerReferans) as CustomerReferans,
                MAX(d.Adet) as Adet,
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM DollySubmissionHold h
                        WHERE h.DollyNo = d.DollyNo 
                        AND h.Status = 'scanned'
                        AND h.LoadingSessionId LIKE :session_pattern
                    ) THEN 1 
                    ELSE 0 
                END as IsScanned
            FROM DollyEOLInfo d
            WHERE d.EOLName = :eol_name
            GROUP BY d.DollyNo
            ORDER BY CAST(MAX(d.DollyOrderNo) AS INT) ASC
            """
            
            dolly_results = db.session.execute(db.text(dolly_query), {
                "eol_name": eol.PWorkStationName,
                "session_pattern": session_pattern
            }).fetchall()
            
            dollys = []
            for row in dolly_results:
                dollys.append({
                    "dolly_no": row[0],
                    "dolly_order_no": row[1],
                    "vin_no": row[2],
                    "customer_referans": row[3],
                    "adet": row[4] or 1,
                    "is_scanned": bool(row[5])
                })
            
            eol_list.append({
                "eol_id": eol_id,
                "eol_name": eol.PWorkStationName,
                "dollys": dollys
            })
        
        return jsonify({
            "group_id": group.Id,
            "group_name": group.GroupName,
            "part_number": part_number,
            "eols": eol_list
        }), 200
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"Get group with EOLs and dollys error: {e}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({"error": "Grup detayları alınamadı", "retryable": True}), 500


@api_bp.get("/manual-collection/groups/<int:group_id>/eols/<int:eol_id>")
@require_forklift_auth
def get_manual_collection_eol_dollys(group_id, eol_id):
    """Get all dollys in a specific EOL within a group
    
    This allows flexible selection within the same group.
    User can switch between EOLs in the same group without strict order.
    
    Headers:
        Authorization: Bearer <sessionToken>
    
    Response:
    {
      "group_id": 1,
      "group_name": "710grup",
      "eol_id": 5,
      "eol_name": "V710-MR-EOL",
      "dollys": [
        {
          "dolly_no": "1061469",
          "dolly_order_no": "1",
          "vin_no": "VIN001\nVIN002\nVIN003",
          "scanned": false
        }
      ]
    }
    """
    try:
        from ..models.group import DollyGroup, DollyGroupEOL
        from ..models.pworkstation import PWorkStation
        
        # Verify group exists and is active
        group = DollyGroup.query.filter_by(Id=group_id, IsActive=True).first()
        if not group:
            return jsonify({
                "error": f"Grup bulunamadı (ID: {group_id})",
                "retryable": False
            }), 404
        
        # Verify EOL belongs to this group
        group_eol = DollyGroupEOL.query.filter_by(
            GroupId=group_id,
            PWorkStationId=eol_id
        ).first()
        
        if not group_eol:
            return jsonify({
                "error": f"EOL bu gruba ait değil (Group: {group_id}, EOL: {eol_id})",
                "retryable": False
            }), 404
        
        # Get EOL name
        station = PWorkStation.query.filter_by(Id=eol_id).first()
        if not station:
            return jsonify({
                "error": f"EOL bulunamadı (ID: {eol_id})",
                "retryable": False
            }), 404
        
        eol_name = station.PWorkStationName
        
        # Get dollys for this EOL
        # STRING_AGG 8000 byte limitini aşıyor - sadece COUNT kullan
        query = """
        SELECT 
            d.DollyNo,
            d.DollyOrderNo,
            COUNT(DISTINCT d.VinNo) as VinCount,
            MAX(CASE WHEN h.DollyNo IS NOT NULL THEN 1 ELSE 0 END) as scanned
        FROM (
            SELECT DISTINCT DollyNo, DollyOrderNo, VinNo
            FROM DollyEOLInfo
            WHERE EOLName = :eol_name
        ) d
        LEFT JOIN DollySubmissionHold h 
            ON d.DollyNo = h.DollyNo 
            AND h.Status = 'scanned'
        GROUP BY d.DollyNo, d.DollyOrderNo
        ORDER BY d.DollyNo
        """
        
        result_proxy = db.session.execute(db.text(query), {"eol_name": eol_name})
        rows = result_proxy.fetchall()
        
        if not rows:
            return jsonify({
                "error": f"EOL '{eol_name}' için dolly bulunamadı",
                "retryable": True
            }), 404
        
        result_dollys = []
        for row in rows:
            # Her dolly için VIN'leri ayrı sorguda çek (STRING_AGG limiti yok)
            vin_query = """
            SELECT VinNo 
            FROM DollyEOLInfo 
            WHERE DollyNo = :dolly_no AND EOLName = :eol_name
            ORDER BY InsertedAt
            """
            vin_result = db.session.execute(db.text(vin_query), {
                "dolly_no": row[0],
                "eol_name": eol_name
            })
            vins = [v[0] for v in vin_result.fetchall()]
            
            result_dollys.append({
                "dolly_no": row[0],
                "dolly_order_no": row[1],
                "vin_no": "\n".join(vins),  # VIN'leri birleştir
                "scanned": bool(row[3])
            })
        
        return jsonify({
            "group_id": group_id,
            "group_name": group.GroupName,
            "eol_id": eol_id,
            "eol_name": eol_name,
            "dollys": result_dollys
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        current_app.logger.error(f"Get EOL dollys error (Group: {group_id}, EOL: {eol_id}): {e}")
        current_app.logger.error(f"Full traceback:\n{error_trace}")
        return jsonify({"error": "EOL dolly'leri alınamadı", "retryable": True, "details": str(e)}), 500


@api_bp.get("/manual-collection/groups/<string:group_name>")
@require_forklift_auth
def get_manual_collection_group_dollys(group_name):
    """Get all dollys in a specific EOL group with scanned status
    
    Headers:
        Authorization: Bearer <sessionToken>
    
    Response:
    {
      "group_name": "V710-MR-EOL",
      "dollys": [
        {
          "dolly_no": "DOLLY123",
          "vin_no": "VIN001\\nVIN002\\nVIN003",
          "scanned": false
        }
      ]
    }
    """
    try:
        # Use raw SQL query - Group VINs per dolly (with DISTINCT to avoid duplicates)
        # STRING_AGG ile NVARCHAR(MAX) kullan - 8000 byte limitini aşmamak için
        query = """
        SELECT 
            d.DollyNo,
            STRING_AGG(CAST(d.VinNo AS NVARCHAR(MAX)), CHAR(10)) WITHIN GROUP (ORDER BY d.VinNo) as VinNo,
            MAX(CASE WHEN h.DollyNo IS NOT NULL THEN 1 ELSE 0 END) as scanned
        FROM (
            SELECT DISTINCT DollyNo, VinNo
            FROM DollyEOLInfo WITH (NOLOCK)
            WHERE EOLName = :group_name
        ) d
        LEFT JOIN DollySubmissionHold h WITH (NOLOCK)
            ON d.DollyNo = h.DollyNo 
            AND h.Status = 'scanned'
        GROUP BY d.DollyNo
        ORDER BY d.DollyNo
        """
        
        result_proxy = db.session.execute(db.text(query), {"group_name": group_name})
        rows = result_proxy.fetchall()
        
        if not rows:
            return jsonify({
                "error": f"Grup '{group_name}' bulunamadı veya dolly yok",
                "retryable": True
            }), 404
        
        result_dollys = []
        for row in rows:
            result_dollys.append({
                "dolly_no": row[0],
                "vin_no": row[1] or "",
                "scanned": bool(row[2])
            })
        
        return jsonify({
            "group_name": group_name,
            "dollys": result_dollys
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        current_app.logger.error(f"Get group dollys error for '{group_name}': {e}")
        current_app.logger.error(f"Full traceback:\n{error_trace}")
        return jsonify({"error": "Grup dolly'leri alınamadı", "retryable": True, "details": str(e)}), 500


@api_bp.post("/manual-collection/scan")
@require_forklift_auth
def manual_collection_scan():
    """Scan a dolly barcode and add to Group
    
    Headers:
        Authorization: Bearer <sessionToken>
    
    Request:
    {
      "group_name": "710grup",        # GRUP ADI (zorunlu) - DollyGroup.GroupName
      "eol_name": "V710-LLS-EOL",     # EOL filtresi (opsiyonel)
      "barcode": "DOLLY123"           # Dolly barkodu veya DollyNo
    }
    
    Response (Success):
    {
      "success": true,
      "dolly_no": "DOLLY123",
      "eol_name": "V710-LLS-EOL",
      "group_name": "710grup",
      "message": "Dolly 'DOLLY123' (V710-LLS-EOL) '710grup' grubuna eklendi"
    }
    
    Response (Error - Grup bulunamadı):
    {
      "error": "Grup '710grup' bulunamadı",
      "retryable": true
    }
    
    Response (Error - Dolly farklı grupta):
    {
      "error": "Bu dolly 'V820-EOL' EOL'ünden geliyor, '710grup' grubunda değil",
      "retryable": true
    }
    
    Response (Error - Zaten taranmış):
    {
      "error": "Bu dolly zaten taranmış",
      "retryable": true
    }
    
    NOT: Bir grupta birden fazla EOL olabilir (710grup içinde V710-LLS-EOL, V710-FR-EOL vs.)

    """
    try:
        from ..models.group import DollyGroup, DollyGroupEOL
        
        payload = request.get_json(force=True, silent=True) or {}
        group_name = payload.get("group_name")
        eol_name_filter = payload.get("eol_name")  # Opsiyonel EOL filtresi
        barcode = payload.get("barcode")
        
        if not group_name or not barcode:
            return jsonify({
                "error": "group_name ve barcode gerekli",
                "retryable": True
            }), 400
        
        # 1. Grup adından grup bul
        group = DollyGroup.query.filter_by(
            GroupName=group_name,
            IsActive=True
        ).first()
        
        if not group:
            return jsonify({
                "error": f"Grup '{group_name}' bulunamadı",
                "retryable": True
            }), 404
        
        # 2. Find dolly by barcode with all needed fields
        find_query = """
        SELECT TOP 1 DollyNo, VinNo, EOLName, DollyOrderNo, CustomerReferans, EOLID, Adet
        FROM DollyEOLInfo
        WHERE EOLDollyBarcode = :barcode OR DollyNo = :barcode
        """
        
        result = db.session.execute(db.text(find_query), {"barcode": barcode}).fetchone()
        
        if not result:
            return jsonify({
                "error": f"Barkod '{barcode}' sistemde bulunamadı",
                "retryable": True
            }), 404
        
        dolly_no = result[0]
        vin_no = result[1]
        eol_name = result[2]
        dolly_order_no = result[3]
        customer_referans = result[4]
        eol_id = result[5]
        adet = result[6] or 1
        
        # 3. Dolly'nin EOL'ü bu grubun içinde mi kontrol et (EOL Name üzerinden)
        from ..models.pworkstation import PWorkStation
        
        # EOL adından PWorkStation'ları bul
        pworkstations = PWorkStation.query.filter_by(PWorkStationName=eol_name).all()
        
        if not pworkstations:
            return jsonify({
                "error": f"EOL '{eol_name}' PWorkStation tablosunda bulunamadı",
                "retryable": True
            }), 404
        
        # Bu grup bu EOL'lerden herhangi birini içeriyor mu?
        pws_ids = [pws.Id for pws in pworkstations]
        group_eol = DollyGroupEOL.query.filter(
            DollyGroupEOL.GroupId == group.Id,
            DollyGroupEOL.PWorkStationId.in_(pws_ids)
        ).first()
        
        if not group_eol:
            return jsonify({
                "error": f"Bu dolly '{eol_name}' EOL'ünden geliyor, '{group_name}' grubunda değil",
                "retryable": True
            }), 400
        
        # 4. Opsiyonel: EOL filtresi kontrolü
        if eol_name_filter and eol_name != eol_name_filter:
            return jsonify({
                "error": f"Bu dolly '{eol_name}' EOL'ünden, '{eol_name_filter}' değil",
                "retryable": True
            }), 400
        
        # 5. Check if already scanned
        check_query = """
        SELECT COUNT(*) FROM DollySubmissionHold
        WHERE DollyNo = :dolly_no AND Status = 'scanned'
        """
        
        count = db.session.execute(db.text(check_query), {"dolly_no": dolly_no}).scalar()
        
        if count > 0:
            return jsonify({
                "error": "Bu dolly zaten taranmış",
                "retryable": True
            }), 400
        
        # ✅ SIRALI OKUTMA KONTROLÜ (Her EOL için ayrı ayrı - DollyOrderNo bazlı)
        # 1. Okutulan dolly'nin DollyOrderNo'sunu bul
        dolly_order_query = """
        SELECT TOP 1 DollyOrderNo
        FROM DollyEOLInfo
        WHERE DollyNo = :dolly_no AND EOLName = :eol_name
        """
        
        dolly_order_result = db.session.execute(db.text(dolly_order_query), {
            "dolly_no": dolly_no,
            "eol_name": eol_name
        }).fetchone()
        
        if not dolly_order_result or not dolly_order_result[0]:
            return jsonify({
                "error": f"Dolly '{dolly_no}' için DollyOrderNo bulunamadı",
                "retryable": True
            }), 404
        
        current_order_no = dolly_order_result[0]
        
        # 2. Bu grup+EOL'de şu ana kadar taranan en yüksek DollyOrderNo'yu bul
        import hashlib
        group_hash = hashlib.md5(group_name.encode()).hexdigest()[:8].upper()
        session_pattern = f"MANUAL-{group_hash}-%"
        
        last_scanned_query = """
        SELECT MAX(CAST(d.DollyOrderNo AS INT)) as MaxOrder
        FROM DollySubmissionHold h
        INNER JOIN DollyEOLInfo d ON h.DollyNo = d.DollyNo
        WHERE d.EOLName = :eol_name 
          AND h.Status = 'scanned'
          AND h.LoadingSessionId LIKE :session_pattern
        """
        
        last_scanned_result = db.session.execute(db.text(last_scanned_query), {
            "eol_name": eol_name,
            "session_pattern": session_pattern
        }).fetchone()
        
        last_scanned_order = last_scanned_result[0] if last_scanned_result and last_scanned_result[0] else None
        
        # Eğer hiç tarama yapılmamışsa, GRUPTAKİ EN KÜÇÜK ORDER'DAN başla
        if last_scanned_order is None:
            # Bu grup+EOL kombinasyonundaki en küçük DollyOrderNo'yu bul
            min_order_query = """
            SELECT MIN(CAST(d.DollyOrderNo AS INT)) as MinOrder
            FROM DollyEOLInfo d
            INNER JOIN DollyGroupEOL ge ON d.EOLID = ge.PWorkStationId
            WHERE ge.GroupId = :group_id
              AND d.EOLName = :eol_name
              AND d.DollyOrderNo IS NOT NULL
            """
            
            min_order_result = db.session.execute(db.text(min_order_query), {
                "group_id": group.Id,
                "eol_name": eol_name
            }).fetchone()
            
            min_order_value = min_order_result[0] if min_order_result and min_order_result[0] else None
            
            # DEBUG LOG
            current_app.logger.warning(f"🔍 MIN ORDER DEBUG - Group: {group_name} (ID:{group.Id}), EOL: {eol_name}, MinOrder: {min_order_value}")
            
            # Eğer JOIN sonuç vermezse, tüm EOL'deki minimum order'ı al
            if min_order_value is None:
                fallback_query = """
                SELECT MIN(CAST(DollyOrderNo AS INT)) as MinOrder
                FROM DollyEOLInfo
                WHERE EOLName = :eol_name
                  AND DollyOrderNo IS NOT NULL
                """
                fallback_result = db.session.execute(db.text(fallback_query), {"eol_name": eol_name}).fetchone()
                min_order_value = fallback_result[0] if fallback_result and fallback_result[0] else 1
                current_app.logger.warning(f"⚠️ FALLBACK - Tüm EOL'deki MinOrder kullanılıyor: {min_order_value}")
            
            expected_order = min_order_value
        else:
            expected_order = last_scanned_order + 1
        
        # 3. DollyOrderNo kontrolü (sadece aynı EOL içinde)
        try:
            current_order_int = int(current_order_no)
        except (ValueError, TypeError):
            return jsonify({
                "error": f"Geçersiz DollyOrderNo: {current_order_no}",
                "retryable": True
            }), 400
        
        if current_order_int != expected_order:
            # Sıradaki dolly'yi bul
            expected_dolly_query = """
            SELECT TOP 1 DollyNo
            FROM DollyEOLInfo
            WHERE EOLName = :eol_name 
              AND CAST(DollyOrderNo AS INT) = :expected_order
            """
            
            expected_dolly_result = db.session.execute(db.text(expected_dolly_query), {
                "eol_name": eol_name,
                "expected_order": expected_order
            }).fetchone()
            
            expected_dolly_no = expected_dolly_result[0] if expected_dolly_result else "BILINMIYOR"
            
            return jsonify({
                "error": f"{eol_name} EOL'de dolly sırası yanlış! Sıradaki dolly '{expected_dolly_no}' (order:{expected_order}) okutulmalı",
                "retryable": True,
                "expected_dolly": expected_dolly_no,
                "expected_order": expected_order,
                "received_dolly": dolly_no,
                "received_order": current_order_int,
                "eol_name": eol_name
            }), 400
        
        # Get current operator from session
        operator = get_current_forklift_user()
        
        # Generate group hash for session ID
        import hashlib
        group_hash = hashlib.md5(group_name.encode()).hexdigest()[:8].upper()
        
        # Session ID format: MANUAL-{GrupHash}-{Date}
        # Örnek: MANUAL-A3F2B1C4-20260121
        session_id = f"MANUAL-{group_hash}-{datetime.utcnow().strftime('%Y%m%d')}"
        
        # Count scanned dollys for this session to determine ScanOrder
        count_query = """
        SELECT COUNT(DISTINCT DollyNo) 
        FROM DollySubmissionHold
        WHERE LoadingSessionId = :session_id AND Status = 'scanned'
        """
        
        scan_count = db.session.execute(db.text(count_query), {"session_id": session_id}).scalar() or 0
        scan_order = scan_count + 1
        
        # Insert to DollySubmissionHold with all fields
        insert_query = """
        INSERT INTO DollySubmissionHold 
            (DollyNo, VinNo, Status, TerminalUser, LoadingSessionId, 
             DollyOrderNo, CustomerReferans, EOLName, EOLID, Adet, ScanOrder,
             CreatedAt, UpdatedAt)
        VALUES 
            (:dolly_no, :vin_no, 'scanned', :operator, :session_id,
             :dolly_order_no, :customer_referans, :eol_name, :eol_id, :adet, :scan_order,
             GETUTCDATE(), GETUTCDATE())
        """
        
        db.session.execute(db.text(insert_query), {
            "dolly_no": dolly_no,
            "vin_no": vin_no or "",
            "operator": operator,
            "session_id": session_id,
            "dolly_order_no": dolly_order_no,
            "customer_referans": customer_referans,
            "eol_name": eol_name,
            "eol_id": eol_id,
            "adet": adet,
            "scan_order": scan_order
        })
        db.session.commit()
        
        # Log to audit
        from ..services.audit_service import AuditService
        audit = AuditService()
        audit.log(
            action="mobile.manual_scan",
            resource="dolly",
            resource_id=dolly_no,
            actor_name=operator,
            metadata={
                "group_name": group_name,
                "eol_name": eol_name,
                "barcode": barcode
            }
        )
        
        return jsonify({
            "success": True,
            "dolly_no": dolly_no,
            "eol_name": eol_name,
            "group_name": group_name,
            "scan_order": scan_order,
            "message": f"Dolly '{dolly_no}' ({eol_name}) '{group_name}' grubuna eklendi"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Manual collection scan error: {e}")
        return jsonify({
            "error": "Tarama başarısız",
            "retryable": True
        }), 500


@api_bp.post("/manual-collection/mobile-submit")
@require_forklift_auth
def mobile_manual_collection_submit():
    """Mobile: Submit scanned dollys to operator panel (GRUP BAZLI - Tüm EOL'ler TEK PartNumber altında)
    
    Headers:
        Authorization: Bearer <sessionToken>
    
    Request:
    {
      "group_name": "deneme1213"     # GRUP ADI (zorunlu) - Grup içindeki TÜM EOL'lerdeki dollyler submit edilir
    }
    
    Response (Success):
    {
      "success": true,
      "submitted_count": 6,           # Toplam dolly sayısı (tüm EOL'lerden)
      "vin_count": 48,                # Toplam VIN sayısı
      "part_number": "PART-CUST-GRUP-20260113120000",
      "message": "6 dolly (48 VIN) başarıyla submit edildi",
      "eol_summary": {                # Her EOL'den kaç dolly submit edildiği
        "V710-LLS-EOL": 3,
        "V710-FR-EOL": 3
      }
    }
    
    Response (Error):
    {
      "error": "Hiç taranmış dolly bulunamadı",
      "retryable": true
    }
    """
    try:
        from ..models.dolly import DollyEOLInfo
        from ..models.dolly_hold import DollySubmissionHold
        import uuid
        
        payload = request.get_json(force=True, silent=True) or {}
        group_name = payload.get("group_name")
        
        if not group_name:
            return jsonify({
                "error": "group_name gerekli",
                "retryable": True
            }), 400
        
        operator = get_current_forklift_user()
        
        # 1. GRUP bazlı taranmış dolly'leri al (TÜM EOL'lerden)
        import hashlib
        group_hash = hashlib.md5(group_name.encode()).hexdigest()[:8].upper()
        session_pattern = f"MANUAL-{group_hash}-%"
        scanned_query = """
        SELECT DISTINCT h.DollyNo, d.EOLName, h.ScanOrder
        FROM DollySubmissionHold h
        LEFT JOIN DollyEOLInfo d ON h.DollyNo = d.DollyNo
        WHERE h.LoadingSessionId LIKE :session_pattern AND h.Status = 'scanned'
        ORDER BY h.ScanOrder ASC, h.DollyNo ASC
        """
        
        scanned_result = db.session.execute(db.text(scanned_query), {"session_pattern": session_pattern}).fetchall()
        scanned_dolly_info = [(row[0], row[1] or 'UNKNOWN', row[2] or 0) for row in scanned_result]  # (DollyNo, EOLName, ScanOrder)
        
        scanned_result = db.session.execute(db.text(scanned_query), {"session_pattern": session_pattern}).fetchall()
        scanned_dolly_info = [(row[0], row[1] or 'UNKNOWN', row[2] or 0) for row in scanned_result]  # (DollyNo, EOLName, ScanOrder)
        
        if not scanned_dolly_info:
            return jsonify({
                "error": "Hiç taranmış dolly bulunamadı",
                "retryable": True
            }), 400
        
        # EOL dağılımını çıkar (log için)
        eol_distribution = {}
        for _, eol_name, _ in scanned_dolly_info:
            eol_distribution[eol_name] = eol_distribution.get(eol_name, 0) + 1
        
        current_app.logger.info(f"📋 Mobile submit başlatıldı: {group_name}, {len(scanned_dolly_info)} dolly (TÜM EOL'ler)")
        current_app.logger.info(f"📊 EOL Dağılımı: {eol_distribution}")
        
        # 2. TEK PartNumber oluştur (GRUP başına TEK PartNumber - TÜM EOL'ler dahil)
        # Yeni format: PART-{Tarih}-{GrupHash}-{İlkDolly}-{SonDolly}-{Adet}
        
        # Tarih al (YYYYMMDD formatında)
        batch_date = datetime.utcnow().strftime('%Y%m%d')
        batch_timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        
        # İlk ve son dolly'yi bul
        first_dolly_no = scanned_dolly_info[0][0]  # İlk dolly
        last_dolly_no = scanned_dolly_info[-1][0]  # Son dolly
        total_dolly_count = len(scanned_dolly_info)
        
        # Grup adını hash'e çevir (uzun grup adları için - 8 karakter)
        import hashlib
        group_hash = hashlib.md5(group_name.encode()).hexdigest()[:8].upper()
        
        # LoadingSessionId formatı: MANUAL-{GrupHash}-{Timestamp}
        # Örnek: MANUAL-A3F2B1C4-20260121131736
        # Max uzunluk: 6+1+8+1+14 = 30 karakter (50 limitinin altında)
        loading_session_id = f"MANUAL-{group_hash}-{batch_timestamp}"
        
        # PartNumber formatı: PART-{Tarih}-{GrupHash}-{İlkDolly}-{SonDolly}-{Adet}
        # Örnek: PART-20260121-A3F2B1C4-1100695-1100695-1
        # Max uzunluk: 4+1+8+1+8+1+7+1+7+1+3 = ~42 karakter (50 limitinin altında)
        single_part_number = f"PART-{batch_date}-{group_hash}-{first_dolly_no}-{last_dolly_no}-{total_dolly_count}"
        
        current_app.logger.info(f"🏷️  TEK PartNumber (TÜM {len(scanned_dolly_info)} dolly için): {single_part_number}")
        
        # 🔍 Grup ismi veya EOL ismi bul (display_name için CustomerReferans)
        from ..models.group import DollyGroup, DollyGroupEOL
        from ..models.pworkstation import PWorkStation
        
        # Taranmış EOL'leri topla
        unique_eol_names = {eol_name for _, eol_name, _ in scanned_dolly_info if eol_name and eol_name != 'UNKNOWN'}
        display_customer_referans = group_name  # Varsayılan: grup ismi
        
        if unique_eol_names:
            # EOL'ler için PWorkStation bul
            eol_stations = db.session.query(PWorkStation).filter(
                PWorkStation.PWorkStationName.in_(unique_eol_names)
            ).all()
            
            # Bu EOL'ler için grup isimleri bul
            group_names_set = set()
            for eol in eol_stations:
                group_eols = db.session.query(DollyGroupEOL).filter(
                    DollyGroupEOL.PWorkStationId == eol.Id
                ).all()
                
                for ge in group_eols:
                    if ge.GroupId:
                        group = db.session.query(DollyGroup).filter_by(Id=ge.GroupId).first()
                        if group and group.GroupName:
                            group_names_set.add(group.GroupName)
            
            # Eğer grup isimleri bulunduysa, join et
            if group_names_set:
                display_customer_referans = " / ".join(sorted(group_names_set))
            else:
                # Grup ismi yoksa, EOL isimlerini kullan
                display_customer_referans = " / ".join(sorted(unique_eol_names))
        
        current_app.logger.info(f"📛 Display Customer Referans: {display_customer_referans}")
        
        total_vins = 0
        total_dollys = 0
        
        # 3. Her dolly için işlem yap (TÜM EOL'lerden)
        for dolly_no, eol_name, scan_order in scanned_dolly_info:
            # DollyEOLInfo'dan tüm VIN'leri al - SIRALAMA: 1. InsertedAt, 2. VinNo
            eol_records = db.session.query(DollyEOLInfo).filter_by(
                DollyNo=dolly_no
            ).order_by(
                DollyEOLInfo.InsertedAt.asc(),
                DollyEOLInfo.VinNo.asc()
            ).all()
            
            if not eol_records:
                current_app.logger.warning(f"⚠️ Dolly {dolly_no} DollyEOLInfo'da bulunamadı, atlanıyor...")
                continue
            
            current_app.logger.info(f"  📦 Dolly {dolly_no} ({eol_name}): {len(eol_records)} VIN işleniyor...")
            
            # Her VIN için ayrı kayıt oluştur
            for eol_record in eol_records:
                vin = eol_record.VinNo
                
                # DollySubmissionHold'da bu dolly için scanned kaydını bul
                hold_record = db.session.query(DollySubmissionHold).filter_by(
                    DollyNo=dolly_no,
                    VinNo=vin,
                    Status='scanned'
                ).first()
                
                if hold_record:
                    # Mevcut kaydı güncelle: scanned → pending
                    hold_record.Status = 'pending'
                    hold_record.PartNumber = single_part_number  # TEK PartNumber
                    hold_record.DollyOrderNo = eol_record.DollyOrderNo
                    hold_record.CustomerReferans = eol_record.CustomerReferans  # ✅ DollyEOLInfo'daki orijinal değer
                    hold_record.EOLName = eol_record.EOLName
                    hold_record.EOLID = eol_record.EOLID
                    hold_record.Adet = eol_record.Adet
                    hold_record.InsertedAt = eol_record.InsertedAt  # ✅ EOL timestamp'i koru
                    hold_record.ScanOrder = scan_order
                    hold_record.TerminalUser = operator
                    hold_record.LoadingSessionId = loading_session_id
                    hold_record.UpdatedAt = datetime.now()  # ✅ Yerel saat
                else:
                    # Yeni kayıt ekle (scan edilmiş ama hold'da yoksa)
                    hold_record = DollySubmissionHold(
                        DollyNo=dolly_no,
                        VinNo=vin,
                        Status='pending',
                        DollyOrderNo=eol_record.DollyOrderNo,
                        CustomerReferans=eol_record.CustomerReferans,  # ✅ DollyEOLInfo'daki orijinal değer
                        PartNumber=single_part_number,  # TEK PartNumber
                        EOLName=eol_record.EOLName,
                        EOLID=eol_record.EOLID,
                        Adet=eol_record.Adet,
                        InsertedAt=eol_record.InsertedAt,  # ✅ EOL timestamp'i koru
                        ScanOrder=scan_order,
                        TerminalUser=operator,
                        LoadingSessionId=loading_session_id,
                        CreatedAt=datetime.now()  # ✅ Yerel saat
                    )
                    db.session.add(hold_record)
                
                # DollyEOLInfo'dan sil
                db.session.delete(eol_record)
                total_vins += 1
            
            total_dollys += 1
        
        # Commit
        db.session.commit()
        
        # Audit log
        from ..services.audit_service import AuditService
        audit = AuditService()
        audit.log(
            action="mobile.manual_submit",
            resource="dolly_batch",
            resource_id=single_part_number,
            actor_name=operator,
            metadata={
                "group_name": group_name,
                "dolly_count": total_dollys,
                "vin_count": total_vins,
                "part_number": single_part_number,
                "eol_distribution": eol_distribution
            }
        )
        
        # Web operator paneli için realtime bildirim gönder
        try:
            from ..services.realtime_service import RealtimeService
            RealtimeService.emit_notification(
                message=f"✅ {total_dollys} dolly / {total_vins} VIN submit edildi • {single_part_number}",
                notification_type="success"
            )
            # Ayrıca task/dolly update sinyali gönder
            RealtimeService.emit_dolly_update(
                event_type="manual_submit_completed",
                data={
                    "part_number": single_part_number,
                    "group_name": group_name,
                    "dolly_count": total_dollys,
                    "vin_count": total_vins,
                    "eol_distribution": eol_distribution
                }
            )
        except Exception as e:
            current_app.logger.warning(f"Realtime notification failed for mobile submit: {e}")
        
        current_app.logger.info(f"✅ Mobile submit tamamlandı: {total_dollys} dolly, {total_vins} VIN, PartNumber: {single_part_number}")
        
        return jsonify({
            "success": True,
            "submitted_count": total_dollys,
            "vin_count": total_vins,
            "part_number": single_part_number,
            "message": f"{total_dollys} dolly ({total_vins} VIN) başarıyla submit edildi",
            "eol_summary": eol_distribution  # Her EOL'den kaç dolly
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Mobile submit error: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            "error": "Submit başarısız",
            "retryable": True
        }), 500


@api_bp.post("/manual-collection/remove-last")
@require_forklift_auth
def manual_collection_remove_last():
    import logging
    logger = current_app.logger

    """Remove last scanned dolly from EOL group
    
    Headers:
        Authorization: Bearer <sessionToken>
    
    Request:
    {
        "group_name": "V710-MR-EOL",
        "barcode": "DOLLY456"
    }
    
    Response (Success):
    {
        "success": true,
        "dolly_no": "DOLLY456",
        "message": "Dolly çıkartıldı"
    }
    
    Response (Error):
    {
        "error": "Bu dolly taranmamış",
        "http_code": 400
    }
    """
    try:
        payload = request.get_json(force=True, silent=True) or {}
        barcode = payload.get("barcode")
        if not barcode:
            return jsonify({
                "error": "barcode gerekli",
                "retryable": True
            }), 400

        # Find dolly by barcode
        find_query = """
        SELECT TOP 1 DollyNo
        FROM DollyEOLInfo
        WHERE EOLDollyBarcode = :barcode OR DollyNo = :barcode
        """
        result = db.session.execute(db.text(find_query), {"barcode": barcode}).fetchone()
        if not result:
            return jsonify({
                "error": f"Barkod '{barcode}' sistemde bulunamadı",
                "retryable": True
            }), 404
        dolly_no = result[0]


        # 1. Barkoddan EOLName'i bul
        eol_query = """
        SELECT TOP 1 EOLName FROM DollyEOLInfo
        WHERE EOLDollyBarcode = :barcode OR DollyNo = :barcode
        """
        eol_result = db.session.execute(db.text(eol_query), {"barcode": barcode}).fetchone()
        if not eol_result:
            logger.error(f"[MANUAL_REMOVE] Barkoddan EOL grubu bulunamadı | barcode={barcode}")
            return jsonify({
                "error": f"Barkoddan EOL grubu bulunamadı",
                "retryable": True
            }), 404
        eol_name = eol_result[0]
        logger.info(f"[MANUAL_REMOVE] barcode={barcode} eol_name={eol_name}")

        # 2. O EOL grubu ve kullanıcı için en son scanned kasayı bul
        operator = get_current_forklift_user()
        last_query = """
        SELECT TOP 1 DollyNo FROM DollySubmissionHold
        WHERE Status = 'scanned' AND EOLName = :eol_name AND TerminalUser = :operator
        ORDER BY CreatedAt DESC
        """
        last_result = db.session.execute(db.text(last_query), {"eol_name": eol_name, "operator": operator}).fetchone()
        logger.info(f"[MANUAL_REMOVE] operator={operator} last_scanned_dolly={last_result[0] if last_result else None} (type={type(last_result[0]).__name__ if last_result else None}) requested_dolly={dolly_no} (type={type(dolly_no).__name__})")
        # Karşılaştırmayı hem str hem int olarak yap
        last_val = last_result[0] if last_result else None
        match = False
        if last_val is not None:
            if str(last_val) == str(dolly_no):
                match = True
            else:
                try:
                    match = int(last_val) == int(dolly_no)
                except Exception:
                    match = False
        if not last_result or not match:
            logger.warning(f"[MANUAL_REMOVE] RED: Sadece bu EOL grubunda ve bu kullanıcı tarafından en son okutulan kasayı çıkartabilirsiniz. | operator={operator} eol_name={eol_name} last_scanned_dolly={last_val} (type={type(last_val).__name__}) requested_dolly={dolly_no} (type={type(dolly_no).__name__})")
            return jsonify({
                "error": f"Sadece bu EOL grubunda ve bu kullanıcı tarafından en son okutulan kasayı çıkartabilirsiniz. (last_scanned_dolly={last_val} type={type(last_val).__name__}, requested_dolly={dolly_no} type={type(dolly_no).__name__})",
                "retryable": False
            }), 400

        # Check if scanned (güvenlik için yine de kontrol)
        check_query = """
        SELECT COUNT(*) FROM DollySubmissionHold
        WHERE DollyNo = :dolly_no AND Status = 'scanned'
        """
        count = db.session.execute(db.text(check_query), {"dolly_no": dolly_no}).scalar()
        if count == 0:
            logger.warning(f"[MANUAL_REMOVE] RED: Bu dolly taranmamış | dolly_no={dolly_no}")
            return jsonify({
                "error": "Bu dolly taranmamış",
                "retryable": True
            }), 400

        # Get current operator from session
        operator = get_current_forklift_user()

        # Delete from DollySubmissionHold
        delete_query = """
        DELETE FROM DollySubmissionHold
        WHERE DollyNo = :dolly_no AND Status = 'scanned'
        """
        db.session.execute(db.text(delete_query), {"dolly_no": dolly_no})
        db.session.commit()
        logger.info(f"[MANUAL_REMOVE] SUCCESS: Dolly çıkartıldı | operator={operator} eol_name={eol_name} dolly_no={dolly_no}")

        # Log to audit
        from ..services.audit_service import AuditService
        audit = AuditService()
        audit.log(
            action="mobile.manual_remove",
            resource="dolly",
            resource_id=dolly_no,
            actor_name=operator,
            metadata={
                "barcode": barcode
            }
        )

        return jsonify({
            "success": True,
            "dolly_no": dolly_no,
            "message": "Dolly çıkartıldı"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Manual collection remove error: {e}")
        return jsonify({
            "error": "Çıkartma başarısız",
            "retryable": True
        }), 500


# ==================== DOLLY FILLING STATUS (YÜZDE) ====================

@api_bp.get("/yuzde")
def dolly_filling_status():
    """
    Dolly dolma durumunu anlık olarak gösterir
    
    ÖNEMLI: DISTINCT VinNo kullanır - Aynı VIN'den birden fazla kayıt varsa 1 tane sayar
    
    Mantık:
    1. Her EOL grubu için şu an aktif dolly'yi bulur (en son dolly)
    2. O dolly'de kaç FARKLI VIN olduğunu sayar (DISTINCT)
    3. Bir önceki dolly'lere bakarak maksimum VIN sayısını bulur
    4. Format: "8/16" şeklinde gösterir (yüzde yok)
    5. Bekleyen dolly sayısını hesaplar
    
    Response:
    {
        "timestamp": "2025-12-25T10:30:00",
        "eol_groups": [
            {
                "eol_name": "V710-MR-EOL",
                "current_dolly": "DL-5170427",
                "current_vin_count": 8,
                "max_vin_capacity": 16,
                "vin_display": "8/16",
                "pending_dollys": 5,
                "status": "filling",
                "message": "Dolmasına 8 VIN kaldı",
                "last_vin": "VIN123456789",
                "can_scan": true
            }
        ],
        "summary": {
            "total_active_dollys": 3,
            "filling_dollys": 2,
            "full_dollys": 1,
            "empty_dollys": 0
        }
    }
    """
    try:
        # SQL query: Her EOL grubu için dolly analizi (DISTINCT VIN kullanarak)
        query = """
        WITH CurrentDollys AS (
            -- Her EOL için en son dolly'yi bul (DISTINCT VIN sayar)
            SELECT 
                EOLName,
                DollyNo,
                COUNT(DISTINCT VinNo) as CurrentVinCount,  -- DISTINCT kullan!
                MAX(InsertedAt) as LastInsertTime,
                MAX(VinNo) as LastVin
            FROM DollyEOLInfo
            GROUP BY EOLName, DollyNo
        ),
        DollyCapacities AS (
            -- Her dolly'nin kaç FARKLI VIN içerdiğini hesapla
            SELECT 
                EOLName,
                DollyNo,
                COUNT(DISTINCT VinNo) as VinCount  -- DISTINCT kullan!
            FROM DollyEOLInfo
            GROUP BY EOLName, DollyNo
        ),
        MaxCapacities AS (
            -- Her EOL grubu için maksimum VIN kapasitesini bul
            SELECT 
                EOLName,
                MAX(VinCount) as MaxVinCapacity,
                COUNT(DISTINCT DollyNo) as TotalDollys
            FROM DollyCapacities
            GROUP BY EOLName
        ),
        PendingDollys AS (
            -- DollySubmissionHold'daki bekleyen dolly'leri say
            SELECT 
                EOLName,
                COUNT(DISTINCT DollyNo) as PendingCount
            FROM DollySubmissionHold
            WHERE Status IN ('scanned', 'pending')
            GROUP BY EOLName
        )
        SELECT 
            cd.EOLName,
            cd.DollyNo as CurrentDolly,
            cd.CurrentVinCount,
            mc.MaxVinCapacity,
            mc.TotalDollys,
            ISNULL(pd.PendingCount, 0) as PendingDollys,
            cd.LastVin,
            cd.LastInsertTime
        FROM CurrentDollys cd
        LEFT JOIN MaxCapacities mc ON cd.EOLName = mc.EOLName
        LEFT JOIN PendingDollys pd ON cd.EOLName = pd.EOLName
        WHERE cd.LastInsertTime = (
            -- Sadece en son dolly'leri getir
            SELECT MAX(LastInsertTime) 
            FROM CurrentDollys cd2 
            WHERE cd2.EOLName = cd.EOLName
        )
        ORDER BY cd.EOLName, cd.DollyNo
        """
        
        result = db.session.execute(db.text(query)).fetchall()
        
        eol_groups = []
        summary = {
            "total_active_dollys": 0,
            "filling_dollys": 0,
            "full_dollys": 0,
            "empty_dollys": 0
        }
        
        for row in result:
            eol_name = row[0]
            current_dolly = row[1]
            current_vin_count = row[2]
            max_capacity = row[3]
            total_dollys = row[4]
            pending_dollys = row[5]
            last_vin = row[6]
            last_insert_time = row[7]
            
            # VIN display format: "8/16"
            vin_display = f"{current_vin_count}/{max_capacity}"
            
            # Durum hesapla
            remaining_vins = max_capacity - current_vin_count
            filling_percentage = (current_vin_count / max_capacity * 100) if max_capacity > 0 else 0
            
            # Status belirleme
            if filling_percentage >= 100:
                status = "full"
                message = "Dolly DOLU! Yeni dolly doluyor"
                can_scan = False
                summary["full_dollys"] += 1
            elif filling_percentage >= 90:
                status = "almost_full"
                message = f"Neredeyse dolu! {remaining_vins} VIN kaldı"
                can_scan = True
                summary["filling_dollys"] += 1
            elif current_vin_count > 0:
                status = "filling"
                message = f"Dolmasına {remaining_vins} VIN kaldı"
                can_scan = True
                summary["filling_dollys"] += 1
            else:
                status = "empty"
                message = "Boş dolly - İlk VIN bekleniyor"
                can_scan = True
                summary["empty_dollys"] += 1
            
            summary["total_active_dollys"] += 1
            
            eol_groups.append({
                "eol_name": eol_name,
                "current_dolly": current_dolly,
                "current_vin_count": current_vin_count,
                "max_vin_capacity": max_capacity,
                "vin_display": vin_display,
                "pending_dollys": pending_dollys,
                "total_dollys_scanned": total_dollys,
                "remaining_vins": remaining_vins,
                "status": status,
                "message": message,
                "last_vin": last_vin,
                "last_insert_time": last_insert_time.isoformat() if last_insert_time else None,
                "can_scan": can_scan
            })
        
        return jsonify({
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "eol_groups": eol_groups,
            "summary": summary
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Dolly filling status error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== PUBLIC ACTIVE SHIPMENT CHECK (NO LOGIN REQUIRED) ====================

@api_bp.get("/check-active-shipments")
def check_active_shipments():
    """
    Login olmadan aktif sevkiyat kontrolü yapar.
    Sadece var/yok bilgisi ve temel sevkiyat grup bilgilerini döner.
    
    Response:
    {
        "success": true,
        "has_active_shipments": true,
        "count": 3,
        "shipments": [
            {
                "group_name": "ABC123",
                "part_number": "ABC123",
                "total_vins": 25,
                "total_dollys": 5
            }
        ]
    }
    """
    try:
        from ..models.dolly_hold import DollySubmissionHold
        
        # Aktif sevkiyatları kontrol et (pending veya loading_completed)
        active_shipments = db.session.query(
            DollySubmissionHold.PartNumber,
            db.func.count(DollySubmissionHold.VinNo).label('TotalVINs'),
            db.func.count(db.func.distinct(DollySubmissionHold.DollyNo)).label('TotalDollys')
        ).filter(
            DollySubmissionHold.Status.in_(['pending', 'loading_completed'])
        ).group_by(
            DollySubmissionHold.PartNumber
        ).all()
        
        # Sonuçları hazırla
        shipments_list = []
        for shipment in active_shipments:
            shipments_list.append({
                "group_name": shipment.PartNumber,
                "part_number": shipment.PartNumber,
                "total_vins": shipment.TotalVINs,
                "total_dollys": shipment.TotalDollys
            })
        
        return jsonify({
            "success": True,
            "has_active_shipments": len(shipments_list) > 0,
            "count": len(shipments_list),
            "shipments": shipments_list,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Active shipments check error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "has_active_shipments": False,
            "count": 0,
            "shipments": []
        }), 500
