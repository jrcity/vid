import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, deque
from dataclasses import dataclass

@dataclass
class TowerEvent:
    tower_id: str
    timestamp: datetime
    lat: float
    lon: float
    signal_strength: float
    event_type: str

class GeoRouteAnalyzer:
    
    def __init__(self, graph_db=None):
        self.graph_db = graph_db
        self.location_history = defaultdict(lambda: deque(maxlen=1000))
        self.tower_transition_matrix = defaultdict(lambda: defaultdict(int))
        
    def update_location_history(self, twin_id: str, tower_event: TowerEvent):
        self.location_history[twin_id].append(tower_event)
        
        history_list = list(self.location_history[twin_id])
        if len(history_list) >= 2:
            prev = history_list[-2]
            curr = history_list[-1]
            key = f"{prev.tower_id}->{curr.tower_id}"
            self.tower_transition_matrix[twin_id][key] += 1
    
    def detect_rapid_tower_hopping(self, twin_id: str) -> Tuple[float, Dict]:
        history = self.location_history[twin_id]
        if len(history) < 5:
            return 0.0, {"message": "Insufficient data"}
        
        rapid_moves = []
        anomalies = []
        
        for i in range(1, len(history)):
            prev = history[i-1]
            curr = history[i]
            time_diff = (curr.timestamp - prev.timestamp).total_seconds()
            
            distance_km = self._calculate_distance(
                prev.lat, prev.lon, curr.lat, curr.lon
            )
            min_possible_time = distance_km / 100
            min_possible_ms = min_possible_time * 1000
            
            if time_diff * 1000 < min_possible_ms * 0.5:
                rapid_moves.append({
                    "from": prev.tower_id,
                    "to": curr.tower_id,
                    "actual_ms": time_diff * 1000,
                    "min_possible_ms": min_possible_ms
                })
        
        attaches = [e for e in history if e.event_type == 'attach']
        rapid_reattaches = 0
        for i in range(1, len(attaches)):
            time_diff = (attaches[i].timestamp - attaches[i-1].timestamp).total_seconds()
            if time_diff < 30:
                rapid_reattaches += 1
        
        risk_score = 0.0
        reasons = []
        
        if len(rapid_moves) > 3:
            risk_score += min(0.5, len(rapid_moves) * 0.1)
            reasons.append(f"Detected {len(rapid_moves)} physically impossible tower hops")
        
        if rapid_reattaches > 5:
            risk_score += 0.4
            reasons.append(f"Detected {rapid_reattaches} rapid re-attaches - possible proxy cycling")
        
        avg_latency = self._calculate_avg_latency(history)
        if avg_latency > 200:
            risk_score += min(0.3, avg_latency / 1000)
            reasons.append(f"High average latency: {avg_latency:.0f}ms - possible remote SIM")
        
        risk_score = min(1.0, risk_score)
        
        return risk_score, {
            "risk_score": risk_score,
            "reasons": reasons,
            "rapid_hops": len(rapid_moves),
            "reattach_count": rapid_reattaches,
            "avg_latency_ms": avg_latency,
            "sample_hops": rapid_moves[:3]
        }
    
    def detect_impossible_travel(self, twin_id: str, 
                                  current_loc: Dict, 
                                  last_loc: Optional[Dict]) -> float:
        if not last_loc or not current_loc:
            return 0.0
        
        distance_km = self._calculate_distance(
            last_loc.get('lat'), last_loc.get('lon'),
            current_loc.get('lat'), current_loc.get('lon')
        )
        
        last_time = datetime.fromisoformat(last_loc.get('timestamp'))
        current_time = datetime.fromisoformat(current_loc.get('timestamp'))
        time_diff_hours = (current_time - last_time).total_seconds() / 3600
        
        if time_diff_hours <= 0:
            return 0.0
        
        speed_kmh = distance_km / time_diff_hours
        
        if speed_kmh > 1000:
            return min(1.0, speed_kmh / 5000)
        
        return 0.0
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2) -> float:
        from math import radians, sin, cos, sqrt, atan2
        
        if None in [lat1, lon1, lat2, lon2]:
            return 0
        
        R = 6371
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def _calculate_avg_latency(self, history: List[TowerEvent]) -> float:
        latencies = []
        for i in range(1, len(history)):
            if hasattr(history[i], 'signal_strength') and history[i].signal_strength < 0:
                signal = history[i].signal_strength
                if signal > -50:
                    latencies.append(20)
                elif signal > -70:
                    latencies.append(50)
                elif signal > -90:
                    latencies.append(100)
                else:
                    latencies.append(200)
        
        return np.mean(latencies) if latencies else 0
