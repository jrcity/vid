import asyncio
import os
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
import logging

from app.detectors.sim_swap_detector import SimSwapDetector
from app.detectors.geo_route_analyzer import GeoRouteAnalyzer, TowerEvent
from app.detectors.proxy_clone_detector import ProxyCloneDetector

logger = logging.getLogger(__name__)

class SimFarmingDetector:
    
    def __init__(self):
        self.sim_swap_detector = SimSwapDetector()
        self.geo_analyzer = GeoRouteAnalyzer()
        self.proxy_detector = ProxyCloneDetector()
        self.twin_state = {}
        self.is_healthy = True
        
        self.enabled = os.getenv("SIM_FARMING_ENABLED", "true").lower() == "true"
        self.risk_threshold = float(os.getenv("SIM_FARMING_RISK_THRESHOLD", "0.7"))
        
        self.country_salts = {
            "NG": os.getenv("SALT_NIGERIA", "ng_salt_2024"),
            "KE": os.getenv("SALT_KENYA", "ke_salt_2024"),
            "GH": os.getenv("SALT_GHANA", "gh_salt_2024"),
            "ZA": os.getenv("SOUTH_AFRICA", "za_salt_2024"),
            "ET": os.getenv("SALT_ETHIOPIA", "et_salt_2024"),
            "DEFAULT": os.getenv("SALT_DEFAULT", "default_salt_2024")
        }
        
    async def initialize(self):
        try:
            logger.info("Initializing SIM Farming Detector")
            self.is_healthy = True
            logger.info("SIM Farming Detector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SIM Farming Detector: {e}")
            self.is_healthy = False
    
    async def shutdown(self):
        logger.info("Shutting down SIM Farming Detector")
    
    async def analyze_request(self, request_data: Dict) -> Dict:
        if not self.enabled:
            return {"risk_score": 0.0, "verdict": "ALLOW"}
        
        try:
            anonymized = self._anonymize_pii(request_data)
            twin_id = anonymized["twin_id"]
            
            tasks = [
                self._check_sim_swap(twin_id, request_data),
                self._check_location_anomaly(twin_id, request_data),
                self._check_proxy_clone(twin_id, request_data),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            risk_scores = [r.get("risk_score", 0) for r in results if isinstance(r, dict)]
            avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0
            
            verdict = self._determine_verdict(avg_risk)
            
            await self._update_twin_state(twin_id, request_data, avg_risk)
            
            return {
                "twin_id": twin_id,
                "risk_score": avg_risk,
                "verdict": verdict,
                "details": results if avg_risk > self.risk_threshold else None
            }
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {"risk_score": 0.0, "verdict": "ALLOW"}
    
    def _anonymize_pii(self, data: Dict) -> Dict:
        country = data.get("country_code", "DEFAULT")
        salt = self.country_salts.get(country, self.country_salts["DEFAULT"])
        
        composite = []
        for field in ["msisdn", "imsi", "imei"]:
            if data.get(field):
                composite.append(f"{field}={data[field]}")
        
        composite_str = "|".join(sorted(composite))
        twin_id = hmac.new(
            salt.encode(),
            composite_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return {"twin_id": twin_id, "country": country}
    
    async def _check_sim_swap(self, twin_id: str, data: Dict) -> Dict:
        if data.get("event_type") == "sim_swap":
            return self.sim_swap_detector.analyze_sim_swap_pattern(
                twin_id, data, data.get("nokia_data", {})
            )
        return {"risk_score": 0.0}
    
    async def _check_location_anomaly(self, twin_id: str, data: Dict) -> Dict:
        location = data.get("nokia_data", {}).get("location")
        if location:
            tower_event = TowerEvent(
                tower_id=location.get("tower_id", "unknown"),
                timestamp=datetime.utcnow(),
                lat=location.get("latitude", 0),
                lon=location.get("longitude", 0),
                signal_strength=location.get("signal_strength", -100),
                event_type=data.get("event_type", "location_update")
            )
            self.geo_analyzer.update_location_history(twin_id, tower_event)
            risk, details = self.geo_analyzer.detect_rapid_tower_hopping(twin_id)
            return {"risk_score": risk, "details": details}
        return {"risk_score": 0.0}
    
    async def _check_proxy_clone(self, twin_id: str, data: Dict) -> Dict:
        network_report = data.get("nokia_data", {})
        http_headers = data.get("http_headers", {})
        
        risk, details = self.proxy_detector.analyze_fingerprint_consistency(
            twin_id, network_report, http_headers
        )
        return {"risk_score": risk, "details": details}
    
    def _determine_verdict(self, risk_score: float) -> str:
        if risk_score > 0.8:
            return "BLOCK"
        elif risk_score > 0.6:
            return "CHALLENGE"
        elif risk_score > 0.4:
            return "REVIEW"
        elif risk_score > 0.2:
            return "MONITOR"
        else:
            return "ALLOW"
    
    async def _update_twin_state(self, twin_id: str, data: Dict, risk: float):
        if twin_id not in self.twin_state:
            self.twin_state[twin_id] = {
                "first_seen": datetime.utcnow(),
                "last_seen": datetime.utcnow(),
                "risk_history": [],
                "event_count": 0
            }
        
        state = self.twin_state[twin_id]
        state["last_seen"] = datetime.utcnow()
        state["risk_history"].append((datetime.utcnow(), risk))
        state["event_count"] += 1
        
        if len(state["risk_history"]) > 100:
            state["risk_history"] = state["risk_history"][-100:]
    
    async def get_statistics(self, hours: int = 24):
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        stats = {
            "total_requests": 0,
            "high_risk_count": 0,
            "blocked_count": 0,
            "active_twins": 0
        }
        
        for twin_id, state in self.twin_state.items():
            if state["last_seen"] > cutoff:
                stats["total_requests"] += state["event_count"]
                stats["active_twins"] += 1
                
                recent_risks = [r for t, r in state["risk_history"] if t > cutoff]
                if recent_risks and max(recent_risks) > 0.8:
                    stats["high_risk_count"] += 1
                    stats["blocked_count"] += 1
        
        return stats
    
    async def get_twin_state(self, twin_id: str) -> Dict:
        if twin_id in self.twin_state:
            state = self.twin_state[twin_id].copy()
            state["risk_history"] = [
                {"time": t.isoformat(), "risk": r} 
                for t, r in state["risk_history"][-10:]
            ]
            return state
        return {"error": "Twin not found"}
    
    async def log_detection(self, detection_result: Dict):
        logger.info(f"Detection logged: {detection_result.get('twin_id')} - {detection_result.get('verdict')}")
