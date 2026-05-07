from typing import Dict, List, Tuple, Optional
from collections import defaultdict, deque
from datetime import datetime

class ProxyCloneDetector:
    
    def __init__(self):
        self.device_fingerprints = defaultdict(dict)
        self.ip_location_cache = {}
        self.identity_clusters = defaultdict(set)
        
    def analyze_fingerprint_consistency(self, twin_id: str, 
                                         network_report: Dict,
                                         http_headers: Dict) -> Tuple[float, Dict]:
        inconsistencies = []
        risk_score = 0.0
        
        network_os = network_report.get('device_os', '').lower()
        http_ua = http_headers.get('user-agent', '').lower()
        
        if network_os and http_ua:
            if network_os == 'android' and 'android' not in http_ua:
                inconsistencies.append("Network says Android, HTTP UA doesn't match")
                risk_score += 0.3
            elif network_os == 'ios' and ('iphone' not in http_ua and 'ipad' not in http_ua):
                inconsistencies.append("Network says iOS, HTTP UA doesn't match")
                risk_score += 0.3
            elif network_os == 'windows' and 'windows' not in http_ua:
                inconsistencies.append("Network says Windows, HTTP UA doesn't match")
                risk_score += 0.3
        
        network_model = network_report.get('device_model', '')
        if network_model and http_ua:
            if network_model.lower() not in http_ua and len(network_model) > 3:
                inconsistencies.append(f"Network model '{network_model}' not in User-Agent")
                risk_score += 0.2
        
        tower_country = network_report.get('location', {}).get('country_code', '')
        ip_country = self._get_ip_country(http_headers.get('x-forwarded-for', ''))
        
        if tower_country and ip_country and tower_country != ip_country:
            inconsistencies.append(f"Tower in {tower_country} but IP in {ip_country}")
            risk_score += 0.4
        
        device_id = network_report.get('device_id')
        if device_id:
            self.identity_clusters[device_id].add(twin_id)
            if len(self.identity_clusters[device_id]) > 5:
                inconsistencies.append(f"Device {device_id[:8]} used by {len(self.identity_clusters[device_id])} identities")
                risk_score += min(0.5, len(self.identity_clusters[device_id]) * 0.05)
        
        risk_score = min(1.0, risk_score)
        
        return risk_score, {
            "risk_score": risk_score,
            "inconsistencies": inconsistencies,
            "recommendation": "BLOCK" if risk_score > 0.7 else "REVIEW_DEVICE"
        }
    
    def detect_proxy_chain(self, network_path: List[Dict]) -> Tuple[float, List[str]]:
        if len(network_path) < 2:
            return 0.0, []
        
        suspicious_patterns = []
        risk_score = 0.0
        
        if len(network_path) > 5:
            suspicious_patterns.append(f"Unusual hop count: {len(network_path)}")
            risk_score += min(0.3, len(network_path) * 0.05)
        
        for i in range(1, len(network_path)):
            hop = network_path[i]
            prev_hop = network_path[i-1]
            latency_gap = hop.get('latency', 0) - prev_hop.get('latency', 0)
            
            if latency_gap > 50:
                suspicious_patterns.append(f"Large latency jump at hop {i}: +{latency_gap}ms")
                risk_score += 0.1
        
        asns = [hop.get('asn') for hop in network_path if hop.get('asn')]
        if len(set(asns)) > 2:
            suspicious_patterns.append(f"Multiple ASNs detected: {set(asns)}")
            risk_score += 0.2
        
        risk_score = min(1.0, risk_score)
        
        return risk_score, suspicious_patterns
    
    def detect_otp_hijack(self, twin_id: str, 
                          otp_request_time: datetime,
                          network_events: List[Dict]) -> float:
        risk_score = 0.0
        
        for event in network_events:
            event_time = datetime.fromisoformat(event['timestamp'])
            time_diff = abs((otp_request_time - event_time).total_seconds())
            
            if time_diff < 10:
                if event.get('event_type') == 'handover' and time_diff < 5:
                    risk_score += 0.3
                if event.get('message_type') == 'sms' and event.get('direction') == 'incoming':
                    risk_score += 0.2
        
        return min(1.0, risk_score)
    
    def _get_ip_country(self, ip_address: str) -> str:
        if ip_address in self.ip_location_cache:
            return self.ip_location_cache[ip_address]
        return "UNKNOWN"
