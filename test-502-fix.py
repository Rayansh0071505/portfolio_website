"""Test if message trimming fixes the 502 crash"""
import asyncio
import sys
import os
sys.path.insert(0, 'backend')
os.chdir('backend')

print("="*60)
print("TESTING 502 FIX - Message Trimming")
print("="*60)

async def test():
    from backend.personal_ai import rayansh_ai

    # Initialize
    print("\n1. Initializing AI...")
    await rayansh_ai.initialize()
    print("✅ AI initialized")

    # Same questions that caused 502
    questions = [
        "hi",
        "tell me your tech stack",
        "have you work in voice model",
        "in which company you worked in it",
        "explain your role in everest",
        "have you work in e commerce",
        "what did you work in ooodles",
        "how much experience you have"
    ]

    session_id = "test_502_fix"

    print("\n" + "="*60)
    print("RUNNING 8 QUESTIONS")
    print("="*60)

    for i, question in enumerate(questions, 1):
        print(f"\n{'='*60}")
        print(f"Question {i}: {question}")
        print("="*60)

        try:
            response = await rayansh_ai.chat(question, session_id=session_id)

            # Show response (first 150 chars)
            msg = response['message'][:150]
            print(f"✅ Response: {msg}...")
            print(f"   Time: {response['response_time']} | Model: {response['model']}")

        except Exception as e:
            print(f"❌ CRASHED on question {i}!")
            print(f"   Error: {type(e).__name__}: {str(e)[:100]}")
            return False

    print("\n" + "="*60)
    print("✅ SUCCESS! All 8 questions completed without crash!")
    print("="*60)
    return True

try:
    success = asyncio.run(test())
    if success:
        print("\n✅ Test PASSED - Ready to deploy!")
    else:
        print("\n❌ Test FAILED - Do NOT deploy!")
except Exception as e:
    print(f"\n❌ Test FAILED with error: {e}")
    import traceback
    traceback.print_exc()
