"""
Phase 8M Request/Response Schemas - Pydantic Models
Validation & documentation for API endpoints
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any


# ============================================================================
# CONTACTS MANAGEMENT SCHEMAS (Feature 1: Whitelist/Blacklist)
# ============================================================================

class AIToggleRequest(BaseModel):
    """Toggle AI for specific contact"""
    ai_enabled: bool = Field(..., description="Enable or disable AI for this contact")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"ai_enabled": False}
        }
    )


class BulkPhoneRequest(BaseModel):
    """Bulk operation on multiple phone numbers"""
    phones: List[str] = Field(..., description="List of phone numbers")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"phones": ["237666123456", "237777777777"]}
        }
    )


class ContactInfoResponse(BaseModel):
    """Contact information response"""
    phone_number: str
    ai_enabled: bool
    message_count: int
    contact_name: Optional[str]
    first_seen: Optional[str]
    last_seen: Optional[str]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "phone_number": "237666123456",
                "ai_enabled": True,
                "message_count": 42,
                "contact_name": "Patrick Ngoumou",
                "first_seen": "2025-01-15T10:00:00Z",
                "last_seen": "2025-01-15T14:30:00Z"
            }
        }
    )


# ============================================================================
# TENANT SETTINGS SCHEMAS (Feature 3: Response Delay)
# ============================================================================

class SetTenantDelayRequest(BaseModel):
    """Set tenant-wide response delay"""
    response_delay_seconds: int = Field(
        ..., 
        description="Delay in seconds: 0, 15, 30, 60, or 120"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"response_delay_seconds": 30}
        }
    )


class SetContactDelayRequest(BaseModel):
    """Set custom delay for specific contact"""
    response_delay_seconds: int = Field(
        ..., 
        description="Custom delay in seconds for this contact: 0, 15, 30, 60, or 120"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"response_delay_seconds": 0}
        }
    )


class TenantSettingsResponse(BaseModel):
    """Tenant settings response"""
    tenant_id: int
    response_delay_seconds: int
    contact_delays: Optional[Dict[str, int]]
    last_updated: Optional[str]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tenant_id": 1,
                "response_delay_seconds": 30,
                "contact_delays": {
                    "237666123456": 0,
                    "237777777777": 60
                },
                "last_updated": "2025-01-15T14:30:00Z"
            }
        }
    )


class QueuedMessageResponse(BaseModel):
    """Queued message info"""
    id: Optional[int]
    conversation_id: int
    phone_number: str
    response_text: str
    send_at: str
    sent: bool
    retry_count: int
    created_at: Optional[str]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "conversation_id": 42,
                "phone_number": "237666123456",
                "response_text": "Bonjour! Comment puis-je vous aider?",
                "send_at": "2025-01-15T14:30:30Z",
                "sent": False,
                "retry_count": 0,
                "created_at": "2025-01-15T14:30:00Z"
            }
        }
    )


class DelayOptionsResponse(BaseModel):
    """Available delay options"""
    options: Dict[int, str]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "options": {
                    0: "Instantané (urgent)",
                    15: "Très rapide (impatient)",
                    30: "Recommandé (normal)",
                    60: "Modéré (naturel)",
                    120: "Très lent (premium)"
                }
            }
        }
    )


# ============================================================================
# HUMAN DETECTION SCHEMAS (Feature 2: Human Intervention)
# ============================================================================

class MarkHumanRequest(BaseModel):
    """Mark human active/inactive"""
    confidence: Optional[float] = Field(
        None, 
        description="Confidence level (0-100%) for human detection"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"confidence": 85.5}
        }
    )


class ConversationStateResponse(BaseModel):
    """Conversation human state"""
    conversation_id: int
    human_active: bool
    ai_paused_at: Optional[str]
    last_human_message_at: Optional[str]
    detection_confidence: float
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "conversation_id": 42,
                "human_active": True,
                "ai_paused_at": "2025-01-15T14:25:00Z",
                "last_human_message_at": "2025-01-15T14:24:00Z",
                "detection_confidence": 92.0
            }
        }
    )


# ============================================================================
# WHATSAPP QR SCHEMAS (QR Management)
# ============================================================================

class GenerateQRRequest(BaseModel):
    """Generate new WhatsApp QR code"""
    session_id: Optional[str] = Field(None, description="Optional custom session ID")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"session_id": "tenant-123-session"}
        }
    )


class QRStatusResponse(BaseModel):
    """QR Code status"""
    session_id: str
    phone_number: Optional[str]
    status: str  # pending, connected, expired, disconnected
    qr_code_data: Optional[str]
    qr_expires_at: Optional[str]
    session_expires_at: Optional[str]
    created_at: Optional[str]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "tenant-123-session",
                "phone_number": "237666123456",
                "status": "connected",
                "qr_code_data": "data:image/png;base64,...",
                "qr_expires_at": "2025-01-15T14:35:00Z",
                "session_expires_at": "2025-02-14T14:30:00Z",
                "created_at": "2025-01-15T14:30:00Z"
            }
        }
    )


class RegenerateQRRequest(BaseModel):
    """Regenerate QR if expired"""
    force: bool = Field(False, description="Force regenerate even if not expired")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"force": False}
        }
    )


class DisconnectReconnectRequest(BaseModel):
    """Disconnect and get new QR"""
    reason: Optional[str] = Field(None, description="Reason for reconnection")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"reason": "Session expired"}
        }
    )


# ============================================================================
# GENERIC RESPONSE SCHEMAS
# ============================================================================

class SuccessResponse(BaseModel):
    """Generic success response"""
    status: str = "success"
    data: Optional[Any] = None
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Generic error response"""
    status: str = "error"
    error: Optional[str] = None
    message: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: str
    services_status: Dict[str, str]
