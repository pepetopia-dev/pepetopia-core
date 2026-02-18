import logging
import re
import json
from typing import Dict, Tuple

# Import services
from .gemini_service import GeminiService
from .app_config import Config
from .utils import extract_url_content
from .prompt_builder import PromptBuilder, TweetContext

# Logger configuration
logger = logging.getLogger(__name__)

class PersonaManager:
    """
    Manages the tone and stylistic constraints for different bot personas.
    """
    PERSONAS = {
        "dev": {
            "role": "SENIOR SOFTWARE ARCHITECT (@pepetopia_dev)",
            "style": "Technical, terse, authoritative, code-centric. Uses jargon (Rust, Solana, TPS) correctly. Skeptical optimization focus.",
            "directive": "Focus on implementation details, security, and architectural implications."
        },
        "brand": {
            "role": "ECOSYSTEM VISIONARY (@pepetopia)",
            "style": "Inspiring, high-status, community-focused, forward-looking. Uses emoji sparingly but effectively.",
            "directive": "Focus on the big picture, market impact, and community growth."
        }
    }

    @staticmethod
    def get_persona(input_text: str) -> Tuple[str, dict]:
        # Check for the specific trigger handle
        if "@pepetopia_dev" in input_text.lower():
            return "dev", PersonaManager.PERSONAS["dev"]
        return "brand", PersonaManager.PERSONAS["brand"]

def clean_json_string(s: str) -> str:
    """Helper to clean markdown code blocks from LLM response."""
    s = s.strip()
    if s.startswith("```json"): s = s[7:]
    elif s.startswith("```"): s = s[3:]
    if s.endswith("```"): s = s[:-3]
    return s.strip()

async def analyze_and_draft(user_input: str) -> str:
    """
    Main orchestrator function (Async).
    """
    # Service check
    # Note: We assume GeminiService is available. If imports fail, this will crash early (good for debugging).
    
    # 1. Determine Persona
    persona_key, persona_data = PersonaManager.get_persona(user_input)
    
    # 2. Pre-process Input (Remove trigger, fetch URL content)
    clean_input = re.sub(r'@pepetopia(_dev)?', '', user_input, flags=re.IGNORECASE).strip()
    enriched_context = extract_url_content(clean_input) or clean_input

    # 3. Build Context
    tweet_context = TweetContext(
        text=enriched_context,
        author="User", 
        topic=None, 
        sentiment=None 
    )
    
    # 4. Build Prompts
    prompt_builder = PromptBuilder()
    system_instruction = prompt_builder.build_system_prompt(persona_data)
    user_prompt = prompt_builder.build_user_prompt(tweet_context)

    try:
        # 5. Call LLM (Async)
        # We await directly here, removing the need for internal event loops.
        response_text, model_name = await GeminiService._generate_with_retry(
            prompt=user_prompt,
            system_instruction=system_instruction
        )
        
        # 6. Parse and Format
        result_text = clean_json_string(response_text)
        try:
            result_json = json.loads(result_text)
            return format_response_html(result_json, model_name, persona_key)
        except json.JSONDecodeError:
            logger.error(f"JSON Decode Error. Raw: {result_text}")
            return f"⚠️ <b>JSON Hatası:</b> Model geçersiz format üretti.<br>Model: {model_name}"

    except Exception as e:
        logger.error(f"Engine Error: {e}")
        return f"⚠️ <b>Kritik Hata:</b> {str(e)}"

def format_response_html(data: dict, model_name: str, persona_key: str) -> str:
    """
    Formats the JSON response into Telegram-friendly HTML.
    Supports 3 distinct reply options.
    """
    # Header Icons & Titles
    if persona_key == "dev":
        header = "👨‍💻 <b>MÜHENDİS MODU</b>"
    else:
        header = "🔮 <b>VİZYONER (CEO) MODU</b>"
    
    analysis = data.get('analysis', {})
    viral_score = data.get('viral_score', 0)
    replies = data.get('replies', [])
    
    # Viral Score Indicator
    if viral_score >= 90: score_icon = "🔥"
    elif viral_score >= 75: score_icon = "🟢"
    elif viral_score >= 50: score_icon = "🟡"
    else: score_icon = "🔴"

    # Build HTML Output
    output = []
    output.append(header)
    output.append(f"📊 <b>Viral Puanı:</b> {score_icon} {viral_score}/100")
    output.append(f"💡 <i>{analysis.get('context_thought', 'Analiz tamamlandı.')}</i>")
    output.append("") # Spacer
    
    output.append("<b>📝 TASLAK CEVAPLAR (İngilizce):</b>")
    output.append("")
    
    # Loop through the 3 replies
    if isinstance(replies, list):
        for i, reply in enumerate(replies, 1):
            r_type = reply.get('type', f'Option {i}')
            r_text = reply.get('text', 'No text generated.')
            
            output.append(f"<b>{i}. {r_type}</b>")
            # Using <code> tag for easy copy-pasting in Telegram
            output.append(f"<code>{r_text}</code>")
            output.append("") # Spacer
    else:
        # Fallback for old/wrong format
        output.append(f"<code>{data.get('reply_text', 'Error parsing replies.')}</code>")

    output.append(f"⚙️ <span class='tg-spoiler'>Model: {model_name}</span>")
    
    return "\n".join(output)