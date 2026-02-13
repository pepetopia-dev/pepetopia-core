import logging
import re
import json
import asyncio
from typing import Dict, Optional

# --- DÜZELTME: Doğrudan aynı klasörden import ediyoruz ---
try:
    from .gemini_service import GeminiService
except ImportError as e:
    # Hata durumunda log basalım ama kodun çökmesini engelleyelim
    logging.error(f"CRITICAL: Could not import GeminiService. Error: {e}")
    GeminiService = None

from .app_config import Config
from .utils import extract_url_content
from .prompt_builder import PromptBuilder, TweetContext

# Logger yapılandırması
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
    # Servis kontrolü
    if not GeminiService:
        return "🚫 **System Error:** GeminiService module is missing or failed to load."

    persona_key, persona_data = PersonaManager.get_persona(user_input)
    
    # Kullanıcı adını temizle ve link varsa içeriğini çek
    clean_input = re.sub(r'@pepetopia(_dev)?', '', user_input, flags=re.IGNORECASE).strip()
    enriched_context = extract_url_content(clean_input) or clean_input

    # Context hazırla
    tweet_context = TweetContext(
        text=enriched_context,
        author="Unknown User", 
        topic=None, 
        sentiment=None 
    )
    
    # JSON temizleme yardımcısı
    def clean_json_string(s: str) -> str:
        s = s.strip()
        if s.startswith("```json"): s = s[7:]
        elif s.startswith("```"): s = s[3:]
        if s.endswith("```"): s = s[:-3]
        return s.strip()

    prompt_builder = PromptBuilder()
    system_instruction = prompt_builder.build_system_prompt(persona_data)
    user_prompt = prompt_builder.build_user_prompt(tweet_context)

    try:
        # Senkron fonksiyonda asenkron kodu çalıştırma yaması (Patch)
        # Main.py'de thread içinde çağrıldığı için yeni bir event loop gerekebilir.
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Gemini servisini çağır
        response_text, model_name = loop.run_until_complete(
            GeminiService._generate_with_retry(
                prompt=user_prompt,
                system_instruction=system_instruction
            )
        )
        
        # Sonucu işle
        result_text = clean_json_string(response_text)
        try:
            result_json = json.loads(result_text)
            return format_response(result_json, model_name, persona_key)
        except json.JSONDecodeError:
            logger.error(f"JSON Decode Error. Raw: {result_text}")
            return f"⚠️ JSON Error from {model_name}. Raw response was invalid."

    except Exception as e:
        logger.error(f"GeminiService call failed: {e}")
        return f"⚠️ Engine Error: {e}"

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