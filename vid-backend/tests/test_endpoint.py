import httpx
import json
import time
import os

BASE_URL = "http://localhost:8000/api/v1" if os.getenv("APP_ENV") != "production" else "https://vid.redemption.africa/api/v1"

def test_endpoint(name, method, path, data=None):
    print(f"Testing {name} [{method} {path}]...")
    try:
        if method == "GET":
            response = httpx.get(f"{BASE_URL}{path}", timeout=30.0)
        else:
            response = httpx.post(f"{BASE_URL}{path}", json=data, timeout=30.0)
        
        print(f"Status: {response.status_code}")
        if response.status_code >= 400:
            print(f"Error: {response.text}")
        else:
            print("Success!")
            # print(json.dumps(response.json(), indent=2))
        return response.json() if response.status_code < 400 else None
    except Exception as e:
        print(f"Failed: {e}")
        return None

def run_all_tests():
    print("--- VID API ENDPOINT TESTS ---")
    
    # 1. Health
    test_endpoint("Health", "GET", "/health")
    
    # 2. Countries
    test_endpoint("Countries", "GET", "/countries")
    
    # 3. Resolve Phone
    phone_data = {"phone": "+2348031234567"}
    test_endpoint("Resolve Phone", "POST", "/resolve-phone", data=phone_data)
    
    # 4. Enroll
    enroll_data = {
        "phone_numbers": [
            {"number": "+2348031234567", "is_primary": True}
        ],
        "full_name": "Test User",
        "consent": True
    }
    enroll_res = test_endpoint("Enroll", "POST", "/enroll", data=enroll_data)
    
    if enroll_res and "certificate" in enroll_res:
        vid_id = enroll_res["certificate"]["vid_id"]
        print(f"Enrollment successful. VID ID: {vid_id}")
        
        # 5. Verify
        test_endpoint("Verify", "GET", f"/verify/{vid_id}")
    else:
        print("Enrollment failed, skipping Verify test.")

if __name__ == "__main__":
    run_all_tests()
