"""
tests/test_api.py
API integration tests for FastAPI support service.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["brand"] == "AmazonHelp"

def test_examples_endpoint(client):
    res = client.get("/api/support/examples")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 5

def test_analyze_tracking_endpoint(client):
    payload = {"message": "Where is my package? Tracking says delayed."}
    res = client.post("/api/support/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "intent" in data
    assert "decision" in data
    assert "action" in data["decision"]
    assert "audit_trail" in data
    assert len(data["audit_trail"]) > 0

def test_analyze_fraud_escalation(client):
    payload = {"message": "Someone stole my card and hacked my Amazon account!"}
    res = client.post("/api/support/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"]["action"] == "ESCALATE"
    assert data["decision"]["reason_code"] in ["HIGH_RISK", "PAYMENT_DISPUTE", "ACCOUNT_SPECIFIC_ACTION"]
