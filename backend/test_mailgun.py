"""
Test Mailgun Email Configuration
Run this to verify your Mailgun setup before using the conversation tracker
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_mailgun():
    """Test Mailgun API with a simple email"""

    print("\n" + "="*60)
    print("🧪 TESTING MAILGUN CONFIGURATION")
    print("="*60 + "\n")

    # Get credentials
    mailgun_domain = os.getenv("MAILGUN_DOMAIN")
    mailgun_api_key = os.getenv("MAILGUN_SECRET")

    # Validate credentials
    print("1️⃣ Checking environment variables...")
    if not mailgun_api_key:
        print("❌ MAILGUN_SECRET not found in .env file")
        print("   Add: MAILGUN_SECRET=your_api_key_here")
        return False

    if not mailgun_domain:
        print("❌ MAILGUN_DOMAIN not found in .env file")
        print("   Add: MAILGUN_DOMAIN=your_domain.mailgun.org")
        return False

    print(f"✅ MAILGUN_DOMAIN: {mailgun_domain}")
    print(f"✅ MAILGUN_SECRET: {mailgun_api_key[:15]}..." + ("*" * 20))

    # Prepare test email
    print("\n2️⃣ Preparing test email...")

    api_endpoint = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"
    print(f"   Endpoint: {api_endpoint}")

    test_subject = "🧪 Mailgun Test - Portfolio AI Chat"
    test_html = """
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #3b82f6;">✅ Mailgun Configuration Successful!</h2>
        <p>This is a test email from your portfolio AI chat system.</p>
        <p><strong>Setup Status:</strong> Working correctly</p>
        <p style="color: #64748b; font-size: 14px; margin-top: 30px;">
            You can now receive conversation summaries from your AI assistant.
        </p>
    </body>
    </html>
    """

    test_text = """
    ✅ MAILGUN TEST EMAIL
    =====================

    This is a test email from your portfolio AI chat system.

    Setup Status: Working correctly

    You can now receive conversation summaries from your AI assistant.
    """

    # Send test email
    print("\n3️⃣ Sending test email...")
    print(f"   To: rayanshsrivastava.ai@gmail.com")

    try:
        response = requests.post(
            api_endpoint,
            auth=("api", mailgun_api_key),
            data={
                "from": f"Rayansh AI Test <noreply@{mailgun_domain}>",
                "to": ["rayanshsrivastava.ai@gmail.com"],
                "subject": test_subject,
                "text": test_text,
                "html": test_html,
            },
            timeout=15
        )

        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()
            message_id = response_data.get("id", "unknown")
            message_text = response_data.get("message", "")

            print("\n" + "="*60)
            print("✅ SUCCESS!")
            print("="*60)
            print(f"Message ID: {message_id}")
            print(f"Response: {message_text}")
            print("\n📬 Check your email: rayanshsrivastava.ai@gmail.com")
            print("   (May take 1-2 minutes to arrive)")
            print("\n💡 Note: If using sandbox domain, make sure")
            print("   rayanshsrivastava.ai@gmail.com is verified as")
            print("   an authorized recipient in Mailgun dashboard!")
            print("="*60 + "\n")
            return True

        else:
            print("\n" + "="*60)
            print("❌ FAILED")
            print("="*60)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")

            if response.status_code == 401:
                print("\n💡 Possible issue: Invalid API key")
                print("   Check MAILGUN_SECRET in .env file")
            elif response.status_code == 400:
                print("\n💡 Possible issue: Bad request")
                print("   Check MAILGUN_DOMAIN is correct")
            elif response.status_code == 403:
                print("\n💡 Possible issue: Forbidden")
                print("   For sandbox domains, verify recipient email:")
                print("   1. Go to Mailgun Dashboard")
                print("   2. Sending → Domain Settings → Authorized Recipients")
                print("   3. Add rayanshsrivastava.ai@gmail.com")
                print("   4. Check Gmail and verify the authorization link")

            print("="*60 + "\n")
            return False

    except requests.exceptions.Timeout:
        print("\n❌ Request timed out")
        print("   Check your internet connection")
        return False

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Network error: {str(e)}")
        return False

    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_mailgun()

    if success:
        print("\n🎉 Mailgun is configured correctly!")
        print("Your conversation tracker is ready to use.")
    else:
        print("\n⚠️  Please fix the issues above before using conversation tracker.")
        print("\nFor help, see:")
        print("- CONVERSATION_TRACKING.md")
        print("- https://documentation.mailgun.com/docs/mailgun/get-started")
