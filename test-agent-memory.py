"""Test if create_agent with checkpointer parameter works (v0.3+ API)"""
import asyncio
import sys
import os
sys.path.insert(0, 'backend')
os.chdir('backend')

from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

print("="*60)
print("TESTING AGENT MEMORY WITH MEMORYSAVER (v0.3+ API)")
print("="*60)

async def test():
    # Initialize LLM
    print("\n1. Initializing Groq LLM...")
    GROQ_API_KEY = ""  # Add your key here for testing

    if not GROQ_API_KEY:
        print("❌ Please add GROQ_API_KEY in the script")
        return

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.7,
        groq_api_key=GROQ_API_KEY,
        timeout=30
    )
    print("✅ LLM initialized")

    # Create agent with checkpointer (v0.3+ API - NO .compile() needed!)
    print("\n2. Creating agent with MemorySaver...")
    memory = MemorySaver()
    agent = create_agent(
        llm,
        tools=[],
        checkpointer=memory,  # ✅ Pass checkpointer directly
        system_prompt="You are a helpful assistant."
    )
    print("✅ Agent created with memory enabled")

    # Test conversation
    config = {"configurable": {"thread_id": "test-123"}}

    print("\n" + "="*60)
    print("CONVERSATION TEST")
    print("="*60)

    # Turn 1
    print("\n👤 User: My name is Alice")
    result1 = await agent.ainvoke(
        {"messages": [HumanMessage(content="My name is Alice")]},
        config
    )
    response1 = result1["messages"][-1].content
    print(f"🤖 AI: {response1}")

    # Turn 2 - Test memory
    print("\n👤 User: What is my name?")
    result2 = await agent.ainvoke(
        {"messages": [HumanMessage(content="What is my name?")]},
        config
    )
    response2 = result2["messages"][-1].content
    print(f"🤖 AI: {response2}")

    # Check if memory works
    print("\n" + "="*60)
    if "alice" in response2.lower():
        print("✅ SUCCESS! MEMORY WORKS!")
        print("Agent remembered the name 'Alice'")
    else:
        print("❌ FAILED! MEMORY NOT WORKING!")
        print("Agent did NOT remember the name")
    print("="*60)

    # Show message history
    state = await agent.aget_state(config)
    print(f"\n📝 Total messages in history: {len(state.values['messages'])}")

try:
    asyncio.run(test())
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}")
    print(f"Message: {str(e)}")
    import traceback
    traceback.print_exc()
