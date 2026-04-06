import requests
import random
import time
from datetime import datetime

API = "http://localhost:8000/api/v1"

def test(name, condition, details=""):
    print(f"[{'PASS' if condition else 'FAIL'}] {name} {details}")
    if not condition:
        raise Exception(f"Failed: {name} - {details}")

def run_tests():
    print("Testing 1-day manual entry corner case...")
    
    # 1. Register new mock user
    email = f"test_{int(time.time())}@example.com"
    r = requests.post(f"{API}/auth/register", json={
        "email": email,
        "password": "password123",
        "monthly_income": 50000,
        "full_name": "Test User"
    })
    test("Register new user", r.status_code == 201, r.text)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Upload sparse manual data (just today)
    r = requests.post(f"{API}/transactions/bulk", json={
        "transactions": [
            {"date": datetime.today().strftime("%Y-%m-%d"), "amount": 1000, "category": "Food"},
            {"date": datetime.today().strftime("%Y-%m-%d"), "amount": 500, "category": "Transport"},
        ]
    }, headers=headers)
    test("Upload sparse data", r.status_code == 201, r.text)
    
    # 3. Check Predict Endpoint
    r = requests.get(f"{API}/predict?forecast_days=30", headers=headers)
    test("GET /predict", r.status_code == 200, r.text[:200])
    
    # 4. Check Recommend Endpoint
    r = requests.get(f"{API}/recommend", headers=headers)
    test("GET /recommend", r.status_code == 200, r.text[:200])
    
    # 5. Check Explain Endpoint
    r = requests.get(f"{API}/explain", headers=headers)
    test("GET /explain", r.status_code == 200, r.text[:200])

    print("\nAll corner case tests passed successfully!")

if __name__ == "__main__":
    run_tests()
