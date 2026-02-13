import sys
import os
import asyncio
import logging

# Configure Logging to console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LiveTest")

# Ensure we can import from src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.ai_engine import analyze_and_draft
from src.app_config import Config

async def test_live_connection():
    print("\n--- 🌍 LIVE CONNECTION TEST (REAL API CALL) ---")
    
    if not Config.GEMINI_API_KEY:
        print("❌ ERROR: GEMINI_API_KEY is missing from environment/Config.")
        print("Please ensure your .env file is set up correctly.")
        return

    print(f"✅ API Key detected: {Config.GEMINI_API_KEY[:4]}...****")
    
    test_input = "Bitcoin is pumping! #BTC to the moon! 🚀"
    print(f"\nSending Input: '{test_input}'")
    
    try:
        # We need to run this in a thread because analyze_and_draft handles the loop logic
        # But wait, analyze_and_draft creates a NEW loop.
        # If we are already in an async function (run by asyncio.run), creating a new loop might crash.
        
        # analyze_and_draft implementation:
        # try: loop = asyncio.get_event_loop() ...
        # response = loop.run_until_complete(...)
        
        # If we call it directly here, it might work if no loop is running in this thread?
        # But asyncio.run(test_live_connection()) starts a loop.
        
        # So we should run analyze_and_draft in a separate thread to be safe, simulating main.py
        response = await asyncio.to_thread(analyze_and_draft, test_input)
        
        print("\n[🤖 AI RESPONSE]")
        try:
            print(response.encode('ascii', 'ignore').decode('ascii'))
        except:
            print(response) # Print raw if unicode fails
            
        if "Viral Score" in response:
            print("\n✅ SUCCESS: Received a structured response with Viral Score.")
        else:
            print("\n⚠️ WARNING: Response format looks unexpected.")
            
    except Exception as e:
        print(f"\n❌ FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_live_connection())
