import sys
import os
from unittest.mock import MagicMock

# Adjust paths
current_dir = os.path.dirname(os.path.abspath(__file__))
core_root = os.path.dirname(current_dir) # pepetopia-core
telegram_bot_root = os.path.join(core_root, 'telegram_bot')
twitter_bot_root = os.path.join(core_root, 'twitter_bot')

# Ensure core_root is in sys.path so we can import packages as expected
if core_root not in sys.path:
    sys.path.insert(0, core_root)

# Mock telegram
sys.modules["telegram"] = MagicMock()
sys.modules["telegram.ext"] = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = MagicMock()
sys.modules["google.genai.types"] = MagicMock()
sys.modules["dotenv"] = MagicMock()
sys.modules["requests"] = MagicMock()
sys.modules["bs4"] = MagicMock()

# Set dummy env vars for AppConfig in twitter_bot
os.environ["GEMINI_API_KEY"] = "dummy"
os.environ["TELEGRAM_BOT_TOKEN"] = "dummy"
os.environ["TELEGRAM_CHAT_ID"] = "dummy"

# Mock GeminiService in sys.modules to simulate successful import
mock_gemini_service = MagicMock()
# _generate_with_retry returns (text, model_name)
async def mock_generate(*args, **kwargs):
    return ('{"analysis": {"context_thought": "Integrated Logic Works"}, "viral_score": 99, "reply_text": "Integration Successful!"}', "central-gemini-pro")

mock_gemini_service.GeminiService._generate_with_retry.side_effect = mock_generate
sys.modules["telegram_bot.src.services.gemini_service"] = mock_gemini_service

print("Attempting to import twitter_bot.src.ai_engine...")
try:
    from twitter_bot.src.ai_engine import analyze_and_draft
    print("Success importing analyze_and_draft.")
    
    print("Testing analyze_and_draft execution with mocked GeminiService...")
    response = analyze_and_draft("Test Tweet input")
    print("\n[Execution Result]")
    try:
        print(response.encode('ascii', 'ignore').decode('ascii'))
    except:
        print(response)

    if "Integrated Logic Works" in response and "central-gemini-pro" in response:
        print("PASS: GeminiService integration confirmed.")
    else:
        print("FAIL: Response did not contain expected mocked values.")

except ImportError as e:
    print(f"FAIL: ImportError: {e}")
except Exception as e:
    print(f"FAIL: Unexpected error: {e}")

