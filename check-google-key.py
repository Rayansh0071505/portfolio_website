"""Check GOOGLE_KEY format in .env"""
import os
from dotenv import load_dotenv

load_dotenv()

google_key = os.getenv('GOOGLE_KEY')

if not google_key:
    print("❌ GOOGLE_KEY not found in .env")
else:
    print(f"GOOGLE_KEY found:")
    print(f"Length: {len(google_key)} characters")
    print(f"First 50 chars: {google_key[:50]}...")
    print(f"Last 50 chars: ...{google_key[-50:]}")
    print(f"\nStarts with quotes? {google_key[0] if google_key else 'N/A'}")
    print(f"Ends with quotes? {google_key[-1] if google_key else 'N/A'}")

    # Check if it's valid base64
    import base64
    try:
        decoded = base64.b64decode(google_key)
        print(f"\n✅ Valid base64! Decoded to {len(decoded)} bytes")
        # Try to decode as UTF-8
        try:
            text = decoded.decode('utf-8')
            print("✅ Valid UTF-8 JSON!")
        except:
            print("❌ Not valid UTF-8 - binary data or corrupted")
    except Exception as e:
        print(f"\n❌ Not valid base64: {e}")
