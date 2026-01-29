"""Re-encode Google credentials JSON properly"""
import base64
import json
import sys

print("="*60)
print("GOOGLE CREDENTIALS ENCODER")
print("="*60)

if len(sys.argv) < 2:
    print("\nUsage: python fix-google-key.py <path-to-credentials.json>")
    print("Example: python fix-google-key.py credentials.json")
    sys.exit(1)

json_file = sys.argv[1]

try:
    # Read JSON file
    print(f"\n1. Reading file: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        json_content = f.read()

    # Validate it's valid JSON
    print("2. Validating JSON...")
    json_data = json.loads(json_content)
    project_id = json_data.get('project_id', 'unknown')
    print(f"   ✅ Valid JSON (project: {project_id})")

    # Encode to base64
    print("3. Encoding to base64...")
    base64_encoded = base64.b64encode(json_content.encode('utf-8')).decode('utf-8')

    # Verify it decodes correctly
    print("4. Verifying encoding...")
    test_decode = base64.b64decode(base64_encoded).decode('utf-8')
    json.loads(test_decode)  # Verify it's still valid JSON
    print("   ✅ Encoding verified!")

    # Output
    print("\n" + "="*60)
    print("✅ SUCCESS! Copy this value:")
    print("="*60)
    print(base64_encoded)
    print("="*60)

    print(f"\nLength: {len(base64_encoded)} characters")
    print("\nPaste this into backend/.env:")
    print(f'GOOGLE_KEY="{base64_encoded}"')

    # Save to file
    with open('google_key_base64.txt', 'w') as f:
        f.write(base64_encoded)
    print("\n✅ Also saved to: google_key_base64.txt")

except FileNotFoundError:
    print(f"\n❌ Error: File '{json_file}' not found!")
except json.JSONDecodeError as e:
    print(f"\n❌ Error: Invalid JSON file!")
    print(f"   {e}")
except Exception as e:
    print(f"\n❌ Error: {e}")
