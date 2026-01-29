"""Simple Vertex AI test - provide credentials JSON file directly"""
import os
import sys
import json

print("="*60)
print("SIMPLE VERTEX AI TEST")
print("="*60)

if len(sys.argv) < 2:
    print("\nUsage: python test-vertex-simple.py <credentials.json>")
    print("Example: python test-vertex-simple.py path/to/credentials.json")
    sys.exit(1)

creds_file = sys.argv[1]

try:
    # Step 1: Load credentials
    print(f"\n1. Loading credentials from: {creds_file}")
    with open(creds_file, 'r') as f:
        creds_data = json.load(f)

    project_id = creds_data.get('project_id')
    print(f"   ✅ Project ID: {project_id}")

    # Step 2: Set credentials
    print("\n2. Setting up credentials...")
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_file
    print("   ✅ Credentials set")

    # Step 3: Test Vertex AI
    print("\n3. Testing Vertex AI Gemini...")
    from langchain_google_vertexai import ChatVertexAI
    from langchain_core.messages import HumanMessage

    llm = ChatVertexAI(
        model_name="gemini-2.0-flash-exp",
        project=project_id,
        temperature=0.7,
        max_tokens=50,
        timeout=15,
    )
    print("   ✅ Model initialized")

    # Step 4: Send test message
    print("\n4. Sending test message...")
    response = llm.invoke([HumanMessage(content="Say 'Hello' in one word")])

    print("\n" + "="*60)
    print("✅ SUCCESS! VERTEX AI WORKS!")
    print("="*60)
    print(f"Response: {response.content}")
    print("="*60)
    print("\nYour Google credentials are VALID!")
    print("The issue is just the encoding in .env")
    print("\nNext step: Run fix-google-key.py to re-encode it properly")

except FileNotFoundError:
    print(f"\n❌ File not found: {creds_file}")

except ImportError as e:
    print(f"\n❌ Missing package: {e}")
    print("Run: pip install langchain-google-vertexai")

except Exception as e:
    print("\n" + "="*60)
    print("❌ VERTEX AI TEST FAILED")
    print("="*60)
    print(f"Error: {type(e).__name__}")
    print(f"Message: {str(e)}")
    print("="*60)

    # Common error messages
    if "403" in str(e) or "permission" in str(e).lower():
        print("\nPossible cause: Vertex AI API not enabled")
        print(f"Enable it: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project={project_id}")
    elif "404" in str(e):
        print("\nPossible cause: Model not available in your region")
    elif "billing" in str(e).lower():
        print("\nPossible cause: Billing not enabled on project")
        print(f"Check billing: https://console.cloud.google.com/billing/linkedaccount?project={project_id}")
    elif "quota" in str(e).lower():
        print("\nPossible cause: Quota exceeded")
