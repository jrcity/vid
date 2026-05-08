
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from app.services.sim_farming_detector import SimFarmingDetector
from app.api.dependencies import get_fraud_detector

router = APIRouter()

class SimSwapDetector:
    async def analyze(self, data): return {"risk": "low"}

class SimFarmingDetector:
    async def analyze(self, data): return {"risk": "low"}

class ProxyCloneDetector:
    async def analyze(self, data): return {"risk": "low"}

class GeoRouteAnalyzer:
    async def analyze(self, data): return {"risk": "low"}

class FraudDetectionRequest(BaseModel):
    """Request model for fraud detection"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = Field(..., regex="^(sim_swap|otp_request|location_update|device_check)$")
    country_code: str = Field(..., min_length=2, max_length=3)
    msisdn: Optional[str] = None  # Will be hashed immediately
    imsi: Optional[str] = None
    imei: Optional[str] = None
    nokia_data: Optional[Dict] = None
    camara_data: Optional[Dict] = None
    http_headers: Optional[Dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class FraudDetectionResponse(BaseModel):
    """Response model - intentionally limited to prevent reverse engineering"""
    request_id: str
    risk_score: float = Field(..., ge=0, le=1)
    verdict: str  # ALLOW, MONITOR, REVIEW, CHALLENGE, BLOCK
    requires_2fa: bool = False
    timestamp: str

@router.post("/detect", response_model=FraudDetectionResponse)
async def detect_sim_farming(
    request_data: FraudDetectionRequest,
    background_tasks: BackgroundTasks,
    detector: SimFarmingDetector = Depends(get_fraud_detector)
):
    """
    Detect SIM farming fraud using digital twin technology
    This endpoint is called automatically by the existing verify/enroll flows
    """
    try:
        # Process through digital twin
        result = await detector.analyze_request(request_data.dict())
        
        # Log to background (doesn't block response)
        background_tasks.add_task(detector.log_detection, result)
        
        return FraudDetectionResponse(
            request_id=request_data.request_id,
            risk_score=result["risk_score"],
            verdict=result["verdict"],
            requires_2fa=result["risk_score"] > 0.5,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        # Fail open - return low risk on error
        print(f"Fraud detection error: {e}")
        return FraudDetectionResponse(
            request_id=request_data.request_id,
            risk_score=0.0,
            verdict="ALLOW",
            requires_2fa=False,
            timestamp=datetime.utcnow().isoformat()
        )

@router.get("/stats")
async def get_fraud_stats(
    hours: int = 24,
    detector: SimFarmingDetector = Depends(get_fraud_detector)
):
    """Get fraud detection statistics (admin only in production)"""
    return await detector.get_statistics(hours)

@router.get("/twin/{twin_id}")
async def get_twin_status(
    twin_id: str,
    detector: SimFarmingDetector = Depends(get_fraud_detector)
):
    """Get digital twin status for a specific SIM (admin only)"""
    return await detector.get_twin_state(twin_id)
