"""
Authentication utilities for Forklift Android app
"""
from datetime import datetime, timedelta
from functools import wraps
import secrets
import json

from flask import request, jsonify, current_app
from ..models import ForkliftLoginSession
from ..extensions import db


def generate_session_token() -> str:
    """Generate a secure random session token"""
    return secrets.token_urlsafe(64)


def validate_forklift_session(token: str) -> ForkliftLoginSession | None:
    """Validate session token and return session if valid"""
    if not token:
        return None
    
    session = ForkliftLoginSession.query.filter_by(
        SessionToken=token,
        IsActive=True
    ).first()
    
    if not session:
        return None
    
    # Check if expired
    if session.is_expired():
        session.IsActive = False
        session.LogoutAt = datetime.utcnow()
        db.session.commit()
        return None
    
    # Update last activity
    session.update_activity()
    db.session.commit()
    
    return session


def require_forklift_auth(f):
    """Decorator to require forklift authentication for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                "error": "authentication_required",
                "message": "Giriş yapmanız gerekiyor. Lütfen barkodunuzu okutun."
            }), 401
        
        token = auth_header.replace('Bearer ', '')
        session = validate_forklift_session(token)
        
        if not session:
            return jsonify({
                "error": "invalid_session",
                "message": "Oturumunuz sona erdi. Lütfen tekrar giriş yapın."
            }), 401
        
        # Add session to request context
        request.forklift_session = session
        request.forklift_user = session.OperatorName
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_forklift_user() -> str | None:
    """Get current forklift user from request context"""
    return getattr(request, 'forklift_user', None)


def get_current_forklift_session() -> ForkliftLoginSession | None:
    """Get current forklift session from request context"""
    return getattr(request, 'forklift_session', None)


def create_forklift_session(
    operator_barcode: str,
    operator_name: str,
    device_id: str | None = None,
    session_hours: int = 8,
    is_admin: bool = False,
    role: str = 'forklift'
) -> ForkliftLoginSession:
    """Create a new forklift login session
    
    IMPORTANT: Only closes sessions for the SAME operator_barcode.
    Different operators can have active sessions simultaneously.
    """
    
    # Deactivate old sessions for THIS SPECIFIC operator only
    # This ensures that different operators don't affect each other
    old_sessions = ForkliftLoginSession.query.filter_by(
        OperatorBarcode=operator_barcode,  # Same operator only!
        IsActive=True
    ).all()
    
    if old_sessions:
        current_app.logger.info(
            f"🔄 Operator {operator_barcode} logging in from new device. "
            f"Closing {len(old_sessions)} old session(s) for THIS operator only."
        )
    
    for old_session in old_sessions:
        old_session.IsActive = False
        old_session.LogoutAt = datetime.utcnow()
        current_app.logger.debug(
            f"   ❌ Closed session for {operator_barcode} on device: {old_session.DeviceId}"
        )
    
    # Create new session
    token = generate_session_token()
    expires_at = datetime.utcnow() + timedelta(hours=session_hours)
    
    # Get request metadata
    ip_address = request.remote_addr if request else None
    user_agent = request.headers.get('User-Agent') if request else None
    
    # Build metadata
    metadata = {
        "deviceId": device_id,
        "appVersion": request.headers.get('X-App-Version') if request else None,
        "platform": request.headers.get('X-Platform') if request else None
    }
    
    session = ForkliftLoginSession(
        OperatorBarcode=operator_barcode,
        OperatorName=operator_name,
        DeviceId=device_id,
        SessionToken=token,
        IsActive=True,
        IsAdmin=is_admin,
        Role=role,
        LoginAt=datetime.utcnow(),
        ExpiresAt=expires_at,
        IpAddress=ip_address,
        UserAgent=user_agent,
        Metadata=json.dumps(metadata)
    )
    
    db.session.add(session)
    db.session.commit()
    
    return session


def logout_forklift_session(token: str) -> bool:
    """Logout a forklift session"""
    session = ForkliftLoginSession.query.filter_by(
        SessionToken=token,
        IsActive=True
    ).first()
    
    if not session:
        return False
    
    session.IsActive = False
    session.LogoutAt = datetime.utcnow()
    db.session.commit()
    
    return True
