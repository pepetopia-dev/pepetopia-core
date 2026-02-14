import sys
import os
import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Mock google.genai BEFORE importing gemini_service
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = MagicMock()
sys.modules["google.genai.types"] = MagicMock()

# Link mocks
mock_genai = sys.modules["google.genai"]
sys.modules["google"].genai = mock_genai

sys.modules["dotenv"] = MagicMock()
sys.modules["src.app_config"] = MagicMock()
# Since we mock app_config, we need to ensure Config.GEMINI_API_KEY exists
sys.modules["src.app_config"].Config.GEMINI_API_KEY = "dummy_key"

from src.gemini_service import GeminiService

class TestGeminiFallback(unittest.IsolatedAsyncioTestCase):
    async def test_fallback_on_429(self):
        print("\nTesting Model Fallback Logic...")
        
        # Setup Mock Client
        mock_client = MagicMock()
        mock_aio = MagicMock()
        mock_models = MagicMock()
        
        # Create an AsyncMock for generate_content
        # We want it to fail first, then succeed
        
        # Side effect can be an iterable of return values/exceptions
        # Call 1 (2.0-flash): Raise 429
        # Call 2 (1.5-flash): Return Success
        
        exception_429 = Exception("429 RESOURCE_EXHAUSTED: Quota exceeded")
        
        mock_response = MagicMock()
        mock_response.text = '{"viral_score": 100, "reply_text": "Success from 1.5-flash"}'
        
        mock_generate = AsyncMock(side_effect=[exception_429, mock_response])
        
        mock_models.generate_content = mock_generate
        mock_aio.models = mock_models
        mock_client.aio = mock_aio
        
        # Mock Client constructor
        mock_genai.Client.return_value = mock_client
        
        # Execute
        response_text, model_name = await GeminiService._generate_with_retry("test prompt", "system prompt")
        
        print(f"Result: Model={model_name}, Response={response_text}")
        
        # Assertions
        self.assertEqual(model_name, "gemini-1.5-flash")
        self.assertIn("Success from 1.5-flash", response_text)
        self.assertEqual(mock_generate.call_count, 2)
        print("✅ Fallback logic verified: Switched from 2.0-flash to 1.5-flash.")

if __name__ == "__main__":
    unittest.main()
