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
    2. Sorting: Prioritizes versions (e.g., 2.0 > 1.5) and Capability (Pro > Flash).
    3. Resilience: If Model A hits a Rate Limit (429), it IMMEDIATELY retries with Model B 
       using the exact same prompt.
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
        Ensures we have a robust list ranging from 'Experimental' to 'Stable'.
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
            # We give points to models to sort them: High Version > Pro > Flash
            def model_scorer(model_name):
                name = model_name.lower()
                score = 0.0
                
                # Extract version (e.g., 1.5, 2.0)
                version_match = re.search(r'gemini-(\d+(\.\d+)?)', name)
                if version_match:
                    version = float(version_match.group(1))
                    score += version * 1000  # Base Score (Version is king)

                # Tier Adjustments
                # Pro/Exp usually hits limits faster, but is smarter. We try them first.
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
            # We must ensure 'gemini-1.5-flash' (The tank) is the absolute LAST resort.
            # It has the highest free tier limits.
            
            final_chain = []
            safety_net_models = []
            
            for m in sorted_models:
                # If it's a 1.5 Flash model, save it for the end
                if "gemini-1.5-flash" in m and "8b" not in m:
                    safety_net_models.append(m)
                else:
                    final_chain.append(m)
            
            # Sort safety net to put "latest" or "002" versions of flash first
            safety_net_models.sort(key=lambda x: "latest" in x or "002" in x, reverse=True)
            
            # Append safety net at the end
            final_chain.extend(safety_net_models)

            # Fallback if list is empty
            if not final_chain:
                final_chain = ["models/gemini-2.0-flash-exp", "models/gemini-1.5-pro", "models/gemini-1.5-flash"]

            cls._available_models = final_chain
            
            logger.info(f"🧬 AI DNA (Optimized Chain): {cls._available_models}")

        except Exception as e:
            logger.error(f"Failed to initialize Gemini Service: {e}")
            cls._available_models = ["models/gemini-1.5-flash"]

    @classmethod
    async def _generate_with_retry(cls, prompt: str, temperature: float = 0.8) -> str:
        """
        THE SURVIVAL LOOP:
        Iterates through the model chain. If a model fails (Quota/Error), 
        it seamlessly passes the SAME prompt to the next model.
        """
        if not cls._available_models:
            cls.initialize()

        last_error = None

        for i, model_name in enumerate(cls._available_models):
            try:
                # Configuration
                # Only enable search tool for high-tier models to avoid config errors on simpler ones
                tools = []
                if "pro" in model_name or "gemini-2" in model_name:
                    tools = [{"google_search_retrieval": {}}]

                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=cls.TOPI_SYSTEM_INSTRUCTION,
                    # tools=tools 
                )
                
                config = genai.types.GenerationConfig(temperature=temperature)
                
                # logger.info(f"🤖 Thinking with {model_name}...")
                
                # Execute (Async execution in thread pool to prevent blocking)
                response = await asyncio.to_thread(
                    model.generate_content, 
                    prompt, 
                    generation_config=config
                )
                
                if response.text:
                    return response.text

            except (ResourceExhausted, InternalServerError, ServiceUnavailable) as e:
                # 429 = QUOTA EXCEEDED. This is what we want to catch.
                logger.warning(f"⚠️ Quota Hit/Server Error on {model_name}. Switching to next model... ({e})")
                last_error = e
                continue # Try next model in loop
            
            except InvalidArgument as e:
                logger.warning(f"⚠️ Config Mismatch on {model_name}: {e}. Skipping...")
                last_error = e
                continue

            except Exception as e:
                logger.error(f"❌ Unexpected Error on {model_name}: {e}")
                last_error = e
                continue

        # If we reach here, ALL models failed.
        logger.critical(f"💀 All AI models failed. Last Error: {last_error}")
        return "🐸 My brain is buffering... (Global neural outage, please try again in 5 mins.)"

    @classmethod
    async def get_response(cls, user_text: str):
        """Chat wrapper."""
        return await cls._generate_with_retry(user_text, temperature=0.9)

    @classmethod
    async def summarize_news(cls, news_title: str, news_source: str):
        """News analysis wrapper."""
        prompt = (
            f"Act as a Crypto News Editor. Analyze: '{news_title}' from '{news_source}'.\n"
            "1. If it's minor noise/spam -> Reply 'SKIP'.\n"
            "2. If important -> Summarize in 1 exciting sentence (Detect Language: Use the same language as the news title)."
        )
        return await cls._generate_with_retry(prompt, temperature=0.5)

    @classmethod
    async def generate_daily_digest(cls, news_list):
        """Daily/Instant Digest wrapper."""
        news_text = "\n".join([f"- {item['title']} (Source: {item['source']})" for item in news_list])
        prompt = (
            f"Role: You are TOPI, the AI crypto market analyst.\n"
            f"Task: Write a 'Crypto Market Digest' based on these headlines:\n{news_text}\n\n"
            "--- FORMATTING RULES ---\n"
            "1. LANGUAGE: English ONLY (Global Standard).\n"
            "2. TONE: Witty, energetic, use emojis.\n"
            "3. FORMAT: Bullet points with bold headers. Keep it concise."
        )
        # Use a lower temperature for digests to be more factual
        return await cls._generate_with_retry(prompt, temperature=0.7)