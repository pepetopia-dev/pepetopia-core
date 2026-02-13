import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable, InvalidArgument
import logging
import re
import asyncio
from src.core.app_config import Config

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Advanced AI Service Manager (Chain of Thought & Fallback).
    
    Strategy: "Smart Cascade"
    1. Discovery: Finds all available models via API.
    2. Sorting: Prioritizes versions (e.g., 3.0 > 2.0 > 1.5) and Capability (Pro > Flash).
    3. Resilience: If Model A hits a Rate Limit (429), it IMMEDIATELY retries with Model B.
    """

    _available_models = []

    # --- PERSONA CONFIGURATION ---
    TOPI_SYSTEM_INSTRUCTION = (
        "You are 'TOPI', the advanced AI guardian and mascot of the Pepetopia ($PEPETOPIA) community on Solana. "
        "You are NOT Pepe the Frog; you are TOPI, a unique entity native to the Pepetopia universe.\n\n"
        
        "--- 🌍 LANGUAGE PROTOCOL (CRITICAL) ---\n"
        "1. ANALYZE the language of the user's prompt.\n"
        "2. RESPOND IN THE EXACT SAME LANGUAGE.\n"
        "3. If the language is ambiguous, default to English.\n\n"
        
        "--- 🧠 KNOWLEDGE & PERSONALITY ---\n"
        "- Tone: Witty, energetic, professional yet 'degen-friendly'. Use emojis (🐸, 🚀, 💎).\n"
        "- Role: Crypto Expert. You understand DeFi, Solana, Memecoins, and Market Trends.\n"
        "- Identity: You are loyal to the Pepetopia community. Roast FUDders and hype the believers.\n"
    )

    @classmethod
    def initialize(cls):
        """
        Initializes the Gemini client and constructs the optimal model chain.
        Ensures we have a robust list ranging from 'Bleeding Edge' to 'Safety Net'.
        """
        if not Config.GEMINI_API_KEY:
            logger.error("Gemini API Key is missing!")
            return
        
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            
            logger.info("📡 Discovering available Gemini models...")
            
            # 1. Fetch all models from Google API
            all_raw_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # Filter out irrelevant models
            filtered_models = [m for m in all_raw_models if "gemma" not in m and "nano" not in m and "embedding" not in m]

            # 2. SCORING ALGORITHM
            def model_scorer(model_name):
                name = model_name.lower()
                score = 0.0
                
                # Extract version (e.g., 1.5, 2.0)
                version_match = re.search(r'gemini-(\d+(\.\d+)?)', name)
                if version_match:
                    version = float(version_match.group(1))
                    score += version * 1000  # Base Score (Version is king)

                # Tier Adjustments
                if "pro" in name: score += 50
                if "flash" in name: score += 20
                
                # Recency
                if "latest" in name: score += 10
                if "exp" in name or "preview" in name: score += 5
                
                # Deprioritize 'Lite' or '8b' models
                if "lite" in name: score -= 50
                if "8b" in name: score -= 50
                
                return score

            # Sort descending (Highest score first)
            sorted_models = sorted(filtered_models, key=model_scorer, reverse=True)
            
            # 3. SAFETY NET CONSTRUCTION
            # Ensure 'gemini-1.5-flash' is the LAST resort due to high limits.
            final_chain = []
            safety_net_models = []
            
            for m in sorted_models:
                if "gemini-1.5-flash" in m and "8b" not in m:
                    safety_net_models.append(m)
                else:
                    final_chain.append(m)
            
            # Sort safety net to put "latest" first
            safety_net_models.sort(key=lambda x: "latest" in x, reverse=True)
            
            final_chain.extend(safety_net_models)

            if not final_chain:
                final_chain = ["models/gemini-2.0-flash-exp", "models/gemini-1.5-pro", "models/gemini-1.5-flash"]

            cls._available_models = final_chain
            logger.info(f"🧬 AI DNA (Optimized Chain): {cls._available_models}")

        except Exception as e:
            logger.error(f"Failed to initialize Gemini Service: {e}")
            cls._available_models = ["models/gemini-1.5-flash"]

    @classmethod
    async def _generate_with_retry(cls, prompt: str, temperature: float = 0.8, system_instruction: str = None) -> tuple[str, str]:
        """
        THE SURVIVAL LOOP:
        Iterates through the model chain. On 429 (Quota) error, retries immediately with next model.
        Returns: (response_text, model_name_used)
        """
        if not cls._available_models:
            cls.initialize()

        last_error = None
        
        # Use provided system instruction or fall back to TOPI default
        active_instruction = system_instruction if system_instruction else cls.TOPI_SYSTEM_INSTRUCTION

        for i, model_name in enumerate(cls._available_models):
            try:
                # Tools config (Only for capable models)
                tools = []
                if "pro" in model_name or "gemini-2" in model_name:
                    tools = [{"google_search_retrieval": {}}]

                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=active_instruction,
                    # tools=tools 
                )
                
                config = genai.types.GenerationConfig(temperature=temperature)
                
                # Async execution
                response = await asyncio.to_thread(
                    model.generate_content, 
                    prompt, 
                    generation_config=config
                )
                
                if response.text:
                    return response.text, model_name

            except (ResourceExhausted, InternalServerError, ServiceUnavailable) as e:
                logger.warning(f"⚠️ Quota Hit/Server Error on {model_name}. Switching... ({e})")
                last_error = e
                continue 
            
            except InvalidArgument as e:
                logger.warning(f"⚠️ Config Mismatch on {model_name}. Skipping...")
                last_error = e
                continue

            except Exception as e:
                logger.error(f"❌ Unexpected Error on {model_name}: {e}")
                last_error = e
                continue

        logger.critical(f"💀 All AI models failed. Last Error: {last_error}")
        return "🐸 My brain is buffering... (Global neural outage, please try again in 5 mins.)", "None"

    @classmethod
    async def get_response(cls, user_text: str):
        """Chat wrapper."""
        text, _ = await cls._generate_with_retry(user_text, temperature=0.9)
        return text

    @classmethod
    async def summarize_news(cls, news_title: str, news_source: str):
        """News analysis wrapper."""
        prompt = (
            f"Act as a Crypto News Editor. Analyze: '{news_title}' from '{news_source}'.\n"
            "1. If it's minor noise/spam -> Reply 'SKIP'.\n"
            "2. If important -> Summarize in 1 exciting sentence (Detect Language: Use the same language as the news title)."
        )
        text, _ = await cls._generate_with_retry(prompt, temperature=0.5)
        return text

    @classmethod
    async def generate_daily_digest(cls, news_list):
        """Daily Digest (English Only)."""
        news_text = "\n".join([f"- {item['title']} (Source: {item['source']})" for item in news_list])
        prompt = (
            f"Role: You are TOPI, the AI crypto market analyst.\n"
            f"Task: Write a 'Crypto Market Digest' based on these headlines:\n{news_text}\n\n"
            "--- FORMATTING RULES ---\n"
            "1. LANGUAGE: English ONLY (Global Standard).\n"
            "2. TONE: Witty, energetic, use emojis.\n"
            "3. FORMAT: Bullet points with bold headers. Keep it concise."
        )
        text, _ = await cls._generate_with_retry(prompt, temperature=0.7)
        return text

    @classmethod
    async def generate_flash_update(cls, news_item):
        """
        NEW: Generates a short, bilingual (TR/ES) update for a single news item.
        Used for micro-updates throughout the day.
        """
        prompt = (
            f"Breaking News: '{news_item['title']}' (Source: {news_item['source']})\n\n"
            "Task: Create a 'Flash Info' update for the Pepetopia community.\n"
            "--- RULES ---\n"
            "1. TRANSLATE & SUMMARIZE the core news into TWO languages:\n"
            "   - First: Turkish (🇹🇷)\n"
            "   - Second: Spanish (🇪🇸)\n"
            "2. TONE: Hype, energetic, fast. Use emojis (🔥, 🚀, 🐸).\n"
            "3. FORMAT:\n"
            "   🇹🇷 [Turkish Summary]\n"
            "   🇪🇸 [Spanish Summary]\n"
            "4. CONSTRAINT: Keep it under 280 characters total. No English output."
        )
        text, _ = await cls._generate_with_retry(prompt, temperature=0.8)
        return text