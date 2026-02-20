"""
Real-time event broadcasting service using Flask-SocketIO
"""
from typing import Any, Dict, Optional
from datetime import datetime
from ..extensions import socketio


class RealtimeService:
    """Service for broadcasting real-time updates to connected clients"""
    
    @staticmethod
    def emit_dolly_update(event_type: str, data: Optional[Dict[str, Any]] = None, room: Optional[str] = None):
        """
        Broadcast dolly-related updates to clients
        
        Args:
            event_type: Type of update (e.g., 'manual_collection', 'group_created', 'task_updated')
            data: Additional data to send with the event
            room: Specific room to broadcast to (None = broadcast to all)
        """
        payload = {
            'type': event_type,
            'data': data or {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Emit to all connected clients (no room or broadcast parameter needed)
        socketio.emit('dolly_update', payload, namespace='/')
    
    @staticmethod
    def emit_task_update(task_id: int, status: str, data: Optional[Dict[str, Any]] = None):
        """Broadcast task status updates"""
        payload = {
            'type': 'task_updated',
            'task_id': task_id,
            'status': status,
            'data': data or {}
        }
        socketio.emit('task_update', payload, namespace='/')
    
    @staticmethod
    def emit_manual_collection(group_id: int, group_name: str, dolly_count: int, actor: str):
        """Broadcast manual collection event"""
        payload = {
            'type': 'manual_collection',
            'group_id': group_id,
            'group_name': group_name,
            'dolly_count': dolly_count,
            'actor': actor
        }
        socketio.emit('dolly_update', payload, namespace='/')
    
    @staticmethod
    def emit_group_created(group_id: int, group_name: str):
        """Broadcast group creation event"""
        payload = {
            'type': 'group_created',
            'group_id': group_id,
            'group_name': group_name
        }
        socketio.emit('dolly_update', payload, namespace='/')
    
    @staticmethod
    def emit_shipment_update(shipment_tag: str, status: str):
        """Broadcast shipment status updates"""
        payload = {
            'type': 'shipment_updated',
            'shipment_tag': shipment_tag,
            'status': status
        }
        socketio.emit('dolly_update', payload, namespace='/')
    
    @staticmethod
    def emit_notification(message: str, notification_type: str = 'info', target_user: Optional[str] = None):
        """
        Send notification to users
        
        Args:
            message: Notification message
            notification_type: 'info', 'success', 'warning', 'error'
            target_user: Specific user to notify (None = all users)
        """
        payload = {
            'type': 'notification',
            'message': message,
            'notification_type': notification_type
        }
        
        socketio.emit('notification', payload, namespace='/')
