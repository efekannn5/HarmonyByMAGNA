import csv
import io
import json
import os
import secrets
import re
from datetime import datetime, timedelta

from flask import Blueprint, Response, current_app, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, text, case, or_
from markupsafe import Markup, escape

from ..extensions import db
from ..models import AuditLog, DollyEOLInfo, DollyEOLInfoBackup, TerminalBarcodeSession, TerminalDevice, UserAccount, UserRole
from ..models.sefer import SeferDollyEOL
from ..services import AuditService, DollyService
from ..modules.operator_edit import add_manual_dolly, remove_last_dolly_in_eol
from ..services.realtime_service import RealtimeService
from ..utils.auth import role_required
from ..utils.security import hash_password

dashboard_bp = Blueprint("dashboard", __name__)
audit_service = AuditService()


def _get_production_date_from_backup(dolly_no: str):
    """
    DollyEOLInfoBackup tablosundan üretim tarihini parametrik sorgu ile al.
    ⚠️ CRITICAL: Sadece parametrik sorgu kullan, sistem yavaşlar!
    """
    if not dolly_no:
        return None
    try:
        backup_record = DollyEOLInfoBackup.query.filter_by(DollyNo=dolly_no).first()
        if backup_record and backup_record.EOLDATE:
            return backup_record.EOLDATE
    except Exception as e:
        current_app.logger.warning(f"⚠️ Backup'tan üretim tarihi alınamadı (DollyNo={dolly_no}): {e}")
    return None


@dashboard_bp.get("/")
@login_required
def dashboard_home():
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    
    # Check user role to show appropriate dashboard
    user_role = (current_user.role.Name if current_user.role else "").lower()
    
    if user_role == "operator":
        # Web operator view - show pending dollys from DollySubmissionHold
        from ..models.dolly_hold import DollySubmissionHold
        from ..models.group import DollyGroup, DollyGroupEOL
        from ..models.pworkstation import PWorkStation
        
        # Get pending submissions grouped by PartNumber ONLY
        # Include both 'pending' and 'loading_completed' status
        pending_submissions = db.session.query(
            DollySubmissionHold.PartNumber,
            db.func.max(DollySubmissionHold.CustomerReferans).label('CustomerReferans'),
            db.func.max(DollySubmissionHold.EOLName).label('EOLName'),
            db.func.count(DollySubmissionHold.VinNo).label('TotalVINs'),
            db.func.count(db.func.distinct(DollySubmissionHold.DollyNo)).label('TotalDollys'),
            db.func.min(DollySubmissionHold.CreatedAt).label('CreatedAt')
        ).filter(
            DollySubmissionHold.Status.in_(['pending', 'loading_completed'])
        ).group_by(
            DollySubmissionHold.PartNumber
        ).order_by(
            db.desc(db.func.min(DollySubmissionHold.CreatedAt))
        ).all()
        
        # Convert to dict for template (compatible with existing template)
        from datetime import datetime
        pending_tasks = []
        
        for p in pending_submissions:
            # Her part_number için ShippingTag'leri kontrol et
            # Bu part_number'a ait EOL'leri bul
            eol_names_query = db.session.query(
                db.func.distinct(DollySubmissionHold.EOLName)
            ).filter(
                DollySubmissionHold.PartNumber == p.PartNumber,
                DollySubmissionHold.Status.in_(['pending', 'loading_completed'])
            ).all()
            
            eol_names = [eol[0] for eol in eol_names_query if eol[0]]
            
            # EOL'ler için ShippingTag'leri al
            shipping_tags = set()
            group_ids = set()
            if eol_names:
                eol_stations = db.session.query(PWorkStation).filter(
                    PWorkStation.PWorkStationName.in_(eol_names)
                ).all()
                
                for eol in eol_stations:
                    group_eols = db.session.query(DollyGroupEOL).filter(
                        DollyGroupEOL.PWorkStationId == eol.Id
                    ).all()
                    
                    for ge in group_eols:
                        if ge.ShippingTag:  # NULL kontrolü
                            shipping_tags.add(ge.ShippingTag)
                        if ge.GroupId:
                            group_ids.add(ge.GroupId)

            group_names = []
            if group_ids:
                groups = db.session.query(DollyGroup).filter(DollyGroup.Id.in_(group_ids)).all()
                group_names = sorted({g.GroupName for g in groups if g.GroupName})
            
            # ✅ ETİKET SİSTEMİ: Etiketlere göre group_tag belirle
            # 🟰 'irsaliye': Sadece manuel irsaliye butonu göster
            # 🟠 'both' = asn+irsaliye: Hem ASN hem manuel irsaliye butonları göster
            # ❌ 'asn': Kullanılmıyor (tek başına asn etiketi yok, both kullanılır)
            has_asn = 'both' in shipping_tags  # Sadece 'both' (asn+irsaliye) etiketli varsa ASN butonu
            has_irsaliye = any(tag in ['irsaliye', 'both'] for tag in shipping_tags)
            
            if not shipping_tags:
                group_tag = 'both'
            elif has_asn and has_irsaliye:
                group_tag = 'both'
            elif has_asn:
                group_tag = 'asn'
            elif has_irsaliye:
                group_tag = 'irsaliye'
            else:
                group_tag = 'both'
            
            if group_names:
                display_name = " / ".join(group_names)
            else:
                display_name = " / ".join(sorted({name for name in eol_names if name})) if eol_names else p.PartNumber

            pending_tasks.append({
                'part_number': p.PartNumber,
                'display_name': display_name,
                'customer_referans': p.CustomerReferans,
                'eol_name': p.EOLName,
                'total_items': p.TotalVINs,
                'total_dollys': p.TotalDollys,
                'created_at': p.CreatedAt if isinstance(p.CreatedAt, datetime) else datetime.now(),
                'status': 'pending',
                'assigned_to': None,
                'group_tag': group_tag,
                'can_submit_asn': has_asn,
                'can_submit_irsaliye': has_irsaliye
            })

        # Aynı display_name için sıra numarası ekle (örn: GroupA-2)
        name_counts = {}
        for task in pending_tasks:
            base = task.get('display_name') or task.get('part_number')
            name_counts[base] = name_counts.get(base, 0) + 1
            if name_counts[base] > 1:
                task['display_name'] = f"{base}-{name_counts[base]}"
        
        return render_template(
            "dashboard/operator_index.html",
            pending_tasks=pending_tasks,
            assigned_tasks=[],
            completed_tasks=[],
            active_groups=[],
            title="Web Operatör Paneli",
        )
    else:
        # Admin view - show all data with pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)  # Varsayılan 50 kayıt
        
        # Limit per_page to reasonable values
        per_page = min(per_page, 200)  # Max 200
        per_page = max(per_page, 10)   # Min 10
        
        # PERFORMANS: Her tablo için ayrı limit (varsayılan 50)
        default_limit = 50
        
        # Get paginated data
        from ..models.dolly import DollyEOLInfo
        from ..models.dolly_hold import DollySubmissionHold
        from ..models.web_operator_task import WebOperatorTask
        
        # PERFORMANS: Her tablo için LIMIT 50 uygula
        
        # DollyEOLInfo - EOL'de bekleyen dollyler (LIMIT 50)
        eol_query = db.session.query(DollyEOLInfo).order_by(
            DollyEOLInfo.InsertedAt.desc()
        )
        total_eol = eol_query.count()
        eol_dollys = eol_query.limit(default_limit).all()
        
        # DollySubmissionHold - Terminal bekleyen dollyler (LIMIT 50)
        hold_query = db.session.query(DollySubmissionHold).filter(
            DollySubmissionHold.Status.in_(['pending', 'scanned', 'loading_completed'])
        ).order_by(
            DollySubmissionHold.CreatedAt.desc()
        )
        total_hold = hold_query.count()
        hold_dollys = hold_query.limit(default_limit).all()
        
        # Groups listesi - LIMIT 50 (legacy compatibility için)
        groups_raw = db.session.query(DollyEOLInfo).order_by(
            DollyEOLInfo.DollyNo.asc()
        ).limit(default_limit).all()
        groups = [service._to_queue_entry(record) for record in groups_raw]
        
        # Filtre parametreleri (admin paneli için)
        filters = {
            "PartNumber": request.args.get("filter_part_number", "").strip(),
            "Status": request.args.get("filter_status", "").strip(),
            "AssignedTo": request.args.get("filter_assigned", "").strip(),
            "GroupTag": request.args.get("filter_group_tag", "").strip(),
            "CreatedAt": request.args.get("filter_created_at", "").strip(),
        }
        operator_tasks_query = db.session.query(WebOperatorTask)
        if filters["PartNumber"]:
            operator_tasks_query = operator_tasks_query.filter(WebOperatorTask.PartNumber.ilike(f"%{filters['PartNumber']}%"))
        if filters["Status"]:
            operator_tasks_query = operator_tasks_query.filter(WebOperatorTask.Status.ilike(f"%{filters['Status']}%"))
        if filters["AssignedTo"]:
            operator_tasks_query = operator_tasks_query.filter(WebOperatorTask.AssignedTo == filters["AssignedTo"])
        if filters["GroupTag"]:
            operator_tasks_query = operator_tasks_query.filter(WebOperatorTask.GroupTag.ilike(f"%{filters['GroupTag']}%"))
        if filters["CreatedAt"]:
            try:
                from datetime import datetime
                date_val = datetime.strptime(filters["CreatedAt"], "%Y-%m-%d")
                operator_tasks_query = operator_tasks_query.filter(db.func.date(WebOperatorTask.CreatedAt) == date_val.date())
            except Exception:
                pass
        operator_tasks_raw = operator_tasks_query.order_by(WebOperatorTask.CreatedAt.desc()).limit(default_limit).all()
        total_tasks = operator_tasks_query.count()
        # Sondan başa sıralama: en yeni en üstte
        operator_tasks_raw = sorted(operator_tasks_raw, key=lambda t: t.CreatedAt or t.UpdatedAt or 0, reverse=True)
        operator_tasks = [service._to_web_operator_task_entry(task) for task in operator_tasks_raw]
        for task_entry in operator_tasks[:default_limit]:
            task_entry.hold_entries = service.list_hold_entries_by_part_number(task_entry.part_number)
        
        # Pagination bilgisi - basitleştirilmiş (her tablo 50 kayıt gösterir)
        pagination_info = {
            'total_eol': total_eol,
            'total_hold': total_hold,
            'total_tasks': total_tasks,
            'shown_limit': default_limit,
        }
        
        return render_template(
            "dashboard/index.html",
            groups=groups,
            hold_entries=hold_dollys,
            eol_dollys=eol_dollys,
            operator_tasks=operator_tasks,
            pagination=pagination_info,
            filters=filters,
            title="Dolly Sıralama",
        )


@dashboard_bp.get("/settings")
@login_required
@role_required("admin")
def settings_home():
    return render_template("dashboard/settings.html", title="Ayarlar")


@dashboard_bp.get("/groups/manage")
@login_required
@role_required("admin")
def manage_groups_view():
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    definitions = service.list_group_definitions()
    eol_candidates = service.list_eol_candidates()
    message = request.args.get("message")
    error = request.args.get("error")
    return render_template(
        "dashboard/groups.html",
        title="Grup Yönetimi",
        definitions=definitions,
        eol_candidates=eol_candidates,
        message=message,
        error=error,
    )


@dashboard_bp.post("/groups/manage")
@login_required
@role_required("admin")
def create_group_action():
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()
    eol_ids = request.form.getlist("eol_ids")
    if not name:
        return redirect(url_for("dashboard.manage_groups_view", error="Grup adı zorunludur."))
    if not eol_ids:
        return redirect(url_for("dashboard.manage_groups_view", error="En az bir EOL seçmelisiniz."))
    entries = []
    try:
        for value in eol_ids:
            tag = (request.form.get(f"tag_{value}") or "both").lower()
            entries.append({"id": int(value), "tag": tag})
    except ValueError:
        return redirect(url_for("dashboard.manage_groups_view", error="Geçersiz EOL seçimi."))
    try:
        group_id = service.create_group(name, description or None, entries, actor_name="dashboard")
        
        # Emit real-time update for new group
        RealtimeService.emit_group_created(group_id=group_id, group_name=name)
        
    except (ValueError, RuntimeError) as exc:
        return redirect(url_for("dashboard.manage_groups_view", error=str(exc)))
    return redirect(url_for("dashboard.manage_groups_view", message="Grup oluşturuldu."))


