import sys
import os
import json
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Set dummy env vars for Config
os.environ["GEMINI_API_KEY"] = "dummy_key"
os.environ["TELEGRAM_BOT_TOKEN"] = "dummy_token"
os.environ["TELEGRAM_CHAT_ID"] = "dummy_chat_id"

# Adjust path to include src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Mock ONLY the google.genai library, not our internal wrappers
mock_google = MagicMock()
mock_genai = MagicMock()
sys.modules["google"] = mock_google
sys.modules["google.genai"] = mock_genai
# CRITICAL: Link them so 'from google import genai' gets the configured mock
mock_google.genai = mock_genai

sys.modules["google.genai.types"] = MagicMock()
# We also need to mock dotenv/requests/bs4 if they are imported at top level
sys.modules["dotenv"] = MagicMock()
sys.modules["requests"] = MagicMock()
sys.modules["bs4"] = MagicMock()

# Import REAL modules
from src.prompt_builder import PromptBuilder, TweetContext
from src.ai_engine import analyze_and_draft, format_response, GeminiService

async def test_end_to_end_flow():
    print("\n--- Testing Standalone AI Engine Integration ---")
    
    # Mock the internal client of GeminiService
    # The user's code uses: client = genai.Client(api_key=Config.GEMINI_API_KEY)
    # And then: await client.aio.models.generate_content(...)
    
    # We need to mock genai.Client so that it returns our AsyncMock
    mock_client_instance = MagicMock()
    mock_aio = MagicMock()
    mock_models = MagicMock()
    
    # Setup the async generate_content return value
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "analysis": {
            "sentiment": "Positive",
            "topic": "Crypto",
            "context_thought": "Unit Test Execution"
        },
        "viral_score": 95,
        "reply_text": "Standalone Engine is Operational! 🚀"
    })
    
    mock_generate = AsyncMock(return_value=mock_response)
    mock_models.generate_content = mock_generate
    mock_aio.models = mock_models
    mock_client_instance.aio = mock_aio
    
    # Patch the genai.Client constructor to return our mock
    # sys.modules["google.genai"] is our MagicMock for the module
    # We need to make sure genai.Client returns our mock_client_instance
    sys.modules["google.genai"].Client.return_value = mock_client_instance
    
    # DEBUG: verify the mock structure
    print(f"DEBUG: genai module: {sys.modules['google.genai']}")
    print(f"DEBUG: genai.Client: {sys.modules['google.genai'].Client}")
    print(f"DEBUG: genai.Client(): {sys.modules['google.genai'].Client()}")
    print(f"DEBUG: client.aio: {sys.modules['google.genai'].Client().aio}")
    print(f"DEBUG: client.aio.models.generate_content: {sys.modules['google.genai'].Client().aio.models.generate_content}")
    # Check if awaitable
    is_coroutine = asyncio.iscoroutinefunction(sys.modules['google.genai'].Client().aio.models.generate_content)
    print(f"DEBUG: is generate_content awaitable? {is_coroutine}")

    print("Executing analyze_and_draft...")
    
    # Since analyze_and_draft is now patched to run asyncio.run internally when called synchronously,
    # OR we can call the async internal logic if we could, but let's test the public API.
    # However, we are already in an async function. 
    # analyze_and_draft has this logic:
    # try: loop = asyncio.get_event_loop() ...
    # response_text, model_name = loop.run_until_complete(...)
    
    # Creating a new loop inside an existing loop is problematic.
    # But analyze_and_draft handles the RuntimeError? 
    # Let's try calling it. If it fails due to existing loop, we might need to run it in a thread 
    # to simulate how main.py calls it (asyncio.to_thread).
    
    try:
        response = await asyncio.to_thread(analyze_and_draft, "Test Input")
        print("\n[Engine Output]")
        try:
            print(response.encode('ascii', 'ignore').decode('ascii'))
        except:
            print(response)

        if "Standalone Engine is Operational" in response and "95/100" in response:
            print("PASS: Standalone integration verified.")
        else:
            print("FAIL: Output does not match expected mock.")
            
    except Exception as e:
        print(f"FAIL: Execution error: {e}")

if __name__ == "__main__":
    # Test PromptBuilder (Sync)
    print("--- Testing PromptBuilder ---")
    pb = PromptBuilder()
    if len(pb.insights) > 50: print("PASS: Insights loaded.")
    
    # Test Engine (Async wrapper)
    asyncio.run(test_end_to_end_flow())
