"""Test Vertex AI using GOOGLE_KEY from .env"""
import os
import sys
import base64
import tempfile
import json
from dotenv import load_dotenv

print("="*60)
print("VERTEX AI TEST (from .env GOOGLE_KEY)")
print("="*60)

# Load .env
load_dotenv('backend/.env')

google_key = os.getenv('GOOGLE_KEY')
if not google_key:
    print("❌ GOOGLE_KEY not found in backend/.env")
    sys.exit(1)

print(f"✅ GOOGLE_KEY found ({len(google_key)} chars)")

# Try to decode
print("\nAttempting to decode GOOGLE_KEY...")
try:
    decoded = base64.b64decode(google_key)
    print(f"✅ Base64 decoded ({len(decoded)} bytes)")

    # Try UTF-8 first
    try:
        creds_json = decoded.decode('utf-8')
        print("✅ Decoded as UTF-8")
    except UnicodeDecodeError:
        # Try other encodings
        print("⚠️  UTF-8 failed, trying latin-1...")
        creds_json = decoded.decode('latin-1')
        print("✅ Decoded as latin-1")

    # Parse JSON
    creds_data = json.loads(creds_json)
    project_id = creds_data.get('project_id')
    print(f"✅ Valid JSON! Project: {project_id}")

    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write(creds_json)
        temp_file = f.name

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_file
    print(f"✅ Credentials saved to temp file")

    # Test Vertex AI
    print("\n" + "="*60)
    print("Testing Vertex AI Gemini Model...")
    print("="*60)

    from langchain_google_vertexai import ChatVertexAI
    from langchain_core.messages import HumanMessage

    llm = ChatVertexAI(
        model_name="gemini-2.0-flash-exp",
        project=project_id,
        temperature=0.7,
        max_tokens=50,
        timeout=20,
    )
    print("✅ Model initialized")

    print("\nSending test message: 'Say hello'")
    response = llm.invoke([HumanMessage(content="Say hello in one sentence")])

    print("\n" + "="*60)
    print("✅ SUCCESS! VERTEX AI WORKS!")
    print("="*60)
    print(f"Response: {response.content}")
    print("="*60)

    # Cleanup
    os.unlink(temp_file)

except json.JSONDecodeError as e:
    print(f"\n❌ Invalid JSON after decoding: {e}")
    print("\nThe GOOGLE_KEY is corrupted!")
    print("You need to re-encode your credentials.json file")
    print("Run: python fix-google-key.py credentials.json")

except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}")
    print(f"Message: {str(e)}")

    if "403" in str(e):
        print("\n⚠️  Vertex AI API not enabled!")
        print(f"Enable: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com")
    elif "billing" in str(e).lower():
        print("\n⚠️  Billing not enabled!")
    elif "quota" in str(e).lower():
        print("\n⚠️  Quota exceeded!")

    # Cleanup
    if 'temp_file' in locals():
        try:
            os.unlink(temp_file)
        except:
            pass
