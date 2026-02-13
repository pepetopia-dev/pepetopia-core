import sys
import os
import json
from dataclasses import asdict
from unittest.mock import MagicMock

# Set dummy env vars to pass Config validation
os.environ["GEMINI_API_KEY"] = "dummy"
os.environ["TELEGRAM_BOT_TOKEN"] = "dummy"
os.environ["TELEGRAM_CHAT_ID"] = "dummy"

# Mock google.genai to avoid ImportError
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = MagicMock()
sys.modules["google.genai.types"] = MagicMock()
sys.modules["dotenv"] = MagicMock()
sys.modules["requests"] = MagicMock()
sys.modules["bs4"] = MagicMock()

# Adjust path to include src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.prompt_builder import PromptBuilder, TweetContext
from src.ai_engine import format_response

def test_prompt_builder():
    print("--- Testing PromptBuilder ---")
    pb = PromptBuilder()
    
    # Test 1: Load Insights
    print(f"Insights loaded (approx length): {len(pb.insights)} chars")
    if len(pb.insights) < 100:
        print("WARNING: Insights seem too short!")
    
    # Test 2: Build System Prompt
    persona = {
        "role": "TEST ROLE",
        "style": "Test Style",
        "directive": "Test Directive"
    }
    sys_prompt = pb.build_system_prompt(persona)
    print("\n[System Prompt Snippet]")
    print(sys_prompt[:200] + "...")
    
    if "JSON OUTPUT STRUCTURE" not in sys_prompt and "Output Format (STRICT JSON)" not in sys_prompt:
         print("FAIL: JSON instructions missing in system prompt.")
    else:
         print("PASS: JSON instructions found.")

    # Test 3: Build User Prompt
    ctx = TweetContext(text="Bitcoin is going to the moon!", author="Satoshi", topic="Crypto", sentiment="Positive")
    user_prompt = pb.build_user_prompt(ctx)
    print("\n[User Prompt]")
    print(user_prompt)

def test_response_parsing():
    print("\n--- Testing Response Parsing (Mock) ---")
    
    mock_json_response = {
        "analysis": {
            "sentiment": "Positive",
            "topic": "Crypto",
            "context_thought": "User is bullish. Align with 'Growth' viral score logic."
        },
        "viral_score": 88,
        "reply_text": "Moon mission confirmed. 🚀 But what's the plan for re-entry? #BTC"
    }
    
    formatted = format_response(mock_json_response, "mock-model-1.0", "brand")
    print("\n[Formatted Output]")
    try:
        print(formatted.encode('ascii', 'ignore').decode('ascii'))
    except Exception as e:
        print(f"Error printing formatted output: {e}")

    
    if "88/100" in formatted and "Moon mission confirmed" in formatted:
        print("PASS: Formatting looks correct.")
    else:
        print("FAIL: Formatted output missing key elements.")

if __name__ == "__main__":
    test_prompt_builder()
    test_response_parsing()
