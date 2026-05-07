from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from typing import Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

router = APIRouter(tags=["Fraud Detection"])

class FraudDetectionRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = Field(..., regex="^(sim_swap|otp_request|location_update|device_check)$")
    country_code: str = Field(..., min_length=2, max_length=3)
    msisdn: Optional[str] = None
    imsi: Optional[str] = None
    imei: Optional[str] = None
    nokia_data: Optional[Dict] = None
    camara_data: Optional[Dict] = None
    http_headers: Optional[Dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class FraudDetectionResponse(BaseModel):
    request_id: str
    risk_score: float = Field(..., ge=0, le=1)
    verdict: str
    requires_2fa: bool = False
    timestamp: str

async def get_detector(request: Request):
    if not hasattr(request.app.state, 'fraud_detector'):
        return None
    return request.app.state.fraud_detector

@router.post("/detect", response_model=FraudDetectionResponse)
async def detect_sim_farming(
    request_data: FraudDetectionRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    detector = Depends(get_detector)
):
    if not detector:
        return FraudDetectionResponse(
            request_id=request_data.request_id,
            risk_score=0.0,
            verdict="ALLOW",
            requires_2fa=False,
            timestamp=datetime.utcnow().isoformat()
        )
    
    try:
        result = await detector.analyze_request(request_data.dict())
        
        background_tasks.add_task(detector.log_detection, result)
        
        return FraudDetectionResponse(
            request_id=request_data.request_id,
            risk_score=result["risk_score"],
            verdict=result["verdict"],
            requires_2fa=result["risk_score"] > 0.5,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
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
    request: Request,
    detector = Depends(get_detector)
):
    if not detector:
        return {"error": "Fraud detector not initialized"}
    return await detector.get_statistics(hours)

@router.get("/twin/{twin_id}")
async def get_twin_status(
    twin_id: str,
    request: Request,
    detector = Depends(get_detector)
):
    if not detector:
        return {"error": "Fraud detector not initialized"}
    return await detector.get_twin_state(twin_id)