@dashboard_bp.post("/groups/edit/<int:group_id>")
@login_required
@role_required("admin")
def edit_group_action(group_id: int):
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()
    eol_ids = request.form.getlist("eol_ids")
    
    if not name:
        return redirect(url_for("dashboard.manage_groups_view", error="Grup adı zorunludur."))
    if not eol_ids:
        return redirect(url_for("dashboard.manage_groups_view", error="En az bir EOL seçmelisiniz."))
    
    entries = []
    try:
        for value in eol_ids:
            tag = (request.form.get(f"tag_{value}") or "both").lower()
            entries.append({"id": int(value), "tag": tag})
    except ValueError:
        return redirect(url_for("dashboard.manage_groups_view", error="Geçersiz EOL seçimi."))
    
    try:
        result = service.update_group(group_id, name, description or None, entries, actor_name=current_user.Username)
        if result:
            return redirect(url_for("dashboard.manage_groups_view", message="Grup güncellendi."))
        else:
            return redirect(url_for("dashboard.manage_groups_view", error="Grup bulunamadı."))
    except (ValueError, RuntimeError) as exc:
        return redirect(url_for("dashboard.manage_groups_view", error=str(exc)))


@dashboard_bp.post("/groups/delete/<int:group_id>")
@login_required
@role_required("admin")
def delete_group_action(group_id: int):
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    try:
        if service.delete_group(group_id, actor_name=current_user.Username):
            return redirect(url_for("dashboard.manage_groups_view", message="Grup silindi."))
        else:
            return redirect(url_for("dashboard.manage_groups_view", error="Grup bulunamadı."))
    except Exception as exc:
        return redirect(url_for("dashboard.manage_groups_view", error=f"Silme hatası: {str(exc)}"))


@dashboard_bp.get("/manual-collection")
@login_required
@role_required("operator")
def manual_collection():
    """Manuel dolly collection page - EOL bazlı gruplama (Tablo görünümü)"""
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    active_groups = service.get_active_groups()
    # Get all available dollys grouped by EOL (en çok dolly olan EOL üstte)
    eol_dollys = service.get_dollys_by_eol_for_collection()
    
    return render_template(
        "dashboard/manual_collection_table.html",
        active_groups=active_groups,
        eol_dollys=eol_dollys,
        title="Manuel Dolly Toplama"
    )


# NEW: Operator shipment routes
@dashboard_bp.get("/operator/shipments")
@login_required
@role_required("operator")
def operator_shipments():
    """Show pending shipments waiting for operator to complete"""
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    pending_shipments = service.list_pending_shipments()
    
    return render_template(
        "dashboard/operator_shipments.html",
        pending_shipments=pending_shipments,
        title="Bekleyen Sevkiyatlar"
    )


