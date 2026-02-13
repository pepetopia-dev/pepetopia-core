import logging
import re
import json
import asyncio
import sys
import os
from typing import List, Dict, Optional

# Add path for centralized GeminiService
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
try:
    from telegram_bot.src.services.gemini_service import GeminiService
except ImportError:
    # Fallback/Mock for testing when not in full env
    logging.warning("Failed to import GeminiService. Ensure telegram_bot is in path.")
    GeminiService = None

from .app_config import Config
from .utils import extract_url_content
from .prompt_builder import PromptBuilder, TweetContext

# Configure module-level logger
logger = logging.getLogger(__name__)

class PersonaManager:
    """
    Manages the tone and stylistic constraints for different bot personas.
    """
    PERSONAS = {
        "dev": {
            "role": "SENIOR SOFTWARE ARCHITECT (@pepetopia_dev)",
            "style": "Technical, terse, authoritative, code-centric. Uses jargon correctly.",
            "directive": "Focus on implementation details, performance metrics, and architectural implications."
        },
        "brand": {
            "role": "ECOSYSTEM VISIONARY (@pepetopia)",
            "style": "Inspiring, high-status, community-focused, forward-looking.",
            "directive": "Focus on the big picture, market impact, and community growth."
        }
    }

    @staticmethod
    def get_persona(input_text: str) -> tuple[str, dict]:
        if "@pepetopia_dev" in input_text.lower():
            return "dev", PersonaManager.PERSONAS["dev"]
        return "brand", PersonaManager.PERSONAS["brand"]

def analyze_and_draft(user_input: str) -> str:
    """
    Main orchestrator function.
    """
    persona_key, persona_data = PersonaManager.get_persona(user_input)
    
    clean_input = re.sub(r'@pepetopia(_dev)?', '', user_input, flags=re.IGNORECASE).strip()
    enriched_context = extract_url_content(clean_input) or clean_input

    # Prepare Context
    tweet_context = TweetContext(
        text=enriched_context,
        author="Unknown User", 
        topic=None, 
        sentiment=None 
    )
    
    # helper to clean simple markdown code blocks if LLM outputs them despite strict JSON
    def clean_json_string(s: str) -> str:
        s = s.strip()
        if s.startswith("```json"):
            s = s[7:]
        if s.startswith("```"):
            s = s[3:]
        if s.endswith("```"):
            s = s[:-3]
        return s.strip()

    prompt_builder = PromptBuilder()
    system_instruction = prompt_builder.build_system_prompt(persona_data)
    user_prompt = prompt_builder.build_user_prompt(tweet_context)

    # Use Centralized GeminiService
    if GeminiService:
        # Since analyze_and_draft is ostensibly sync in this signature (based on previous code),
        # but GeminiService is async, we need to run it.
        # HOWEVER, the calling code in ai_chat.py now calls it via await asyncio.to_thread.
        # But wait, asyncio.to_thread runs a sync function in a thread. 
        # Inside that sync function, we can't easily await... unless we create a new event loop or run_until_complete?
        # NO. The calling code `ai_chat.py` does: `ai_response = await asyncio.to_thread(analyze_and_draft, cleaned_text)`
        # This implies `analyze_and_draft` MUST BE SYNCHRONOUS.
        # But `GeminiService._generate_with_retry` is ASYNC.
        
        # FIX: We should use `asyncio.run()` or similar if we are in a thread?
        # OR better: make `analyze_and_draft` async?
        # But if I make it async, `ai_chat.py` calling `asyncio.to_thread(analyze_and_draft...)` will return a coroutine, not result.
        
        # User requested: "update analyze_and_draft ... use GeminiService"
        # Strategy: 
        # Option 1: Convert `analyze_and_draft` to async. Update `ai_chat.py` to just `await analyze_and_draft(...)`.
        # Option 2: Keep `analyze_and_draft` sync and use `asyncio.run()` inside it.
        
        # Given `ai_chat.py` is under my control and I just updated it, Option 1 is cleaner.
        # BUT `ai_chat.py` is ALREADY updated to use `await asyncio.to_thread(analyze_and_draft, cleaned_text)`.
        # If I change `analyze_and_draft` to async, I must update `ai_chat.py` to `await analyze_and_draft(...)` directly.
        # The user said "Update Twitter Bot Engine".
        
        # Let's try to make `analyze_and_draft` synchronous wrapper around async call for now because I can't easily change `ai_chat.py` in the same step easily (different file).
        # Actually I can update `ai_chat.py` in next step if needed. 
        # But `asyncio.run()` might fail if there is already a loop?
        # `asyncio.to_thread` runs in a separate thread. `asyncio.run` creates a new loop. This should work in a thread.
        
        try:
            # We are likely running in a thread (via ai_chat.py).
            # So we need a loop.
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response_text, model_name = loop.run_until_complete(
                GeminiService._generate_with_retry(
                    prompt=user_prompt,
                    system_instruction=system_instruction
                )
            )
            loop.close()
            
            result_text = clean_json_string(response_text)
            try:
                result_json = json.loads(result_text)
                return format_response(result_json, model_name, persona_key)
            except json.JSONDecodeError:
                logger.error(f"JSON Decode Error. Raw: {result_text}")
                return f"⚠️ JSON Error from {model_name}. Raw: {result_text}"

        except Exception as e:
            logger.error(f"GeminiService call failed: {e}")
            return f"⚠️ Engine Error: {e}"
    else:
        return "🚫 Service Integration Error: GeminiService not found."

def format_response(data: dict, model_name: str, persona_key: str) -> str:
    """
    Formats the JSON response into a human-readable/Telegram-ready string.
    """
    header_icon = "👨‍💻" if persona_key == "dev" else "🔮"
    header_title = "ARCHITECT OUTPUT" if persona_key == "dev" else "VISIONARY OUTPUT"
    
    analysis = data.get('analysis', {})
    viral_score = data.get('viral_score', 0)
    reply_text = data.get('reply_text', "No reply generated.")
    
    # Viral Score Icon
    score_icon = "🔴"
    if viral_score >= 90: score_icon = "🔥"
    elif viral_score >= 75: score_icon = "🟢"
    elif viral_score >= 50: score_icon = "🟡"

    output = [f"{header_icon} *{header_title}*"]
    output.append(f"_{analysis.get('context_thought', 'Analysis complete.')}_")
    output.append(f"📊 Viral Score: {score_icon} {viral_score}/100")
    output.append("")
    output.append("*Draft Reply:*")
    output.append(f"`{reply_text}`")
    output.append("")
    output.append(f"⚙️ _Engine: {model_name}_")
    
    return "\n".join(output)