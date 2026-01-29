"""Test Vertex AI Gemini connection"""
import os
import sys
import base64
import tempfile
from dotenv import load_dotenv

# Load .env
load_dotenv('backend/.env')

print("="*60)
print("VERTEX AI GEMINI TEST")
print("="*60)

# Step 1: Check if GOOGLE_KEY exists
google_key = os.getenv('GOOGLE_KEY')
if not google_key:
    print("❌ GOOGLE_KEY not found in .env")
    sys.exit(1)

print(f"✅ GOOGLE_KEY found (length: {len(google_key)} chars)")

# Step 2: Decode and setup credentials
try:
    google_creds_json = base64.b64decode(google_key).decode('utf-8')
    print("✅ GOOGLE_KEY decoded successfully")

    # Parse to get project ID
    import json
    creds_data = json.loads(google_creds_json)
    project_id = creds_data.get('project_id')
    print(f"✅ Project ID: {project_id}")

    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write(google_creds_json)
        temp_creds_path = f.name

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_creds_path
    print(f"✅ Credentials file created: {temp_creds_path}")

except Exception as e:
    print(f"❌ Error decoding GOOGLE_KEY: {e}")
    sys.exit(1)

# Step 3: Test Vertex AI connection
print("\n" + "="*60)
print("Testing Vertex AI Gemini...")
print("="*60)

try:
    from langchain_google_vertexai import ChatVertexAI

    print("Creating ChatVertexAI instance...")
    llm = ChatVertexAI(
        model_name="gemini-2.0-flash-exp",
        project=project_id,
        temperature=0.7,
        max_tokens=100,
        timeout=15,
        max_retries=1,
    )
    print("✅ ChatVertexAI instance created")

    # Send test message
    print("\nSending test message: 'Say hello in one sentence'")
    from langchain_core.messages import HumanMessage

    response = llm.invoke([HumanMessage(content="Say hello in one sentence")])

    print("="*60)
    print("✅ SUCCESS! Vertex AI is working!")
    print("="*60)
    print(f"Response: {response.content}")
    print("="*60)

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Run: pip install langchain-google-vertexai")

except Exception as e:
    print("="*60)
    print("❌ VERTEX AI TEST FAILED")
    print("="*60)
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print("="*60)
    print("\nPossible causes:")
    print("1. Invalid credentials or expired key")
    print("2. Vertex AI API not enabled in Google Cloud")
    print("3. Project doesn't have access to Gemini models")
    print("4. Network/firewall blocking Google Cloud")
    print("5. Billing not enabled on the project")

finally:
    # Cleanup
    if 'temp_creds_path' in locals():
        try:
            os.unlink(temp_creds_path)
            print(f"\n🗑️ Cleaned up temp credentials file")
        except:
            pass
