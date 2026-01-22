#!/usr/bin/env python3
"""Debug script to test a single message and see the error"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Create session
print("Creating session...")
resp = requests.post(f"{BASE_URL}/monica/session")
session_data = resp.json()
session_id = session_data["id"]
print(f"Session ID: {session_id}")
print(f"Stage: {session_data['current_stage']}\n")

# Send a simple message
print("Sending message...")
try:
    resp = requests.post(
        f"{BASE_URL}/monica/chat",
        json={
            "session_id": session_id,
            "text": "Hi, I'm Pavan, BM from India, Stimulus division"
        }
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Reply: {data['reply']}")
        print(f"Advance: {data['advance_stage']}")
    else:
        print(f"Error: {resp.text}")
except Exception as e:
    print(f"Exception: {e}")
