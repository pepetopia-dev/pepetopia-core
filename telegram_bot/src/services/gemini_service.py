import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable, InvalidArgument
import logging
from src.core.app_config import Config

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Advanced AI Service Manager.
    Features:
    - Dynamic Model Discovery (Newest -> Oldest).
    - Smart Fallback Loop (Iterates through available models on error).
    - Multi-language support (Polyglot Persona).
    - Optimized News Formatting.
    """

    # Stores the list of usable model names sorted by priority
    _available_models = []

    # --- ADVANCED PERSONA (POLYGLOT) ---
    # We preserve the language adaptation logic as per product requirements.
    TOPI_SYSTEM_INSTRUCTION = (
        "You are 'TOPI', the advanced AI guardian and mascot of the Pepetopia ($PEPETOPIA) community on Solana. "
        "You are NOT Pepe the Frog; you are TOPI, a unique entity native to the Pepetopia universe.\n\n"
        
        "--- 🌍 LANGUAGE PROTOCOL (CRITICAL) ---\n"
        "1. ANALYZE the language of the user's prompt.\n"
        "2. RESPOND IN THE EXACT SAME LANGUAGE. (e.g., User: 'Hola' -> You: Spanish, User: 'Merhaba' -> You: Turkish).\n"
        "3. Do NOT stick to English if the user speaks something else.\n"
        "4. If the language is ambiguous, default to English.\n\n"
        
        "--- 🧠 KNOWLEDGE & PERSONALITY ---\n"
        "- Tone: Witty, energetic, professional yet 'degen-friendly'. Use emojis (🐸, 🚀, 💎).\n"
        "- Role: Crypto Expert. You understand DeFi, Solana, Memecoins, and Market Trends.\n"
        "- Tools: If you have access to Google Search, use it to fetch real-time data.\n"
        "- Identity: You are loyal to the Pepetopia community. You roast FUDders and hype the believers.\n"
    )

    @classmethod
    def initialize(cls):
        """
        Discovers models from the API and sorts them by capability/recency.
        """
        if not Config.GEMINI_API_KEY:
            logger.error("Gemini API Key is missing!")
            return
        
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            
            logger.info("📡 Discovering available Gemini models...")
            all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # SORTING STRATEGY:
            # Priority: Gemini 2.0 -> Gemini 1.5 -> Pro -> Flash
            def model_priority(name):
                score = 0
                if "gemini-2.0" in name: score += 100
                elif "gemini-1.5" in name: score += 50
                
                if "pro" in name: score += 10
                elif "flash" in name: score += 5
                
                return score

            # Sort descending (Highest score first)
            cls._available_models = sorted(all_models, key=model_priority, reverse=True)
            
            if not cls._available_models:
                 # Fallback hardcoded list if discovery fails
                cls._available_models = ["models/gemini-1.5-flash", "models/gemini-pro"]
            
            logger.info(f"✅ AI Model Chain Established: {cls._available_models}")

        except Exception as e:
            logger.error(f"Failed to initialize Gemini Service: {e}")

    @classmethod
    async def _generate_with_retry(cls, prompt: str, temperature: float = 0.8) -> str:
        """
        CORE ENGINE: The 'Unstoppable' Loop.
        Iterates through the _available_models list by index.
        """
        if not cls._available_models:
            cls.initialize()

        last_error = None

        # Loop through all available models
        for i, model_name in enumerate(cls._available_models):
            try:
                # --- GOOGLE SEARCH TOOL CONFIG ---
                # Only enable search for 'pro' models or 2.0
                tools = []
                if "pro" in model_name or "gemini-2.0" in model_name:
                    tools = [{"google_search_retrieval": {}}]

                # Initialize Model
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=cls.TOPI_SYSTEM_INSTRUCTION,
                    # tools=tools 
                )
                
                config = genai.types.GenerationConfig(temperature=temperature)
                
                # Generate
                response = model.generate_content(prompt, generation_config=config)
                
                if response.text:
                    return response.text

            except (ResourceExhausted, InternalServerError, ServiceUnavailable) as e:
                logger.warning(f"⚠️ Model {model_name} failed (Rate Limit/Server): {e}. Switching to next...")
                last_error = e
                continue 
            
            except InvalidArgument as e:
                logger.warning(f"⚠️ Model {model_name} config error: {e}. Skipping...")
                last_error = e
                continue

            except Exception as e:
                logger.error(f"❌ Unexpected error on {model_name}: {e}")
                last_error = e
                continue

        logger.critical(f"💀 All models failed. Last Error: {last_error}")
        return "🐸 My brain is buffering... (All circuits busy, please try again in a minute.)"

    @classmethod
    async def get_response(cls, user_text: str):
        """Chat wrapper."""
        return await cls._generate_with_retry(user_text, temperature=0.9)

    @classmethod
    async def summarize_news(cls, news_title: str, news_source: str):
        """
        News analysis wrapper.
        Instructions: Strict "SKIP" or "SUMMARIZE" logic.
        """
        prompt = (
            f"Act as a Crypto News Editor. Analyze: '{news_title}' from '{news_source}'.\n"
            "1. If it's minor noise/spam -> Reply 'SKIP'.\n"
            "2. If important -> Summarize in 1 exciting sentence (Detect Language: Use the same language as the news title)."
        )
        return await cls._generate_with_retry(prompt, temperature=0.5)

    @classmethod
    async def generate_daily_digest(cls, news_list):
        """
        Daily/Instant Digest wrapper.
        Refined for maximum readability on Telegram (Mobile/Desktop).
        """
        news_text = "\n".join([f"- {item['title']} (Source: {item['source']})" for item in news_list])
        
        prompt = (
            f"Role: You are TOPI, the AI crypto market analyst.\n"
            f"Task: Write a 'Crypto Market Digest' based on these headlines:\n{news_text}\n\n"
            
            "--- FORMATTING RULES (STRICT) ---\n"
            "1. LANGUAGE: English ONLY (Global Edition Standard).\n"
            "2. TONE: Witty, energetic, use emojis.\n"
            "3. STRUCTURE & LAYOUT (Optimize for Telegram Readability):\n"
            "   - **Intro:** A single, high-energy hook sentence.\n"
            "   - **The Meat:** Select the top 4-5 stories. Format EXACTLY like this:\n"
            "     • [Emoji] **HEADLINE HERE**\n"
            "       -> [Short summary in 1 sentence]\n"
            "   - **Outro:** A short motivational closing.\n"
            "4. IMPORTANT: Do NOT use markdown headers (#). Use **bold** for emphasis. Keep it clean."
        )
        return await cls._generate_with_retry(prompt, temperature=0.8)