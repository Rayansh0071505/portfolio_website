"""Test if conversation history works"""
import requests
import json

API_URL = "http://23.22.97.151:8080/api/chat"
SESSION_ID = "test_memory_123"

print("="*60)
print("CONVERSATION HISTORY TEST")
print("="*60)

# Message 1: Tell the AI your name
print("\n1. First message: 'My name is Bob'")
response1 = requests.post(API_URL, json={
    "message": "My name is Bob",
    "session_id": SESSION_ID
})
data1 = response1.json()
print(f"Response: {data1['message'][:100]}...")
print(f"Session: {data1['session_id']}")

# Message 2: Ask what your name is
print("\n2. Second message: 'What is my name?'")
response2 = requests.post(API_URL, json={
    "message": "What is my name?",
    "session_id": SESSION_ID  # SAME session
})
data2 = response2.json()
print(f"Response: {data2['message']}")
print(f"Session: {data2['session_id']}")

# Check if it remembered
print("\n" + "="*60)
if "bob" in data2['message'].lower():
    print("✅ CONVERSATION HISTORY WORKS!")
    print("AI remembered the name 'Bob'")
else:
    print("❌ CONVERSATION HISTORY BROKEN!")
    print("AI did NOT remember the name")
print("="*60)