@dashboard_bp.get("/api/operator/active-tasks-status")
@login_required
@role_required("operator")
def api_operator_active_tasks_status():
    """
    Real-time için aktif görevlerin durumunu döndürür.
    3 saniyede bir polling yapılacak.
    Operator index sayfası için pending_tasks verisi.
    """
    try:
        from ..models.dolly_hold import DollySubmissionHold
        
        # Operator index'teki aynı query ile aktif görevleri al
        pending_submissions = db.session.query(
            DollySubmissionHold.PartNumber,
            db.func.max(DollySubmissionHold.CustomerReferans).label('CustomerReferans'),
            db.func.max(DollySubmissionHold.EOLName).label('EOLName'),
            db.func.count(DollySubmissionHold.VinNo).label('TotalVINs'),
            db.func.count(db.func.distinct(DollySubmissionHold.DollyNo)).label('TotalDollys'),
            db.func.min(DollySubmissionHold.CreatedAt).label('CreatedAt')
        ).filter(
            DollySubmissionHold.Status.in_(['pending', 'loading_completed'])
        ).group_by(
            DollySubmissionHold.PartNumber
        ).order_by(
            db.desc(db.func.min(DollySubmissionHold.CreatedAt))
        ).all()
        
        # Aktif görevlerin part_number'larını ve timestamp'lerini döndür
        active_tasks = []
        for p in pending_submissions:
            active_tasks.append({
                "part_number": p.PartNumber,
                "customer_referans": p.CustomerReferans,
                "eol_name": p.EOLName,
                "total_vins": p.TotalVINs,
                "total_dollys": p.TotalDollys,
                "created_at": p.CreatedAt.isoformat() if p.CreatedAt else ""
            })
        
        current_app.logger.debug(f"📊 API Status: {len(active_tasks)} aktif görev")
        
        return jsonify({
            "success": True,
            "count": len(active_tasks),
            "tasks": active_tasks,
            "server_time": datetime.now().isoformat()
        })
    
    except Exception as e:
        current_app.logger.error(f"❌ Aktif görev status hatası: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@dashboard_bp.post("/operator/shipments/complete")
@login_required
@role_required("operator")
def operator_complete_shipment():
    """Complete a shipment by adding Sefer No, Plaka, and sending ASN/Irsaliye"""
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    
    loading_session_id = request.form.get("loading_session_id")
    sefer_numarasi = request.form.get("sefer_numarasi", "").strip()
    plaka_no = request.form.get("plaka_no", "").strip()
    shipping_type = request.form.get("shipping_type")
    selected_dolly_ids = request.form.getlist("selected_dolly_ids")  # Checkbox selections
    
    if not all([loading_session_id, sefer_numarasi, plaka_no, shipping_type]):
        return redirect(url_for("dashboard.operator_shipments", error="Tüm alanları doldurun"))
    
    # Convert selected IDs to integers
    try:
        selected_dolly_ids = [int(id) for id in selected_dolly_ids] if selected_dolly_ids else None
    except ValueError:
        return redirect(url_for("dashboard.operator_shipments", error="Geçersiz dolly seçimi"))
    
    try:
        result = service.operator_complete_shipment(
            loading_session_id=loading_session_id,
            sefer_numarasi=sefer_numarasi,
            plaka_no=plaka_no,
            shipping_type=shipping_type,
            operator_user=current_user.Username,
            selected_dolly_ids=selected_dolly_ids
        )
        
        partial_msg = " (Partial Shipment)" if result.get("partialShipment") else ""
        return redirect(url_for(
            "dashboard.operator_shipments", 
            message=f"Sevkiyat tamamlandı: {result['dollyCount']} dolly işlendi{partial_msg}"
        ))
    except ValueError as e:
        return redirect(url_for("dashboard.operator_shipments", error=str(e)))
    except RuntimeError as e:
        return redirect(url_for("dashboard.operator_shipments", error=f"Sistem hatası: {str(e)}. Lütfen tekrar deneyin."))


@dashboard_bp.get("/operator/task/<part_number>")
@login_required
@role_required("operator")
def operator_task_detail(part_number: str):
    try:
        from ..models.dolly_hold import DollySubmissionHold
        from collections import defaultdict
        
        current_app.logger.info(f"🔍 Görev detayları istendi: {part_number}")
        
        # Get all VINs for this PartNumber from DollySubmissionHold
        # Include both 'pending' and 'loading_completed' status
        submissions_raw = db.session.query(DollySubmissionHold).filter(
            DollySubmissionHold.PartNumber == part_number,
            DollySubmissionHold.Status.in_(['pending', 'loading_completed'])
        ).all()
        
        # Her submission için InsertedAt bilgisini hazırla
        submissions_with_dates = []
        for sub in submissions_raw:
            # InsertedAt DollySubmissionHold'da direkt mevcut (DollyEOLInfo'dan kopyalandı)
            submissions_with_dates.append({
                'submission': sub,
                'inserted_at': sub.InsertedAt or sub.CreatedAt,  # Fallback to CreatedAt if InsertedAt missing
                'dolly_no': sub.DollyNo or '',
                'vin_no': sub.VinNo or ''
            })
        
        # ✅ SIRALAMA (Manuel dolly toplama ile aynı): 1. InsertedAt, 2. VinNo (DollyNo sıralamadan çıkarıldı)
        submissions_with_dates.sort(key=lambda x: (
            x['inserted_at'] or datetime.min,
            x['vin_no']
        ))
        submissions = [s['submission'] for s in submissions_with_dates]  # SIRALI!
        
        current_app.logger.info(f"📦 {len(submissions)} submission bulundu")
        
        if not submissions:
            current_app.logger.warning(f"⚠️ {part_number} için submission bulunamadı, anasayfaya yönlendiriliyor")
            return redirect(url_for("dashboard.dashboard_home"))
        
        # Group by DollyNo for display
        dollys_grouped = defaultdict(list)
        # Group by DollyNo for display
        dollys_grouped = defaultdict(list)
        for sub in submissions:
            dollys_grouped[sub.DollyNo].append({
                'id': sub.Id,
                'vin_no': sub.VinNo,
                'dolly_no': sub.DollyNo,
                'customer_referans': sub.CustomerReferans,
                'eol_name': sub.EOLName,
                'scan_order': sub.ScanOrder,
                'dolly_order_no': sub.DollyOrderNo,  # ÇOK ÖNEMLİ: Bu CEVA'ya gönderilecek!
                'created_at': sub.CreatedAt,
                'status': sub.Status,  # pending, loading_completed, etc.
                'part_number': sub.CustomerReferans
            })
        
        # Task metadata (compatible with template)
        first_sub = submissions[0]
        
        # Grup etiketlerini kontrol et - tüm EOL'ler için ShippingTag kontrolü
        from ..models.group import DollyGroupEOL
        from ..models.pworkstation import PWorkStation
        
        # Bu part_number için kullanılan EOL'leri bul
        unique_eol_names = set(sub.EOLName for sub in submissions if sub.EOLName)
        
        # Her EOL için ShippingTag'leri al
        shipping_tags = set()
        if unique_eol_names:
            eol_stations = db.session.query(PWorkStation).filter(
                PWorkStation.PWorkStationName.in_(unique_eol_names)
            ).all()
            
            current_app.logger.info(f"🔍 Part {part_number} için {len(eol_stations)} EOL bulundu")
            
            for eol in eol_stations:
                # Bu EOL için tüm grup etiketlerini al
                group_eols = db.session.query(DollyGroupEOL).filter(
                    DollyGroupEOL.PWorkStationId == eol.Id
                ).all()
                
                for ge in group_eols:
                    if ge.ShippingTag:  # NULL kontrolü ekle
                        shipping_tags.add(ge.ShippingTag)
                        current_app.logger.info(f"  📌 EOL {eol.PWorkStationName}: ShippingTag = {ge.ShippingTag}")
        
        current_app.logger.info(f"📊 Toplanan ShippingTag'ler: {shipping_tags}")
        
        # ✅ ETİKET SİSTEMİ: Etiketlere göre buton durumlarını belirle
        # 🟰 'irsaliye': Sadece manuel irsaliye butonu göster
        # 🟠 'both' = asn+irsaliye: Hem ASN hem manuel irsaliye butonları göster
        # ❌ 'asn': Kullanılmıyor (tek başına asn etiketi yok, both kullanılır)
        has_asn = 'both' in shipping_tags  # Sadece 'both' (asn+irsaliye) etiketli varsa ASN butonu
        has_irsaliye = any(tag in ['irsaliye', 'both'] for tag in shipping_tags)
        
        current_app.logger.info(f"✅ has_asn={has_asn}, has_irsaliye={has_irsaliye}")
        
        # Eğer hiç tag yoksa varsayılan olarak both kabul et
        if not shipping_tags:
            has_asn = True
            has_irsaliye = True
            group_tag = 'both'
            current_app.logger.warning(f"⚠️ ShippingTag bulunamadı, varsayılan 'both' kullanılıyor")
        elif has_asn and has_irsaliye:
            group_tag = 'both'
        elif has_asn:
            group_tag = 'asn'
        elif has_irsaliye:
            group_tag = 'irsaliye'
        else:
            group_tag = 'both'
        
        current_app.logger.info(f"🏷️ Final group_tag={group_tag}, can_submit_asn={has_asn}, can_submit_irsaliye={has_irsaliye}")
        
        task = {
            'part_number': part_number,
            'customer_referans': first_sub.CustomerReferans,
            'eol_name': first_sub.EOLName,
            'total_items': len(submissions),
            'processed_items': 0,  # Will be calculated if needed
            'created_at': first_sub.CreatedAt if hasattr(first_sub, 'CreatedAt') else datetime.now(),
            'updated_at': first_sub.UpdatedAt if hasattr(first_sub, 'UpdatedAt') else datetime.now(),
            'status': 'pending',
            'assigned_to': None,
            'assigned_user_name': None,
            'group_tag': group_tag,
            'can_submit_asn': has_asn,
            'can_submit_irsaliye': has_irsaliye,
            'metadata': None
        }
        
        # Convert to list of dicts with dolly info - SORTED BY DollyOrderNo
        dolly_list = []
        for dolly_no, entries in sorted(dollys_grouped.items(), key=lambda x: min((e['dolly_order_no'] or 999999) for e in x[1])):
            # Use first entry for representative data
            first_entry = entries[0]
            dolly_order_no = first_entry['dolly_order_no']
            
            dolly_dict = {
                'dolly_no': dolly_no,
                'scan_order': first_entry['scan_order'],  # Seçim sırası (internal)
                'dolly_order_no': dolly_order_no,  # ÇOK ÖNEMLİ: CEVA'ya bu gönderilecek!
                'vin_count': len(entries),
                'vin_entries': entries,  # List of VIN dicts
                'hold_entries': entries,  # Alias for compatibility
                'vins': [e['vin_no'] for e in entries],  # VIN list
                'eol_name': first_entry['eol_name'],
                'customer_referans': first_entry['customer_referans'],
                'status': 'pending',  # All are pending in DollySubmissionHold
                'part_number': first_entry['customer_referans']
            }
            dolly_list.append(dolly_dict)
            
            # DEBUG LOG
            current_app.logger.info(f"📋 Dolly added: DollyNo={dolly_no}, DollyOrderNo={dolly_order_no}, ScanOrder={first_entry['scan_order']}, VINs={len(entries)}")
        
        # ✅ TÜM EOL'lerdeki sıradaki dollyler gösterilsin (sadece task EOL'leri değil)
        service = DollyService(current_app.config.get("APP_CONFIG", {}))
        next_dollys = service.get_next_dollys_for_eols(eol_names=None, part_number=part_number, limit=100)
        current_app.logger.info(f"📦 Received {len(next_dollys)} next dollys from ALL EOLs")
        
        message = request.args.get("message")
        error = request.args.get("error")
        
        # Always render embed-friendly template (tek form)
        # Always render embed-friendly template (tek form)
        return render_template(
            "dashboard/operator_task_detail_embed.html",
            task=task,
            dolly_list=dolly_list,
            next_dollys=next_dollys,
            title=f"Task: {part_number}",
            message=message,
            error=error,
        )
    
    except Exception as e:
        current_app.logger.error(f"❌ Görev detayları yüklenirken hata: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        # Embed mode için hata sayfası
        return render_template(
            "dashboard/operator_task_detail_embed.html",
            task=None,
            dolly_list=[],
            next_dollys=[],
            title=f"Hata - {part_number}",
            error=f"Görev detayları yüklenemedi: {str(e)}"
        ), 500


@dashboard_bp.post("/operator/task/<part_number>/send-asn")
@login_required
@role_required("operator")
def operator_send_asn(part_number: str):
    """ASN Gönderme - CEVA API'ye gönderim ve SeferDollyEOL'a kayıt"""
    try:
        from ..models.dolly_hold import DollySubmissionHold
        from ..models.dolly import DollyEOLInfo
        from ..models.sefer import SeferDollyEOL
        from ..services.ceva_service import CevaService, ASNItemDetail
        from ..services.audit_service import AuditService
        from ..models.group import DollyGroupEOL
        from ..models.pworkstation import PWorkStation
        
        # Get form data
        sefer_numarasi = request.form.get('sefer_numarasi', '').strip()
        plaka_no = request.form.get('plaka_no', '').strip()
        irsaliye_no = request.form.get('irsaliye_no', '').strip()  # İrsaliye numarası
        trip_reason_code = request.form.get('trip_reason_code', 'TRC-00').strip()  # Hata kodu
        shipping_type = request.form.get('shipping_type', 'asn').strip()  # 'asn' veya 'irsaliye'
        
        if not sefer_numarasi or not plaka_no or not irsaliye_no:
            return jsonify({'success': False, 'error': 'Sefer numarası, plaka numarası ve irsaliye numarası zorunludur'}), 400
        
        # Get all pending submissions for this PartNumber - ORDER BY InsertedAt + VinNo (SIRA ÇOK ÖNEMLİ!)
        all_submissions_raw = db.session.query(DollySubmissionHold).filter_by(
            PartNumber=part_number,
            Status='pending'
        ).all()
        
        # Her submission için InsertedAt bilgisini hazırla
        submissions_with_dates = []
        for sub in all_submissions_raw:
            # InsertedAt DollySubmissionHold'da direkt mevcut (DollyEOLInfo'dan kopyalandı)
            submissions_with_dates.append({
                'submission': sub,
                'inserted_at': sub.InsertedAt or sub.CreatedAt,  # Fallback to CreatedAt if InsertedAt missing
                'dolly_no': sub.DollyNo or '',
                'vin_no': sub.VinNo or ''
            })
        
        # ✅ SIRALAMA (Manuel dolly toplama ile aynı): 1. InsertedAt, 2. VinNo (DollyNo sıralamadan çıkarıldı)
        submissions_with_dates.sort(key=lambda x: (
            x['inserted_at'] or datetime.min,
            x['vin_no']
        ))
        all_submissions = [s['submission'] for s in submissions_with_dates]  # SIRALI!
        
        if not all_submissions:
            return jsonify({'success': False, 'error': 'Bu PartNumber için pending kayıt bulunamadı'}), 404
        
        # ShippingTag filtrelemesi - shipping_type'a göre filtreleme yap
        submissions = []
        tag_debug = []  # Debug için etiket bilgileri
        for sub in all_submissions:
            # Bu submission'ın EOL'ü için ShippingTag kontrolü
            if sub.EOLName:
                eol_station = db.session.query(PWorkStation).filter_by(
                    PWorkStationName=sub.EOLName
                ).first()
                
                if eol_station:
                    # Bu EOL için grup etiketlerini kontrol et
                    group_eol = db.session.query(DollyGroupEOL).filter_by(
                        PWorkStationId=eol_station.Id
                    ).first()
                    
                    if group_eol:
                        tag = group_eol.ShippingTag
                        # ✅ Case-insensitive ve trim yaparak karşılaştır
                        tag_normalized = tag.lower().strip() if tag else None
                        tag_debug.append(f"{sub.EOLName}={tag}({tag_normalized})")  # Debug
                        
                        # ✅ ETİKET SİSTEMİ (SOVOS entegrasyonu olmadan):
                        # 🟰 'irsaliye': Sadece manuel irsaliye (Görevi Manuel Bitir ile kapatılır)
                        # 🟠 'both' = asn+irsaliye: Şu an ASN'e gider (ileride SOVOS → ASN)
                        # ❌ 'asn': Kullanılmıyor (tek başına asn etiketi yok, both kullanılır)
                        # 
                        # 🔮 İLERİDE (SOVOS entegrasyonu gelince):
                        # 'both' (asn+irsaliye) etiketli olanlar → İlk İrsaliye'ye gönderilecek (SOVOS)
                        # → İrsaliye No gelecek → Sonra ASN gönderilecek (İrsaliye No ile)
                        if shipping_type == 'asn':
                            # ASN: Sadece 'both' (asn+irsaliye) etiketli olanları al
                            if tag_normalized == 'both':
                                submissions.append(sub)
                        elif shipping_type == 'irsaliye':
                            # Manuel İrsaliye: Sadece 'irsaliye' etiketli olanları al
                            # ('both' zaten ASN'e gidiyor)
                            if tag_normalized == 'irsaliye':
                                submissions.append(sub)
                        else:
                            # Bilinmeyen tip - hepsini al
                            submissions.append(sub)
                    else:
                        # Grup etiketi yoksa varsayılan olarak al
                        tag_debug.append(f"{sub.EOLName}=NO_TAG")  # Debug
                        submissions.append(sub)
                else:
                    # EOL bulunamadıysa varsayılan olarak al
                    tag_debug.append(f"{sub.EOLName}=NO_STATION")  # Debug
                    submissions.append(sub)
            else:
                # EOL ismi yoksa varsayılan olarak al
                tag_debug.append("NO_EOL_NAME")  # Debug
                submissions.append(sub)
        
        current_app.logger.info(f"🏷️ Tag Debug: {', '.join(tag_debug)}")
        current_app.logger.info(f"📊 Filtreleme: {len(all_submissions)} toplam -> {len(submissions)} {shipping_type} etiketli")
        
        if not submissions:
            return jsonify({
                'success': False, 
                'error': f'Bu PartNumber için {shipping_type.upper()} etiketli pending kayıt bulunamadı. Etiketler: {", ".join(set(tag_debug))}'
            }), 404
        
        current_app.logger.info(f"📤 ASN Gönderme başlatıldı: PartNumber={part_number}, Sefer={sefer_numarasi}, Plaka={plaka_no}, İrsaliye={irsaliye_no}, TripReasonCode={trip_reason_code}, ShippingType={shipping_type}, VIN Count={len(submissions)}/{len(all_submissions)}")
        
        # LOG: VIN sırasını doğrula (InsertedAt sıralı - Manuel dolly toplama ile aynı)
        vin_order = [f"{i+1}. {sub.EOLName or 'UNKNOWN'} -> {sub.DollyNo}/{sub.VinNo}" for i, sub in enumerate(submissions)]
        current_app.logger.info(f"🔢 VIN SIRASI (InsertedAt sıralı - Manuel dolly toplama ile aynı):\n" + "\n".join(vin_order))
        
        # === STEP 1: Prepare ASN data for CEVA (SIRALI!) ===
        asn_details = []
        
        # ✅ Her dolly içindeki VIN sırasını takip et (DollyEye)
        # DollyEye = Aynı dolly içindeki VIN'in sırası (1, 2, 3, ...)
        dolly_vin_counter = {}  # {DollyNo: kaçıncı VIN}
        
        for idx, sub in enumerate(submissions):
            # Bu dolly'de kaçıncı VIN olduğunu bul
            if sub.DollyNo not in dolly_vin_counter:
                dolly_vin_counter[sub.DollyNo] = 0
            
            dolly_vin_counter[sub.DollyNo] += 1
            dolly_eye_number = dolly_vin_counter[sub.DollyNo]  # Bu dolly içinde kaçıncı VIN (1, 2, 3, ...)
            
            asn_detail = ASNItemDetail(
                dolly_number=str(sub.DollyOrderNo),  # ÇOK ÖNEMLİ: DollyOrderNo gönder!
                vin_number=sub.VinNo,
                part_number=sub.CustomerReferans,  # ✅ CEVA'ya CustomerReferans gönder (EOL/Grup ismi)
                qty=sub.Adet or 1,
                process_time=sub.CreatedAt or datetime.now(),  # ✅ Türkiye yerel saati
                waybill_number=irsaliye_no,  # ÇOK ÖNEMLİ: Formdan gelen İrsaliye No TÜM dollyler için aynı!
                trip_reason_code=trip_reason_code,  # Formdan gelen hata kodu
                dolly_eye=dolly_eye_number  # ✅ ÇOK ÖNEMLİ: Bu dolly içinde kaçıncı VIN (1, 2, 3, ..., 8)
            )
            asn_details.append(asn_detail)
            
            # LOG: Her VIN için detay
            current_app.logger.info(
                f"  [{idx+1}] DollyNo={sub.DollyNo}, DollyOrderNo={sub.DollyOrderNo}, VIN={sub.VinNo}, "
                f"CustomerReferans={sub.CustomerReferans}, PartNumber={sub.PartNumber}, Waybill={irsaliye_no}, "
                f"DollyEye={dolly_eye_number}/{dolly_vin_counter[sub.DollyNo]}, ProcessTime={asn_detail.process_time.strftime('%Y-%m-%d')}"
            )
        
        current_app.logger.info(f"📋 ASN Details hazırlandı: {len(asn_details)} adet VIN (SIRALI), İrsaliye={irsaliye_no}")
        
        # === STEP 2: Send to CEVA API ===
        try:
            ceva_service = CevaService(current_app.config.get("APP_CONFIG", {}))
            ceva_response = ceva_service.send_asn(
                trip_code=sefer_numarasi,
                asn_details=asn_details
            )
            
            current_app.logger.info(f"🌐 CEVA Response: successful={ceva_response.successful}, message={ceva_response.result_description}")
            
            # Check if CEVA accepted the ASN
            if not ceva_response.successful:
                # CEVA rejected - DO NOT save to database
                current_app.logger.error(f"❌ CEVA ASN reddedildi: {ceva_response.result_description}")
                
                # Audit log
                audit = AuditService()
                audit.log(
                    action="asn.send.failed",
                    resource="ceva_asn",
                    resource_id=sefer_numarasi,
                    actor_name=current_user.Username,
                    metadata={
                        "part_number": part_number,
                        "sefer_numarasi": sefer_numarasi,
                        "plaka_no": plaka_no,
                        "vin_count": len(submissions),
                        "shipping_type": shipping_type,
                        "ceva_error": ceva_response.result_description
                    }
                )
                
                return jsonify({
                    'success': False,
                    'error': f'CEVA ASN reddedildi: {ceva_response.result_description}',
                    'ceva_message': ceva_response.result_description
                }), 400
                
        except Exception as ceva_error:
            current_app.logger.error(f"❌ CEVA API hatası: {ceva_error}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            return jsonify({
                'success': False, 
                'error': f'CEVA API bağlantı hatası: {str(ceva_error)}'
            }), 500
        
        # === STEP 3: CEVA accepted - Save to SeferDollyEOL ===
        current_app.logger.info(f"✅ CEVA ASN kabul edildi - SeferDollyEOL'a kaydediliyor...")
        
        transferred_count = 0
        
        for sub in submissions:
            # 📅 Üretim tarihini backup tablosundan al
            production_date = _get_production_date_from_backup(sub.DollyNo)
            dolly_info = DollyEOLInfo.query.filter_by(DollyNo=sub.DollyNo, VinNo=sub.VinNo).first()
            eol_dt = production_date or getattr(dolly_info, "InsertedAt", None) or getattr(dolly_info, "EOLDATE", None) or sub.CreatedAt
            # Terminal zamanı: forklift tamamladıysa LoadingCompletedAt, yoksa tarama zamanı (CreatedAt).
            terminal_dt = sub.LoadingCompletedAt or sub.CreatedAt

            # 1. INSERT into SeferDollyEOL
            sefer_record = SeferDollyEOL(
                SeferNumarasi=sefer_numarasi,
                DollyNo=sub.DollyNo,
                DollyOrderNo=sub.DollyOrderNo,
                VinNo=sub.VinNo,
                PlakaNo=plaka_no,
                CustomerReferans=sub.CustomerReferans,
                Adet=sub.Adet or 1,
                EOLName=sub.EOLName,
                EOLID=sub.EOLID,
                EOLDate=eol_dt,
                TerminalUser=sub.TerminalUser,
                TerminalDate=terminal_dt,
                VeriGirisUser=current_user.Username,
                PartNumber=part_number,
                ASNDate=datetime.now()  # ✅ Türkiye yerel saati
            )
            db.session.add(sefer_record)
            
            # 2. DELETE from DollySubmissionHold
            db.session.delete(sub)
            
            transferred_count += 1
        
        # Commit transaction
        db.session.commit()
        
        current_app.logger.info(f"✅ ASN başarılı: {transferred_count} VIN SeferDollyEOL'a taşındı")
        
        # Audit log success
        audit = AuditService()
        audit.log(
            action="asn.send.success",
            resource="ceva_asn",
            resource_id=sefer_numarasi,
            actor_name=current_user.Username,
            metadata={
                "part_number": part_number,
                "sefer_numarasi": sefer_numarasi,
                "plaka_no": plaka_no,
                "vin_count": transferred_count,
                "shipping_type": shipping_type,
                "ceva_message": ceva_response.result_description
            }
        )
        
        return jsonify({
            'success': True,
            'message': f'✅ {transferred_count} VIN başarıyla CEVA\'ya gönderildi ve kaydedildi',
            'transferred_count': transferred_count,
            'sefer_numarasi': sefer_numarasi,
            'ceva_message': ceva_response.result_description
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ ASN gönderme hatası: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': f'Sistem hatası: {str(e)}'}), 500


@dashboard_bp.get("/operator/task/<part_number>/export")
@login_required
@role_required("operator")
def operator_task_export(part_number: str):
    """Excel formatında dolly listesini indir - Modüler yapı"""
    try:
        from ..models.dolly_hold import DollySubmissionHold
        from ..services.excel_export_service import ExcelExportService
        
        # DollySubmissionHold'dan verileri çek (display ile aynı kaynak)
        submissions = DollySubmissionHold.query.filter_by(
            PartNumber=part_number
        ).order_by(
            DollySubmissionHold.DollyNo,
            DollySubmissionHold.CreatedAt
        ).all()
        
        if not submissions:
            current_app.logger.error(f"❌ Task not found: {part_number}")
            return jsonify({"error": "Görev bulunamadı"}), 404
        
        # Excel export servisini kullan
        excel_service = ExcelExportService()
        excel_file = excel_service.export_dolly_task(part_number, submissions)
        filename = excel_service.generate_filename(part_number)
        
        # Excel response döndür
        return Response(
            excel_file.getvalue(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
        )
    
    except Exception as e:
        current_app.logger.error(f"❌ Excel export error for {part_number}: {str(e)}", exc_info=True)
        return jsonify({"error": f"Excel oluşturulurken hata: {str(e)}"}), 500


@dashboard_bp.get("/operator/task/<path:part_number>/vins")
@login_required
@role_required("operator")
def operator_task_vins(part_number: str):
    """VINleri EOL'e göre gruplu ve EOLDATE sırasına göre sıralı şekilde getir"""
    try:
        from ..models.dolly_hold import DollySubmissionHold
        from ..models.dolly import DollyEOLInfo
        
        current_app.logger.info(f"📋 VIN listesi istendi: {part_number}")
        
        # VINleri al ve EOL alfabetik + EOLDATE'e göre sırala
        submissions = db.session.query(DollySubmissionHold).filter(
            DollySubmissionHold.PartNumber == part_number,
            DollySubmissionHold.Status != 'removed'
        ).all()
        
        # Her submission için InsertedAt bilgisini al (Manuel dolly toplama ekranındaki sıralama ile uyumlu)
        submission_with_dates = []
        for sub in submissions:
            # InsertedAt DollySubmissionHold'da direkt mevcut (DollyEOLInfo'dan kopyalandı)
            submission_with_dates.append({
                'submission': sub,
                'inserted_at': sub.InsertedAt or sub.CreatedAt,  # Fallback to CreatedAt if InsertedAt missing
                'dolly_no': sub.DollyNo or '',
                'vin_no': sub.VinNo or ''
            })
        
        # Sıralama (Manuel dolly toplama ile aynı): 1. InsertedAt, 2. VinNo (DollyNo sıralamadan çıkarıldı)
        submission_with_dates.sort(key=lambda x: (
            x['inserted_at'] or datetime.min,
            x['vin_no']
        ))
        
        result = [(s['submission'].VinNo, s['submission'].EOLName, s['submission'].DollyNo, 
                   s['submission'].DollyOrderNo, s['submission'].CustomerReferans) 
                  for s in submission_with_dates]
        
        current_app.logger.info(f"📊 Toplam {len(result)} VIN bulundu")
        
        # EOL'e göre grupla
        eol_groups = {}
        for row in result:
            vin_no = row[0]
            eol_name = row[1] or "UNKNOWN"
            dolly_no = row[2]
            dolly_order_no = row[3]
            customer = row[4]
            
            if eol_name not in eol_groups:
                eol_groups[eol_name] = []
            
            eol_groups[eol_name].append({
                "vin": vin_no,
                "dolly_no": dolly_no,
                "dolly_order_no": dolly_order_no,
                "customer": customer
            })
        
        return jsonify({
            "success": True,
            "part_number": part_number,
            "eol_groups": eol_groups,
            "total_vins": len(result)
        })
    
    except Exception as e:
        current_app.logger.error(f"❌ VIN listesi hatası: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500



@dashboard_bp.post("/operator/task/<part_number>/add-dolly")
@login_required
@role_required("operator")
def operator_add_dolly(part_number: str):
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    dolly_no = (request.form.get("dolly_no") or "").strip()
    vin_no = (request.form.get("vin_no") or "").strip()
    sefer_no = (request.form.get("sefer_no") or "").strip()
    plaka_no = (request.form.get("plaka_no") or "").strip()
    lokasyon = (request.form.get("lokasyon") or "GHZNA").strip() or "GHZNA"
    
    if not dolly_no or not vin_no:
        return redirect(url_for("dashboard.operator_task_detail", part_number=part_number, error="Dolly No ve VIN No zorunludur."))
    if not sefer_no or not plaka_no:
        return redirect(url_for("dashboard.operator_task_detail", part_number=part_number, error="Sefer No ve Plaka zorunludur."))
    
    try:
        entry = service.add_dolly_to_task(
            part_number,
            dolly_no,
            vin_no,
            current_user.Username,
            sefer_no=sefer_no,
            plaka_no=plaka_no,
            lokasyon=lokasyon,
        )
        if not entry:
            return redirect(url_for("dashboard.operator_task_detail", part_number=part_number, error="Task bulunamadı."))
        
        audit_service.log(
            action="operator.add_dolly",
            resource="task",
            resource_id=part_number,
            actor_user=current_user,
            metadata={"dolly_no": dolly_no, "vin_no": vin_no}
        )
        
        return redirect(url_for("dashboard.operator_task_detail", part_number=part_number, message="Dolly eklendi."))
    except Exception as e:
        return redirect(url_for("dashboard.operator_task_detail", part_number=part_number, error=str(e)))


@dashboard_bp.post("/operator/task/<part_number>/add-next-dolly/<dolly_no>")
@login_required
@role_required("operator")
def operator_add_next_dolly(part_number: str, dolly_no: str):
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    payload = request.get_json(silent=True) or {}
    # ✅ Sefer/plaka zorunlu DEĞİL - operatör sadece dolly ekler, sonra okutma yapar
    # Bu bilgiler ASN/İrsaliye gönderiminde doldurulur
    sefer_no = (payload.get("sefer_no") or "").strip() or None
    plaka_no = (payload.get("plaka_no") or "").strip() or None
    lokasyon = (payload.get("lokasyon") or "GHZNA").strip() or "GHZNA"
    
    try:
        current_app.logger.info(f"📥 Dolly ekleme başlatıldı: PartNumber={part_number}, DollyNo={dolly_no}, User={current_user.Username}")
        
        success = service.add_next_dolly_to_task(
            part_number,
            dolly_no,
            current_user.Username,
            sefer_no=sefer_no,
            plaka_no=plaka_no,
            lokasyon=lokasyon,
        )
        
        if success:
            current_app.logger.info(f"✅ Dolly ekleme başarılı: PartNumber={part_number}, DollyNo={dolly_no}")
            audit_service.log(
                action="operator.add_next_dolly",
                resource="task",
                resource_id=part_number,
                actor_user=current_user,
                metadata={
                    "dolly_no": dolly_no,
                    "sefer_no": sefer_no,
                    "plaka_no": plaka_no,
                    "lokasyon": lokasyon,
                    "success": True
                }
            )
            return jsonify({"success": True, "message": "Dolly başarıyla eklendi"})
        else:
            current_app.logger.warning(f"⚠️ Dolly eklenemedi: PartNumber={part_number}, DollyNo={dolly_no}")
            return jsonify({"success": False, "message": "Dolly eklenemedi"})
            
    except Exception as e:
        current_app.logger.error(f"❌ Dolly ekleme hatası: PartNumber={part_number}, DollyNo={dolly_no}, Error={e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        audit_service.log(
            action="operator.add_next_dolly.error",
            resource="task",
            resource_id=part_number,
            actor_user=current_user,
            metadata={"dolly_no": dolly_no, "error": str(e), "success": False}
        )
        return jsonify({"success": False, "message": str(e)})


@dashboard_bp.post("/operator/task/<part_number>/remove-dolly/<dolly_no>")
@login_required
@role_required("operator")
def operator_remove_dolly(part_number: str, dolly_no: str):
    current_app.logger.info(f"🗑️ Dolly silme başlatıldı: PartNumber={part_number}, DollyNo={dolly_no}, User={current_user.Username}")
    
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    success = service.remove_dolly_from_task(part_number, dolly_no, current_user.Username)
    
    if not success:
        current_app.logger.warning(f"⚠️ Dolly silinemedi: PartNumber={part_number}, DollyNo={dolly_no}")
        audit_service.log(
            action="operator.remove_dolly.failed",
            resource="task",
            resource_id=part_number,
            actor_user=current_user,
            metadata={"dolly_no": dolly_no, "success": False, "reason": "not_found_or_not_last"}
        )
        return redirect(url_for("dashboard.operator_task_detail", part_number=part_number, error="Dolly çıkarılamadı (bulunamadı veya son değil)."))
    
    current_app.logger.info(f"✅ Dolly silme başarılı: PartNumber={part_number}, DollyNo={dolly_no}")
    audit_service.log(
        action="operator.remove_dolly",
        resource="task", 
        resource_id=part_number,
        actor_user=current_user,
        metadata={"dolly_no": dolly_no, "success": True}
    )
    
    return redirect(url_for("dashboard.operator_task_detail", part_number=part_number, message="Dolly çıkarıldı."))


# Inline edit (new module)
@dashboard_bp.post("/operator/task/<part_number>/edit/add")
@login_required
@role_required("operator")
def operator_edit_add(part_number: str):
    payload = request.get_json(silent=True) or {}
    current_app.logger.info(f"✏️ Manuel dolly ekleme başlatıldı: PartNumber={part_number}, User={current_user.Username}")
    current_app.logger.info(f"📝 Payload: DollyNo={payload.get('dolly_no')}, VIN={payload.get('vin_no')}, EOL={payload.get('eol_name')}")
    
    try:
        ok = add_manual_dolly(
            part_number=part_number,
            actor=current_user.Username,
            dolly_no=(payload.get("dolly_no") or "").strip(),
            vin_no=(payload.get("vin_no") or "").strip(),
            eol_name=(payload.get("eol_name") or "").strip(),
            eol_id=payload.get("eol_id"),
            customer_ref=payload.get("customer_ref"),
            dolly_order_no=payload.get("dolly_order_no"),
            adet=int(payload.get("adet") or 1),
            terminal_dt=datetime.fromisoformat(payload.get("terminal_dt")),
            eol_dt=datetime.fromisoformat(payload.get("eol_dt")),
            sefer_no=payload.get("sefer_no"),
            plaka_no=payload.get("plaka_no"),
            lokasyon=payload.get("lokasyon"),
        )
        if not ok:
            current_app.logger.warning(f"⚠️ Manuel dolly eklenemedi: PartNumber={part_number}")
            audit_service.log(
                action="operator.edit_add.failed",
                resource="task",
                resource_id=part_number,
                actor_user=current_user,
                metadata={"dolly_no": payload.get("dolly_no"), "vin_no": payload.get("vin_no"), "success": False}
            )
            return jsonify({"success": False, "message": "Kayıt eklenemedi"}), 400
        
        current_app.logger.info(f"✅ Manuel dolly ekleme başarılı: PartNumber={part_number}, DollyNo={payload.get('dolly_no')}, VIN={payload.get('vin_no')}")
        audit_service.log(
            action="operator.edit_add",
            resource="task",
            resource_id=part_number,
            actor_user=current_user,
            metadata={
                "dolly_no": payload.get("dolly_no"),
                "vin_no": payload.get("vin_no"),
                "eol_name": payload.get("eol_name"),
                "customer_ref": payload.get("customer_ref"),
                "success": True
            }
        )
        return jsonify({"success": True, "message": "Dolly eklendi"})
    except Exception as e:
        current_app.logger.error(f"❌ Manuel dolly ekleme hatası: PartNumber={part_number}, Error={e}")
        current_app.logger.error(f"Edit add error: {e}", exc_info=True)
        audit_service.log(
            action="operator.edit_add.error",
            resource="task",
            resource_id=part_number,
            actor_user=current_user,
            metadata={"error": str(e), "success": False}
        )
        return jsonify({"success": False, "message": str(e)}), 400


@dashboard_bp.post("/operator/task/<part_number>/edit/remove")
@login_required
@role_required("operator")
def operator_edit_remove(part_number: str):
    payload = request.get_json(silent=True) or {}
    dolly_no = (payload.get("dolly_no") or "").strip()
    eol_name = (payload.get("eol_name") or "").strip()
    
    current_app.logger.info(f"🗑️ EOL'den dolly çıkarma başlatıldı: PartNumber={part_number}, DollyNo={dolly_no}, EOL={eol_name}, User={current_user.Username}")
    
    if not dolly_no or not eol_name:
        current_app.logger.warning(f"⚠️ Dolly ve EOL zorunlu: DollyNo={bool(dolly_no)}, EOL={bool(eol_name)}")
        return jsonify({"success": False, "message": "Dolly ve EOL zorunlu"}), 400
    
    try:
        ok = remove_last_dolly_in_eol(part_number, dolly_no, eol_name, current_user.Username)
        if not ok:
            current_app.logger.warning(f"⚠️ Dolly çıkarılamadı (son değil): PartNumber={part_number}, DollyNo={dolly_no}, EOL={eol_name}")
            audit_service.log(
                action="operator.edit_remove.failed",
                resource="task",
                resource_id=part_number,
                actor_user=current_user,
                metadata={"dolly_no": dolly_no, "eol_name": eol_name, "success": False, "reason": "not_last_in_eol"}
            )
            return jsonify({"success": False, "message": "Sadece EOL içindeki son dolly çıkarılabilir"}), 400
        
        current_app.logger.info(f"✅ Dolly çıkarma başarılı: PartNumber={part_number}, DollyNo={dolly_no}, EOL={eol_name}")
        audit_service.log(
            action="operator.edit_remove",
            resource="task",
            resource_id=part_number,
            actor_user=current_user,
            metadata={"dolly_no": dolly_no, "eol_name": eol_name, "success": True}
        )
        return jsonify({"success": True, "message": "Dolly çıkarıldı"})
    except Exception as e:
        current_app.logger.error(f"❌ Dolly çıkarma hatası: PartNumber={part_number}, DollyNo={dolly_no}, EOL={eol_name}, Error={e}")
        current_app.logger.error(f"Edit remove error: {e}", exc_info=True)
        audit_service.log(
            action="operator.edit_remove.error",
            resource="task",
            resource_id=part_number,
            actor_user=current_user,
            metadata={"dolly_no": dolly_no, "eol_name": eol_name, "error": str(e), "success": False}
        )
        return jsonify({"success": False, "message": str(e)}), 400


@dashboard_bp.post("/operator/task/<path:part_number>/complete-manually")
@login_required
@role_required("operator")
def operator_complete_task_manually(part_number: str):
    """İRSALİYE görevlerini manuel olarak tamamla (VIN popup'tan)"""
    try:
        from ..models.dolly_hold import DollySubmissionHold
        from ..models.sefer import SeferDollyEOL
        from ..models import DollyEOLInfo  # ✅ DollyEOLInfo import ekle
        
        payload = request.get_json(silent=True) or {}
        completed_by = payload.get('completed_by', 'operator_manual')
        note = payload.get('note', 'Manuel olarak tamamlandı')
        
        # ✅ Sefer, Plaka ve İrsaliye bilgilerini al
        sefer_numarasi = payload.get('sefer_numarasi', '').strip()
        plaka_no = payload.get('plaka_no', '').strip()
        irsaliye_no = payload.get('irsaliye_no', '').strip()
        
        # 🔍 DEBUG: Payload'u logla
        current_app.logger.info(f"🔍 Payload alındı: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        current_app.logger.info(f"🔍 Parse edilen değerler: Sefer={sefer_numarasi}, Plaka={plaka_no}, İrsaliye={irsaliye_no}")
        
        # Zorunlu alanları kontrol et
        if not sefer_numarasi or not plaka_no or not irsaliye_no:
            current_app.logger.error(f"❌ Zorunlu alanlar eksik! Sefer={bool(sefer_numarasi)}, Plaka={bool(plaka_no)}, İrsaliye={bool(irsaliye_no)}")
            return jsonify({
                'success': False,
                'error': 'Sefer No, Plaka No ve İrsaliye No zorunludur'
            }), 400
        
        current_app.logger.info(f"📋 Manuel görev tamamlama: {part_number} by {current_user.Username}, Sefer={sefer_numarasi}, Plaka={plaka_no}, İrsaliye={irsaliye_no}")
        
        # Bu part_number için tüm pending kayıtları al
        submissions = DollySubmissionHold.query.filter_by(
            PartNumber=part_number,
            Status='pending'
        ).all()
        
        if not submissions:
            return jsonify({
                'success': False,
                'error': 'Bu görev için pending kayıt bulunamadı'
            }), 404
        
        # Tüm kayıtları SeferDollyEOL'e taşı
        moved_count = 0
        for sub in submissions:
            # 📅 Üretim tarihini backup tablosundan al
            production_date = _get_production_date_from_backup(sub.DollyNo)
            dolly_info = DollyEOLInfo.query.filter_by(DollyNo=sub.DollyNo, VinNo=sub.VinNo).first()
            eol_dt = production_date or getattr(dolly_info, "InsertedAt", None) or getattr(dolly_info, "EOLDATE", None) or sub.CreatedAt
            terminal_dt = sub.LoadingCompletedAt or sub.CreatedAt

            # SeferDollyEOL'e ekle - ✅ Önce DollySubmissionHold'dan, yoksa formdan gelen değeri kullan!
            sefer_entry = SeferDollyEOL(
                SeferNumarasi=sub.SeferNumarasi or sefer_numarasi,  # ✅ Önce sub'dan, sonra formdan
                DollyNo=sub.DollyNo,
                DollyOrderNo=sub.DollyOrderNo,
                VinNo=sub.VinNo,
                PlakaNo=sub.PlakaNo or plaka_no,  # ✅ Önce sub'dan, sonra formdan
                CustomerReferans=sub.CustomerReferans,
                Adet=sub.Adet or 1,
                EOLName=sub.EOLName,
                EOLID=sub.EOLID,
                EOLDate=eol_dt,
                TerminalUser=sub.TerminalUser or current_user.Username,
                TerminalDate=terminal_dt,
                VeriGirisUser=current_user.Username,
                PartNumber=sub.PartNumber,
                IrsaliyeDate=datetime.now()  # ✅ Türkiye yerel saati
            )
            
            current_app.logger.info(f"  📦 VIN={sub.VinNo}, SeferNumarasi={sefer_entry.SeferNumarasi}, PlakaNo={sefer_entry.PlakaNo}")
            
            db.session.add(sefer_entry)
            
            # DollySubmissionHold'dan sil
            db.session.delete(sub)
            moved_count += 1
        
        db.session.commit()
        
        # Audit log
        audit_service.log(
            action="operator.complete_task_manually",
            resource="task",
            resource_id=part_number,
            actor_user=current_user,
            metadata={
                'moved_count': moved_count,
                'note': note,
                'completed_by': completed_by,
                'sefer_numarasi': sefer_numarasi,
                'plaka_no': plaka_no,
                'irsaliye_no': irsaliye_no
            }
        )
        
        current_app.logger.info(f"✅ Görev manuel olarak tamamlandı: {part_number}, {moved_count} kayıt taşındı, Sefer={sefer_numarasi}, Plaka={plaka_no}, İrsaliye={irsaliye_no}")
        
        return jsonify({
            'success': True,
            'message': f'Görev başarıyla tamamlandı ({moved_count} kayıt)',
            'moved_count': moved_count
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Manuel görev tamamlama hatası: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_bp.post("/operator/task/<part_number>/submit/<tag_type>")
@login_required
@role_required("operator")
def operator_submit_task(part_number: str, tag_type: str):
    if tag_type not in ["asn", "irsaliye", "both"]:
        return redirect(url_for("dashboard.operator_task_detail", part_number=part_number, error="Geçersiz gönderim türü."))
    
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    success = service.submit_task_with_tag(part_number, tag_type, current_user.Id)
    
    if not success:
        return redirect(url_for("dashboard.operator_task_detail", part_number=part_number, error="Task gönderilemedi."))
    
    audit_service.log(
        action=f"operator.submit_{tag_type}",
        resource="task",
        resource_id=part_number,
        actor_user=current_user,
        metadata={"tag_type": tag_type}
    )
    
    return redirect(url_for("dashboard.dashboard_home"))


@dashboard_bp.get("/admin/users")
@login_required
@role_required("admin")
def admin_users():
    users = UserAccount.query.order_by(UserAccount.Username.asc()).all()
    roles = UserRole.query.order_by(UserRole.Name.asc()).all()
    message = request.args.get("message")
    error = request.args.get("error")
    return render_template(
        "dashboard/admin_users.html",
        title="Kullanıcı ve Terminal Ayarları",
        users=users,
        roles=roles,
        message=message,
        error=error,
    )


@dashboard_bp.post("/admin/users")
@login_required
@role_required("admin")
def create_user():
    username = (request.form.get("username") or "").strip()
    display_name = (request.form.get("display_name") or "").strip()
    barcode = (request.form.get("barcode") or "").strip() or None  # Not saved to UserAccount, used for TerminalBarcodeSession
    password = request.form.get("password") or ""
    role_id = request.form.get("role_id")
    
    if not username or not password or not role_id:
        return redirect(url_for("dashboard.admin_users", error="Kullanıcı adı ve şifre gerekli."))
    
    # Check for duplicate username
    if UserAccount.query.filter_by(Username=username).first():
        return redirect(url_for("dashboard.admin_users", error="Bu kullanıcı adı zaten kayıtlı."))
    
    try:
        role_id_int = int(role_id)
    except ValueError:
        return redirect(url_for("dashboard.admin_users", error="Geçersiz rol seçimi."))
    
    user = UserAccount(
        Username=username,
        DisplayName=display_name or None,
        # Note: Barcode is NOT saved here - it's managed via TerminalBarcodeSession
        PasswordHash=hash_password(password),
        RoleId=role_id_int,
        IsActive=True,
    )
    db.session.add(user)
    db.session.commit()
    role = user.role
    if role and _is_terminal_role(role.Name):
        device = _ensure_user_device(user, role)
        session = _create_barcode_session(user, device)
        audit_meta = {"username": username, "role": role.Name, "barcode": session.Token}
    else:
        audit_meta = {"username": username, "role": role.Name if role else None, "mobile_barcode": barcode}
    audit_service.log(
        action="user.create",
        resource="user",
        resource_id=str(user.Id),
        actor_name="admin",
        metadata=audit_meta,
    )
    return redirect(url_for("dashboard.admin_users", message="Kullanıcı oluşturuldu."))


@dashboard_bp.post("/admin/users/<int:user_id>/password")
@login_required
@role_required("admin")
def reset_user_password(user_id: int):
    new_password = request.form.get("new_password") or ""
    if len(new_password) < 8:
        return redirect(url_for("dashboard.admin_users", error="Yeni şifre en az 8 karakter olmalı."))
    user = UserAccount.query.get_or_404(user_id)
    user.PasswordHash = hash_password(new_password)
    db.session.commit()
    audit_service.log(
        action="user.password_reset",
        resource="user",
        resource_id=str(user.Id),
        actor_name="admin",
    )
    return redirect(url_for("dashboard.admin_users", message=f"{user.Username} için şifre yenilendi."))


@dashboard_bp.post("/admin/users/<int:user_id>/barcode")
@login_required
@role_required("admin")
def update_user_barcode(user_id: int):
    """Update user's TerminalBarcodeSession token (not UserAccount.Barcode)"""
    # Barcode is managed through TerminalBarcodeSession, not UserAccount
    # Users get barcode tokens via the "Terminal Barkod" section (generate_user_terminal_barcode)
    return redirect(url_for("dashboard.admin_users", error="Barkod güncelleme TerminalBarcodeSession üzerinden yapılır. 'Yeniden Oluştur' butonunu kullanın."))


@dashboard_bp.post("/admin/users/<int:user_id>/toggle")
@login_required
@role_required("admin")
def toggle_user_status(user_id: int):
    user = UserAccount.query.get_or_404(user_id)
    user.IsActive = not user.IsActive
    db.session.commit()
    audit_service.log(
        action="user.toggle_status",
        resource="user",
        resource_id=str(user.Id),
        actor_name="admin",
        metadata={"isActive": user.IsActive},
    )
    state = "aktif" if user.IsActive else "pasif"
    return redirect(url_for("dashboard.admin_users", message=f"{user.Username} artık {state}."))


@dashboard_bp.post("/admin/users/<int:user_id>/terminal-barcode")
@login_required
@role_required("admin")
def generate_user_terminal_barcode(user_id: int):
    """Generate TerminalBarcodeSession token for any user (used for terminal login)"""
    user = UserAccount.query.get_or_404(user_id)
    role = user.role
    
    # Allow token generation for all users, not just terminal roles
    device = _ensure_user_device(user, role)
    session = _create_barcode_session(user, device)
    
    return redirect(url_for("dashboard.admin_users", message=f"{user.Username} için token oluşturuldu: {session.Token}"))


@dashboard_bp.get("/admin/logs")
@login_required
@role_required("admin")
def admin_logs():
    """Gelişmiş Log Görüntüleme - Kategorilere ayrılmış, sayfalama ile"""
    import re
    from datetime import datetime, timedelta
    
    # Kategori ve sayfa parametreleri
    category = request.args.get("category", "all")  # all, asn, edit, scan, error
    page = int(request.args.get("page", 1))
    per_page = 50
    
    current_app.logger.info(f"📊 Admin logs görüntülendi: Category={category}, Page={page}, User={current_user.Username}")
    
    # Log dosyasını oku ve parse et
    log_file_path = current_app.config.get("LOG_FILE_PATH") or "logs/app.log"
    parsed_logs = _parse_log_file(log_file_path, category=category, limit=per_page * 10)  # 10 sayfa değerinde oku
    
    # Sayfalama hesaplamaları
    total_logs = len(parsed_logs)
    total_pages = (total_logs + per_page - 1) // per_page if total_logs else 1
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_logs = parsed_logs[start_idx:end_idx]
    
    # Kategori istatistikleri
    category_stats = _get_category_stats(log_file_path)
    
    pagination = {
        "page": page,
        "per_page": per_page,
        "total_count": total_logs,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages
    }
    
    return render_template(
        "dashboard/admin_logs.html",
        title="Sistem Logları",
        logs=paginated_logs,
        pagination=pagination,
        category=category,
        category_stats=category_stats,
    )


def _parse_log_file(file_path: str, category: str = "all", limit: int = 500):
    """Log dosyasını parse et ve kategoriye göre filtrele"""
    import re
    from datetime import datetime
    
    logs = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Yeni → Eski sıralama için ters çevir
        lines.reverse()
        
        # Log pattern: 2026-02-02 13:37:13,359 INFO app 📦 Message...
        log_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ (\w+) (\w+) (.+)$')
        
        for line in lines:
            if len(logs) >= limit:
                break
            
            match = log_pattern.match(line.strip())
            if not match:
                continue
            
            timestamp_str, level, logger, message = match.groups()
            
            # Kategori filtresi
            if category != "all":
                if category == "asn" and not any(k in message.lower() for k in ['asn', 'ceva', 'sevkiyat', 'gönder']):
                    continue
                elif category == "edit" and not any(k in message.lower() for k in ['düzenle', 'edit', 'manuel', 'ekle', 'çıkar', 'remove']):
                    continue
                elif category == "scan" and not any(k in message.lower() for k in ['dolly', 'okut', 'scan', 'barcode', 'vin']):
                    continue
                elif category == "error" and level.upper() not in ['ERROR', 'WARNING']:
                    continue
            
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            except:
                timestamp = None
            
            # Log kategorisini belirle
            log_category = _detect_log_category(message)
            
            logs.append({
                'timestamp': timestamp,
                'timestamp_str': timestamp_str,
                'level': level.upper(),
                'logger': logger,
                'message': message,
                'category': log_category,
                'icon': _get_log_icon(log_category, level)
            })
    
    except FileNotFoundError:
        current_app.logger.error(f"Log dosyası bulunamadı: {file_path}")
    except Exception as e:
        current_app.logger.error(f"Log parse hatası: {e}")
    
    return logs


def _detect_log_category(message: str):
    """Log mesajından kategoriyi belirle"""
    msg_lower = message.lower()
    
    if any(k in msg_lower for k in ['asn', 'ceva', 'sevkiyat']):
        return 'asn'
    elif any(k in msg_lower for k in ['düzenle', 'edit', 'manuel']):
        return 'edit'
    elif any(k in msg_lower for k in ['dolly', 'okut', 'scan', 'vin']):
        return 'scan'
    elif any(k in msg_lower for k in ['error', 'hata', 'warning', 'uyarı']):
        return 'error'
    elif any(k in msg_lower for k in ['sefer', 'geçmiş', 'history']):
        return 'history'
    elif any(k in msg_lower for k in ['filtre', 'filter']):
        return 'filter'
    else:
        return 'general'


def _get_log_icon(category: str, level: str):
    """Kategori ve seviyeye göre icon döndür"""
    if level.upper() == 'ERROR':
        return '❌'
    elif level.upper() == 'WARNING':
        return '⚠️'
    
    icons = {
        'asn': '📤',
        'edit': '✏️',
        'scan': '📦',
        'error': '❌',
        'history': '📋',
        'filter': '🔍',
        'general': '📝'
    }
    return icons.get(category, 'ℹ️')


def _get_category_stats(file_path: str):
    """Kategori bazlı istatistikler"""
    stats = {
        'all': 0,
        'asn': 0,
        'edit': 0,
        'scan': 0,
        'error': 0
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Son 1000 satırı incele
        for line in lines[-1000:]:
            stats['all'] += 1
            line_lower = line.lower()
            
            if 'error' in line_lower or 'warning' in line_lower:
                stats['error'] += 1
            if any(k in line_lower for k in ['asn', 'ceva', 'sevkiyat']):
                stats['asn'] += 1
            if any(k in line_lower for k in ['düzenle', 'edit', 'manuel']):
                stats['edit'] += 1
            if any(k in line_lower for k in ['dolly', 'okut', 'scan']):
                stats['scan'] += 1
    
    except Exception as e:
        current_app.logger.error(f"Kategori stats hatası: {e}")
    
    return stats


def _is_terminal_role(role_name: str | None) -> bool:
    return bool(role_name and role_name.lower().startswith("terminal"))


def _ensure_user_device(user: UserAccount, role: UserRole) -> TerminalDevice:
    identifier = f"user:{user.Id}"
    device = TerminalDevice.query.filter_by(DeviceIdentifier=identifier).first()
    if device:
        return device
    device = TerminalDevice(
        Name=user.DisplayName or user.Username,
        DeviceIdentifier=identifier,
        RoleId=role.Id,
        ApiKey=secrets.token_hex(16),
        BarcodeSecret=secrets.token_hex(16),
        IsActive=True,
    )
    db.session.add(device)
    db.session.commit()
    return device


def _create_barcode_session(
    user: UserAccount,
    device: TerminalDevice,
    minutes: int = 60,
) -> TerminalBarcodeSession:
    token = secrets.token_urlsafe(12)
    session = TerminalBarcodeSession(
        DeviceId=device.Id,
        UserId=user.Id,
        Token=token,
        ExpiresAt=datetime.utcnow() + timedelta(minutes=minutes),
    )
    db.session.add(session)
    db.session.commit()
    audit_service.log(
        action="terminal.token_create",
        resource="barcode",
        resource_id=str(session.Id),
        actor_name="admin",
        metadata={"user": user.Username, "token": token},
    )
    return session


def _read_file_logs(lines: int = 200):
    config = current_app.config.get("APP_CONFIG", {})
    log_file = config.get("logging", {}).get("file")
    if not log_file or not os.path.exists(log_file):
        return []
    results = []
    try:
        with open(log_file, "r", encoding="utf-8") as handle:
            data = handle.readlines()[-lines:]
        for row in data:
            results.append(row.rstrip())
    except Exception:
        return []
    return results


# Manual Queue Management Routes (OLD - for add/submit/reorder)
@dashboard_bp.get("/queue/management")
@login_required  
@role_required("admin")
def queue_management():
    """Old manual queue management page (for add/submit/reorder)"""
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    grouped_dollys = service.list_queue_dollys_grouped(per_group=50)
    stats = service.get_queue_stats()
    eol_candidates = service.list_eol_candidates()
    active_groups = service.get_active_groups()
    
    message = request.args.get("message")
    error = request.args.get("error")
    
    return render_template(
        "dashboard/queue_management.html",
        grouped_dollys=grouped_dollys,
        stats=stats,
        eol_candidates=eol_candidates,
        active_groups=active_groups,
        title="Manuel Kuyruk Yönetimi",
        message=message,
        error=error
    )


@dashboard_bp.post("/queue/add-dolly")
@login_required
@role_required("admin") 
def queue_add_dolly():
    """Add dolly to queue manually"""
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    
    dolly_no = (request.form.get("dolly_no") or "").strip()
    vin_no = (request.form.get("vin_no") or "").strip()
    customer_ref = (request.form.get("customer_ref") or "").strip()
    eol_name = request.form.get("eol_name")
    eol_id = request.form.get("eol_id")
    
    if not all([dolly_no, vin_no, customer_ref, eol_name, eol_id]):
        return redirect(url_for("dashboard.queue_management", error="Tüm alanlar zorunludur."))
    
    try:
        service.manual_add_dolly_to_queue(
            dolly_no=dolly_no,
            vin_no=vin_no,
            customer_ref=customer_ref, 
            eol_name=eol_name,
            eol_id=eol_id,
            actor_name=current_user.Username
        )
        
        audit_service.log(
            action="queue.manual_add",
            resource="dolly",
            resource_id=dolly_no,
            actor_user=current_user,
            metadata={"vin": vin_no, "eol": eol_name}
        )
        
        return redirect(url_for("dashboard.queue_management", message=f"Dolly {dolly_no} kuyruğa eklendi."))
    except ValueError as e:
        return redirect(url_for("dashboard.queue_management", error=str(e)))


@dashboard_bp.post("/queue/submit-dolly/<dolly_no>")
@login_required
@role_required("admin")
def queue_submit_dolly(dolly_no: str):
    """Submit dolly from queue manually"""
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    
    try:
        success = service.manual_submit_dolly(dolly_no, current_user.Username)
        if success:
            audit_service.log(
                action="queue.manual_submit",
                resource="dolly", 
                resource_id=dolly_no,
                actor_user=current_user
            )
            return redirect(url_for("dashboard.queue_management", message=f"Dolly {dolly_no} submit edildi."))
        else:
            return redirect(url_for("dashboard.queue_management", error="Submit işlemi başarısız."))
    except ValueError as e:
        return redirect(url_for("dashboard.queue_management", error=str(e)))


@dashboard_bp.post("/queue/reorder")
@login_required
@role_required("admin")
def queue_reorder():
    """Reorder queue dollys"""
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    
    # Get reorder data from form
    dolly_orders = []
    position = 0
    
    for key in request.form:
        if key.startswith("dolly_"):
            dolly_no = request.form[key]
            if dolly_no:
                dolly_orders.append({"dollyNo": dolly_no, "position": position})
                position += 1
    
    if not dolly_orders:
        return redirect(url_for("dashboard.queue_management", error="Sıralama bilgisi bulunamadı."))
    
    success = service.reorder_queue_dollys(dolly_orders, current_user.Username)
    if success:
        audit_service.log(
            action="queue.reorder",
            resource="queue",
            resource_id="manual_reorder",
            actor_user=current_user,
            metadata={"count": len(dolly_orders)}
        )
        return redirect(url_for("dashboard.queue_management", message="Kuyruk sıralaması güncellendi."))
    else:
        return redirect(url_for("dashboard.queue_management", error="Sıralama güncellenemedi."))


@dashboard_bp.get("/yuzde")
def dolly_yuzde_page():
    """Dolly dolma durumu görsel gösterge sayfası"""
    return render_template("yuzde.html")


@dashboard_bp.get("/queue/manage")
@login_required
@role_required("admin")
def manage_queue():
    """Sıra yönetimi - dolly'leri manuel kaldırma sayfası (PAGINATION ile optimize edildi)"""
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    
    # Pagination parametreleri
    page = request.args.get('page', 1, type=int)
    per_page = 50  # Manuel kuyrukta sabit 50 kayıt
    removed_page = request.args.get('removed_page', 1, type=int)
    removed_per_page = 50
    search_term = request.args.get('search', '', type=str).strip()
    search_dolly = request.args.get('search_dolly', '', type=str).strip()
    if not search_term and search_dolly:
        search_term = search_dolly

    filters = {
        "filter_dolly_no": request.args.get('filter_dolly_no', '', type=str).strip(),
        "filter_vin": request.args.get('filter_vin', '', type=str).strip(),
        "filter_customer_ref": request.args.get('filter_customer_ref', '', type=str).strip(),
        "filter_eol_name": request.args.get('filter_eol_name', '', type=str).strip(),
        "filter_eol_id": request.args.get('filter_eol_id', '', type=str).strip(),
        "filter_barcode": request.args.get('filter_barcode', '', type=str).strip(),
        "filter_removed_by": request.args.get('filter_removed_by', '', type=str).strip(),
        "filter_reason": request.args.get('filter_reason', '', type=str).strip(),
    }
    legacy_filter_eol = request.args.get('filter_eol', '', type=str).strip()
    if legacy_filter_eol and not filters["filter_eol_name"]:
        filters["filter_eol_name"] = legacy_filter_eol
    
    # DOLLY BAZLI GRUPLAMA - Her dolly için sadece 1 satır
    # VIN sayısını COUNT ile al
    query = db.session.query(
        DollyEOLInfo.DollyNo,
        DollyEOLInfo.CustomerReferans,
        DollyEOLInfo.EOLName,
        DollyEOLInfo.EOLID,
        DollyEOLInfo.EOLDATE,
        DollyEOLInfo.EOLDollyBarcode,
        DollyEOLInfo.DollyOrderNo,
        func.count(DollyEOLInfo.VinNo).label('VinCount'),
        func.max(DollyEOLInfo.InsertedAt).label('InsertedAt'),
        func.sum(DollyEOLInfo.Adet).label('TotalAdet')
    ).group_by(
        DollyEOLInfo.DollyNo,
        DollyEOLInfo.CustomerReferans,
        DollyEOLInfo.EOLName,
        DollyEOLInfo.EOLID,
        DollyEOLInfo.EOLDATE,
        DollyEOLInfo.EOLDollyBarcode,
        DollyEOLInfo.DollyOrderNo
    )
    
    # Filtreleme
    if search_term:
        term = f'%{search_term}%'
        query = query.filter(or_(
            DollyEOLInfo.DollyNo.like(term),
            DollyEOLInfo.VinNo.like(term),
            DollyEOLInfo.CustomerReferans.like(term),
            DollyEOLInfo.EOLName.like(term),
            DollyEOLInfo.EOLID.like(term),
            DollyEOLInfo.EOLDollyBarcode.like(term)
        ))
    if filters["filter_dolly_no"]:
        query = query.filter(DollyEOLInfo.DollyNo.like(f'%{filters["filter_dolly_no"]}%'))
    if filters["filter_vin"]:
        query = query.filter(DollyEOLInfo.VinNo.like(f'%{filters["filter_vin"]}%'))
    if filters["filter_customer_ref"]:
        query = query.filter(DollyEOLInfo.CustomerReferans.like(f'%{filters["filter_customer_ref"]}%'))
    if filters["filter_eol_name"]:
        query = query.filter(DollyEOLInfo.EOLName.like(f'%{filters["filter_eol_name"]}%'))
    if filters["filter_eol_id"]:
        query = query.filter(DollyEOLInfo.EOLID.like(f'%{filters["filter_eol_id"]}%'))
    if filters["filter_barcode"]:
        query = query.filter(DollyEOLInfo.EOLDollyBarcode.like(f'%{filters["filter_barcode"]}%'))
    
    # Toplam dolly sayısı (VIN değil!)
    total_count = query.count()
    
    # Pagination uygula - DollyOrderNo'ya göre sırala (SQL Server uyumlu)
    # NULL'lar sona atmak için CASE kullan
    offset = (page - 1) * per_page
    queue_dollys = query.order_by(
        case((DollyEOLInfo.DollyOrderNo.is_(None), 1), else_=0),  # NULL'lar sonda
        DollyEOLInfo.DollyOrderNo.asc(),  # DollyOrderNo sıralı (küçükten büyüğe)
        text('InsertedAt DESC')  # Aggregate alias kullan
    ).limit(per_page).offset(offset).all()
    
    # Pagination bilgisi
    total_pages = (total_count + per_page - 1) // per_page
    pagination = {
        'page': page,
        'per_page': per_page,
        'total_count': total_count,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages
    }
    
    # Arşivlenmiş dolly'leri getir (sayfalı)
    removed_dollys, removed_pagination = service.list_removed_dollys(
        page=removed_page,
        per_page=removed_per_page,
        search_term=search_term,
        filter_dolly_no=filters["filter_dolly_no"],
        filter_vin=filters["filter_vin"],
        filter_customer_ref=filters["filter_customer_ref"],
        filter_eol_name=filters["filter_eol_name"],
        filter_eol_id=filters["filter_eol_id"],
        filter_barcode=filters["filter_barcode"],
        filter_removed_by=filters["filter_removed_by"],
        filter_reason=filters["filter_reason"],
    )
    
    message = request.args.get("message")
    error = request.args.get("error")
    
    return render_template(
        "dashboard/queue_manage.html",
        title="Sıra Yönetimi",
        queue_dollys=queue_dollys,
        removed_dollys=removed_dollys,
        pagination=pagination,
        removed_pagination=removed_pagination,
        message=message,
        error=error,
        search_dolly=search_term,
        search_term=search_term,
        filters=filters
    )


@dashboard_bp.post("/queue/remove")
@login_required
@role_required("admin")
def remove_from_queue():
    """Seçili dolly'leri sıradan kaldır ve ARŞİVLE - DOLLY BAZLI (tüm VIN'ler dahil)"""
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    
    # Form verileri - artık sadece DollyNo geliyor
    dolly_selections = request.form.getlist("dolly_selection")  # ["123", "124", "125"]
    reason = request.form.get("reason", "").strip() or None
    
    if not dolly_selections:
        return redirect(url_for("dashboard.manage_queue", error="Lütfen en az bir dolly seçin."))
    
    # Her dolly için o dolly'ye ait TÜM VIN'leri bul ve kaldır
    dolly_list = []
    for dolly_no in dolly_selections:
        try:
            # Bu dolly'ye ait tüm VIN'leri getir (DollyNo string'dir!)
            vin_records = DollyEOLInfo.query.filter_by(DollyNo=dolly_no).all()
            
            if not vin_records:
                current_app.logger.warning(f"⚠️ Dolly {dolly_no} için VIN bulunamadı")
                continue
            
            for record in vin_records:
                dolly_list.append({
                    "dolly_no": dolly_no,  # String olarak tut
                    "vin_no": record.VinNo
                })
                
            current_app.logger.info(f"✅ Dolly {dolly_no}: {len(vin_records)} VIN bulundu")
            
        except (ValueError, AttributeError) as e:
            current_app.logger.error(f"❌ Dolly {dolly_no} işlenirken hata: {e}")
            return redirect(url_for("dashboard.manage_queue", error=f"Geçersiz dolly: {dolly_no} - {str(e)}"))
    
    if not dolly_list:
        return redirect(url_for("dashboard.manage_queue", error="Seçili dolly'lerde VIN bulunamadı."))
    
    try:
        result = service.remove_multiple_dollys_from_queue(
            dolly_list=dolly_list,
            removed_by=current_user.Username,
            reason=reason
        )
        
        # Toplam dolly sayısını hesapla (unique dolly no)
        unique_dollys = len(set(dolly_selections))
        msg = f"{unique_dollys} dolly ({result['success_count']} VIN) sıradan kaldırıldı."
        if result['failed']:
            msg += f" {len(result['failed'])} dolly kaldırılamadı."
        
        return redirect(url_for("dashboard.manage_queue", message=msg))
        
    except Exception as e:
        return redirect(url_for("dashboard.manage_queue", error=str(e)))


@dashboard_bp.post("/queue/restore/<int:archive_id>")
@login_required
@role_required("admin")
def restore_to_queue(archive_id: int):
    """Arşivden dolly'yi geri sıraya al"""
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    
    try:
        service.restore_dolly_to_queue(
            archive_id=archive_id,
            restored_by=current_user.Username
        )
        return redirect(url_for("dashboard.manage_queue", message="Dolly sıraya geri yüklendi."))
    except Exception as e:
        return redirect(url_for("dashboard.manage_queue", error=str(e)))


@dashboard_bp.post("/queue/restore-bulk")
@login_required
@role_required("admin")
def restore_bulk():
    """Arşivden seçili dolly'leri toplu geri yükle"""
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    selections = request.form.getlist("archive_selection")
    
    if not selections:
        return redirect(url_for("dashboard.manage_queue", error="Lütfen arşivden en az bir kayıt seçin."))
    
    archive_ids = []
    for raw in selections:
        try:
            archive_ids.append(int(raw))
        except (TypeError, ValueError):
            continue
    
    if not archive_ids:
        return redirect(url_for("dashboard.manage_queue", error="Seçimler geçersiz."))
    
    try:
        result = service.restore_multiple_dollys(
            archive_ids=archive_ids,
            restored_by=current_user.Username
        )
        msg = f"{result['success_count']} kayıt sıraya geri yüklendi."
        if result['failed']:
            msg += f" {len(result['failed'])} kayıt geri yüklenemedi."
        return redirect(url_for("dashboard.manage_queue", message=msg))
    except Exception as e:
        return redirect(url_for("dashboard.manage_queue", error=str(e)))


@dashboard_bp.get("/history/sefer")
@login_required
def sefer_history():
    """SeferDollyEOL geçmişini pagine listele (user + admin)"""
    current_app.logger.info(f"📋 Sefer geçmişi görüntülendi: User={current_user.Username if current_user and current_user.is_authenticated else 'Anonymous'}")
    
    service = DollyService(current_app.config.get("APP_CONFIG", {}))
    from sqlalchemy import or_
    part_page = request.args.get("part_page", 1, type=int)
    parts_per_page = 5

    # Filtre parametreleri
    filters = {
        "SeferNumarasi": request.args.get("filter_sefer_no", "").strip(),
        "PlakaNo": request.args.get("filter_plaka", "").strip(),
        "DollyNo": request.args.get("filter_dolly", "").strip(),
        "DollyOrderNo": request.args.get("filter_dolly_order", "").strip(),
        "VinNo": request.args.get("filter_vin", "").strip(),
        "CustomerReferans": request.args.get("filter_customer", "").strip(),
        "EOLName": request.args.get("filter_eol", "").strip(),
        "EOLID": request.args.get("filter_eol_id", "").strip(),
        "TerminalUser": request.args.get("filter_terminal_user", "").strip(),
        "VeriGirisUser": request.args.get("filter_veri_giris", "").strip(),
        "PartNumber": request.args.get("filter_part_number", "").strip(),
        "DateStart": request.args.get("filter_date_start", "").strip(),
        "DateEnd": request.args.get("filter_date_end", "").strip(),
        "ShippingType": request.args.get("filter_shipping_type", "").strip(),  # ✅ ASN veya İrsaliye filtresi
    }

    def highlight_match(value: str, term: str):
        """Wrap matching term with span.hit (case-insensitive)."""
        if not value:
            return "-"
        if not term:
            return escape(value)
        escaped_val = escape(value)
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        highlighted = pattern.sub(lambda m: Markup(f"<span class='hit'>{escape(m.group(0))}</span>"), escaped_val)
        return Markup(highlighted)

     # Sorguya filtreleri önce uygula, böylece part listesi de filtreli olur
    records_query = SeferDollyEOL.query
    
    # Tarih filtreleri ve ShippingType hariç text filtreleri uygula
    for col, val in filters.items():
        if val and col not in ['DateStart', 'DateEnd', 'ShippingType']:
            records_query = records_query.filter(getattr(SeferDollyEOL, col).ilike(f"%{val}%"))
    
    # 📅 Tarih filtreleri (TerminalDate bazında)
    if filters['DateStart']:
        try:
            start_date = datetime.strptime(filters['DateStart'], '%Y-%m-%d')
            records_query = records_query.filter(SeferDollyEOL.TerminalDate >= start_date)
        except ValueError:
            current_app.logger.warning(f"⚠️ Geçersiz başlangıç tarihi: {filters['DateStart']}")
    
    if filters['DateEnd']:
        try:
            # End date'e 23:59:59 ekleyelim
            end_date = datetime.strptime(filters['DateEnd'], '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59)
            records_query = records_query.filter(SeferDollyEOL.TerminalDate <= end_date)
        except ValueError:
            current_app.logger.warning(f"⚠️ Geçersiz bitiş tarihi: {filters['DateEnd']}")
    
    # 🚢 ASN/İrsaliye Filtresi
    # Mantık: ASNDate varsa → ASN, ASNDate yoksa → İrsaliye
    if filters['ShippingType']:
        shipping_type = filters['ShippingType'].lower()
        current_app.logger.info(f"🚢 Gönderim tipi filtresi uygulandı: {shipping_type}")
        if shipping_type == 'asn':
            # ASNDate NULL OLMAYAN kayıtlar
            records_query = records_query.filter(SeferDollyEOL.ASNDate.isnot(None))
        elif shipping_type == 'irsaliye':
            # ASNDate NULL olan kayıtlar
            records_query = records_query.filter(SeferDollyEOL.ASNDate.is_(None))
    
    # Log aktif filtreleri
    active_filters = {k: v for k, v in filters.items() if v}
    if active_filters:
        current_app.logger.info(f"🔍 Aktif filtreler: {active_filters}")

    # Filtre uygulanmış sonuçlar üzerinden parça listesi çıkar
    # Parçaları en yeni (en büyük PartNumber) en üstte göstermek için DESC sıralıyoruz
    part_query = records_query.with_entities(SeferDollyEOL.PartNumber).distinct().order_by(SeferDollyEOL.PartNumber.desc())
    part_list = [row[0] for row in part_query.all()]
    total_parts = len(part_list)
    total_part_pages = (total_parts + parts_per_page - 1) // parts_per_page if total_parts else 1

    offset = (part_page - 1) * parts_per_page
    selected_parts = part_list[offset: offset + parts_per_page]

    
    if selected_parts:
        non_null_parts = [p for p in selected_parts if p is not None]
        if None in selected_parts and non_null_parts:
            records_query = records_query.filter(
                or_(SeferDollyEOL.PartNumber.is_(None), SeferDollyEOL.PartNumber.in_(non_null_parts))
            )
        elif None in selected_parts:
            records_query = records_query.filter(SeferDollyEOL.PartNumber.is_(None))
        else:
            records_query = records_query.filter(SeferDollyEOL.PartNumber.in_(selected_parts))

    # Sondan başa sıralama: en yeni TerminalDate ve EOLDate en üstte
    records = records_query.order_by(
        case((SeferDollyEOL.PartNumber.is_(None), 1), else_=0),  # NULL'lar en alta
        SeferDollyEOL.PartNumber.desc(),  # En büyük PartNumber en üstte
        case((SeferDollyEOL.TerminalDate.is_(None), 1), else_=0),
        SeferDollyEOL.TerminalDate.desc(),
        case((SeferDollyEOL.EOLDate.is_(None), 1), else_=0),
        SeferDollyEOL.EOLDate.desc(),
    ).all()

    grouped_records = {}
    for rec in records:
        key = rec.PartNumber or "Bilinmiyor"
        grouped_records.setdefault(key, []).append(rec)
    grouped_items = sorted(grouped_records.items(), key=lambda kv: kv[0], reverse=True)
    
    current_app.logger.info(f"📊 Sefer geçmişi sonuçları: {len(records)} kayıt, {len(grouped_items)} part")

    part_pagination = {
        "page": part_page,
        "per_page": parts_per_page,
        "total_count": total_parts,
        "total_pages": total_part_pages,
        "has_prev": part_page > 1,
        "has_next": part_page < total_part_pages
    }

    return render_template(
        "dashboard/history_sefer.html",
        title="Sevkiyat Geçmişi",
        grouped_records=grouped_items,
        part_pagination=part_pagination,
        filters=filters,
        highlight=highlight_match,

    )


@dashboard_bp.get("/history/sefer/export/<part_number>")
@login_required
def sefer_history_export(part_number: str):
    """Belirli PartNumber için SeferDollyEOL Excel export"""
    try:
        from ..models.sefer import SeferDollyEOL
        from ..services.excel_export_service import ExcelExportService
        
        records = SeferDollyEOL.query.filter_by(PartNumber=part_number).order_by(
            SeferDollyEOL.TerminalDate.desc()
        ).all()
        
        if not records:
            return jsonify({"error": "Bu part için kayıt bulunamadı"}), 404
        
        exporter = ExcelExportService()
        excel_file = exporter.export_sefer_history(part_number, records)
        filename = exporter.generate_sefer_filename(part_number)
        
        return Response(
            excel_file.getvalue(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
        )
    except Exception as e:
        current_app.logger.error(f"❌ Sefer export error for {part_number}: {e}", exc_info=True)
        return jsonify({"error": f"Excel oluşturulurken hata: {str(e)}"}), 500
