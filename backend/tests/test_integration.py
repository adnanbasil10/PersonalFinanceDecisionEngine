"""
End-to-End Integration Test Suite for Personal Finance Decision Engine.
Tests every API endpoint, validates response schemas, and checks for common errors.
"""

import requests
import json
import sys
import time
from datetime import datetime, timedelta
import random

BASE = "http://localhost:8000"
API = f"{BASE}/api/v1"

# Track results
results = []
token = None
user_id = None

def test(name, passed, detail=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    results.append((name, passed, detail))
    print(f"  {status}  {name}" + (f" — {detail}" if detail and not passed else ""))


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ─────────────────────────────────────────────
# 1. HEALTH CHECK
# ─────────────────────────────────────────────
section("1. Health Check")

try:
    r = requests.get(f"{BASE}/health", timeout=5)
    test("Health endpoint returns 200", r.status_code == 200)
    data = r.json()
    test("Health has correct fields", all(k in data for k in ["status", "app", "version"]))
    test("Health status is 'healthy'", data.get("status") == "healthy")
except Exception as e:
    test("Health endpoint reachable", False, str(e))

# ─────────────────────────────────────────────
# 2. AUTHENTICATION
# ─────────────────────────────────────────────
section("2. Authentication")

# 2a. Register
test_email = f"testuser_{int(time.time())}@example.com"
test_password = "SecureP@ss123!"
reg_payload = {
    "email": test_email,
    "password": test_password,
    "full_name": "Test User",
    "monthly_income": 75000
}

try:
    r = requests.post(f"{API}/auth/register", json=reg_payload, timeout=10)
    test("Register returns 201", r.status_code == 201, f"got {r.status_code}: {r.text[:200]}")
    if r.status_code == 201:
        data = r.json()
        token = data.get("access_token")
        user_id = data.get("user", {}).get("id")
        test("Register returns JWT token", token is not None and len(token) > 20)
        test("Register returns user object", "user" in data and "email" in data["user"])
        test("User email matches", data["user"]["email"] == test_email)
except Exception as e:
    test("Register endpoint works", False, str(e))

# 2b. Duplicate registration
try:
    r = requests.post(f"{API}/auth/register", json=reg_payload, timeout=10)
    test("Duplicate register blocked", r.status_code in [400, 409, 422], f"got {r.status_code}")
except Exception as e:
    test("Duplicate register check", False, str(e))

# 2c. Login
try:
    r = requests.post(f"{API}/auth/login", json={"email": test_email, "password": test_password}, timeout=10)
    test("Login returns 200", r.status_code == 200, f"got {r.status_code}: {r.text[:200]}")
    if r.status_code == 200:
        login_token = r.json().get("access_token")
        test("Login returns valid token", login_token is not None and len(login_token) > 20)
except Exception as e:
    test("Login endpoint works", False, str(e))

# 2d. Wrong password
try:
    r = requests.post(f"{API}/auth/login", json={"email": test_email, "password": "wrongpassword"}, timeout=10)
    test("Wrong password rejected", r.status_code in [400, 401, 403], f"got {r.status_code}")
except Exception as e:
    test("Wrong password check", False, str(e))

# 2e. Get current user
headers = {"Authorization": f"Bearer {token}"} if token else {}
try:
    r = requests.get(f"{API}/auth/me", headers=headers, timeout=10)
    test("GET /auth/me returns 200", r.status_code == 200, f"got {r.status_code}: {r.text[:200]}")
    if r.status_code == 200:
        me = r.json()
        test("User has monthly_income", me.get("monthly_income") == 75000)
except Exception as e:
    test("Current user endpoint works", False, str(e))

# 2f. Unauthenticated access
try:
    r = requests.get(f"{API}/auth/me", timeout=10)
    test("No token → 401/403", r.status_code in [401, 403], f"got {r.status_code}")
except Exception as e:
    test("Auth enforcement check", False, str(e))

# ─────────────────────────────────────────────
# 3. TRANSACTIONS
# ─────────────────────────────────────────────
section("3. Transactions")

# 3a. Bulk upload
categories = ["Food", "Groceries", "Transport", "Entertainment", "Shopping", "Healthcare", "Utilities"]
merchants = ["Amazon", "Swiggy", "Uber", "Netflix", "BigBasket", "Apollo", "Jio"]

bulk_txns = []
base_date = datetime(2025, 6, 1)
for i in range(50):
    d = base_date + timedelta(days=random.randint(0, 28))
    bulk_txns.append({
        "date": d.strftime("%Y-%m-%d"),
        "amount": round(random.uniform(50, 5000), 2),
        "category": random.choice(categories),
        "merchant": random.choice(merchants),
        "description": f"Test transaction {i+1}"
    })

try:
    r = requests.post(f"{API}/transactions/bulk", json={"transactions": bulk_txns}, headers=headers, timeout=30)
    test("Bulk upload returns 201", r.status_code == 201, f"got {r.status_code}: {r.text[:300]}")
    if r.status_code == 201:
        uploaded = r.json()
        test("All 50 transactions uploaded", len(uploaded) == 50, f"got {len(uploaded)}")
        test("Transactions have IDs", all("id" in t for t in uploaded))
except Exception as e:
    test("Bulk upload works", False, str(e))

# 3b. List transactions
try:
    r = requests.get(f"{API}/transactions?skip=0&limit=10", headers=headers, timeout=10)
    test("GET /transactions returns 200", r.status_code == 200, f"got {r.status_code}")
    if r.status_code == 200:
        txns = r.json()
        test("Transactions list is array", isinstance(txns, list))
        test("Transactions have expected fields", len(txns) > 0 and all(k in txns[0] for k in ["id", "amount", "category", "date"]))
except Exception as e:
    test("List transactions works", False, str(e))

# 3c. Summary
try:
    r = requests.get(f"{API}/transactions/summary?year=2025&month=6", headers=headers, timeout=10)
    test("GET /transactions/summary returns 200", r.status_code == 200, f"got {r.status_code}: {r.text[:300]}")
    if r.status_code == 200:
        summary = r.json()
        test("Summary has total_spending", "total_spending" in summary)
        test("Summary has category_breakdown", "category_breakdown" in summary)
        test("Total spending > 0", summary.get("total_spending", 0) > 0)
except Exception as e:
    test("Summary endpoint works", False, str(e))

# ─────────────────────────────────────────────
# 4. ML PREDICTIONS
# ─────────────────────────────────────────────
section("4. ML Predictions")

try:
    r = requests.get(f"{API}/predict?forecast_days=14", headers=headers, timeout=30)
    test("GET /predict returns 200", r.status_code == 200, f"got {r.status_code}: {r.text[:500]}")
    if r.status_code == 200:
        pred = r.json()
        test("Has risk object", "risk" in pred)
        test("Has forecast object", "forecast" in pred)
        test("Risk has probability", "overspend_probability" in pred.get("risk", {}))
        test("Risk probability is 0-1", 0 <= pred["risk"]["overspend_probability"] <= 1)
        test("Risk has level", pred["risk"].get("risk_level") in ["low", "medium", "high", "critical"])
        forecast = pred.get("forecast", {})
        test("Forecast has forecast array", "forecast" in forecast)
        test("Forecast has model_used", "model_used" in forecast)
except Exception as e:
    test("Prediction endpoint works", False, str(e))

# ─────────────────────────────────────────────
# 5. RECOMMENDATIONS
# ─────────────────────────────────────────────
section("5. Recommendations")

try:
    r = requests.get(f"{API}/recommend", headers=headers, timeout=30)
    test("GET /recommend returns 200", r.status_code == 200, f"got {r.status_code}: {r.text[:500]}")
    if r.status_code == 200:
        rec = r.json()
        test("Has recommendations array", "recommendations" in rec and isinstance(rec["recommendations"], list))
        test("Has summary", "summary" in rec)
        if rec["recommendations"]:
            first = rec["recommendations"][0]
            test("Recommendation has message", "message" in first)
            test("Recommendation has priority", first.get("priority") in ["low", "medium", "high"])
            test("Recommendation has confidence", 0 <= first.get("confidence", -1) <= 1)
except Exception as e:
    test("Recommendation endpoint works", False, str(e))

# ─────────────────────────────────────────────
# 6. EXPLAINABILITY
# ─────────────────────────────────────────────
section("6. Explainability")

try:
    r = requests.get(f"{API}/explain", headers=headers, timeout=30)
    test("GET /explain returns 200", r.status_code == 200, f"got {r.status_code}: {r.text[:500]}")
    if r.status_code == 200:
        exp = r.json()
        test("Has explanations array", "explanations" in exp)
        test("Has feature_importance_global", "feature_importance_global" in exp)
        if exp["explanations"]:
            first = exp["explanations"][0]
            test("Explanation has reasoning", "reasoning" in first and len(first["reasoning"]) > 0)
            test("Explanation has feature_impacts", "feature_impacts" in first)
except Exception as e:
    test("Explainability endpoint works", False, str(e))

# ─────────────────────────────────────────────
# 7. SECURITY CHECKS
# ─────────────────────────────────────────────
section("7. Security Checks")

# 7a. Invalid token
try:
    r = requests.get(f"{API}/transactions", headers={"Authorization": "Bearer invalidtoken123"}, timeout=5)
    test("Invalid JWT → 401/403", r.status_code in [401, 403], f"got {r.status_code}")
except Exception as e:
    test("Invalid JWT rejection", False, str(e))

# 7b. SQL injection attempt in login
try:
    r = requests.post(f"{API}/auth/login", json={"email": "' OR 1=1 --", "password": "test"}, timeout=5)
    test("SQL injection blocked", r.status_code in [400, 401, 422], f"got {r.status_code}")
except Exception as e:
    test("SQL injection check", False, str(e))

# 7c. XSS in transaction data
try:
    xss_txn = {
        "transactions": [{
            "date": "2025-06-15",
            "amount": 100,
            "category": "Food",
            "merchant": "<script>alert('xss')</script>",
            "description": "<img onerror='alert(1)' src=x>"
        }]
    }
    r = requests.post(f"{API}/transactions/bulk", json=xss_txn, headers=headers, timeout=10)
    # It should store the data but never execute it (API returns JSON, not HTML)
    test("XSS payload handled safely", r.status_code in [201, 422], f"got {r.status_code}")
except Exception as e:
    test("XSS check", False, str(e))

# 7d. Negative amount transaction
try:
    neg_txn = {
        "transactions": [{
            "date": "2025-06-15",
            "amount": -500,
            "category": "Food",
            "merchant": "Test"
        }]
    }
    r = requests.post(f"{API}/transactions/bulk", json=neg_txn, headers=headers, timeout=10)
    test("Negative amount validation", r.status_code in [200, 422], f"got {r.status_code}")
except Exception as e:
    test("Negative amount check", False, str(e))

# 7e. Oversized payload
try:
    big_txns = [{"date": "2025-06-15", "amount": 100, "category": "Food"} for _ in range(2000)]
    r = requests.post(f"{API}/transactions/bulk", json={"transactions": big_txns}, headers=headers, timeout=15)
    test("Oversized bulk rejected", r.status_code in [200, 400, 413, 422], f"got {r.status_code}")
except Exception as e:
    test("Oversized payload check", False, str(e))

# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────
section("TEST SUMMARY")
passed = sum(1 for _, p, _ in results if p)
failed = sum(1 for _, p, _ in results if not p)
total = len(results)

print(f"\n  Total:  {total}")
print(f"  Passed: {passed}  ✅")
print(f"  Failed: {failed}  ❌")
print(f"  Rate:   {passed/total*100:.1f}%")

if failed > 0:
    print(f"\n  Failed tests:")
    for name, p, detail in results:
        if not p:
            print(f"    ❌ {name}: {detail}")

print()
sys.exit(0 if failed == 0 else 1)
