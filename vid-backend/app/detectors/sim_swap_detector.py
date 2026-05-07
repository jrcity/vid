import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import deque

class SimSwapDetector:
    """
    SIM Swap Fraud Detection using Digital Twin patterns
    Links SIM swap events with OTP request patterns
    """
    
    def __init__(self, graph_db=None):
        self.graph_db = graph_db
        self.swap_history = {}
        self.otp_tracking = {}
        self.location_history = {}
        
    def analyze_sim_swap_pattern(self, twin_id: str, 
                                  swap_event: Dict,
                                  current_location: Dict) -> Tuple[float, Dict]:
        """
        Detect SIM swap fraud by analyzing pattern correlation
        Returns: risk_score (0-1), details dict
        """
        risk_score = 0.0
        reasons = []
        
        if twin_id not in self.swap_history:
            self.swap_history[twin_id] = deque(maxlen=100)
        self.swap_history[twin_id].append(swap_event)
        
        recent_swaps = [
            s for s in self.swap_history[twin_id]
            if (datetime.utcnow() - datetime.fromisoformat(s['timestamp'])).days < 7
        ]
        
        if len(recent_swaps) > 3:
            risk_score += 0.4
            reasons.append(f"High swap frequency: {len(recent_swaps)} swaps in 7 days")
        
        if twin_id in self.otp_tracking:
            recent_otp = [
                otp for otp in self.otp_tracking[twin_id]
                if (datetime.utcnow() - datetime.fromisoformat(otp['timestamp'])).seconds < 300
            ]
            
            for swap in recent_swaps:
                swap_time = datetime.fromisoformat(swap['timestamp'])
                for otp in recent_otp:
                    otp_time = datetime.fromisoformat(otp['timestamp'])
                    time_diff = abs((swap_time - otp_time).total_seconds())
                    
                    if time_diff < 600:
                        risk_score += 0.5
                        reasons.append(f"SIM swap + OTP request within {time_diff:.0f} seconds")
        
        if current_location and swap_event.get('new_device_location'):
            old_loc = swap_event.get('old_device_location', {})
            new_loc = swap_event.get('new_device_location', {})
            
            if old_loc and new_loc:
                distance = self._calculate_distance(
                    old_loc.get('lat'), old_loc.get('lon'),
                    new_loc.get('lat'), new_loc.get('lon')
                )
                if distance > 500:
                    risk_score += min(0.3, distance / 1000 * 0.1)
                    reasons.append(f"Suspicious location jump: {distance:.0f}km after swap")
        
        risk_score = min(1.0, risk_score)
        
        return risk_score, {
            "risk_score": risk_score,
            "reasons": reasons,
            "swap_count_7d": len(recent_swaps),
            "recommendation": "BLOCK" if risk_score > 0.7 else "REVIEW" if risk_score > 0.3 else "ALLOW"
        }
    
    def track_otp_request(self, twin_id: str, otp_request: Dict):
        if twin_id not in self.otp_tracking:
            self.otp_tracking[twin_id] = deque(maxlen=50)
        self.otp_tracking[twin_id].append(otp_request)
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2) -> float:
        if None in [lat1, lon1, lat2, lon2]:
            return 0
        return ((lat1 - lat2)**2 + (lon1 - lon2)**2)**0.5 * 111
