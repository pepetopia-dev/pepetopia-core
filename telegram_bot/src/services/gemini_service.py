import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable, InvalidArgument
import logging
import re
from src.core.app_config import Config

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Advanced AI Service Manager (Generic & Future-Proof).
    
    Strategy: "Bleeding Edge First -> Safety Net Last"
    1. Dynamic Discovery: Uses Regex to parse version numbers (e.g., 3.0 > 2.5 > 1.5).
    2. Priority Sorting: Prioritizes higher versions and 'Pro' models.
    3. Safety Fallback: Ensures 'Gemini 1.5 Flash' is always the final fallback option.
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
        It strictly enforces the 'Newest First, 1.5 Flash Last' strategy.
        """
        if not Config.GEMINI_API_KEY:
            logger.error("Gemini API Key is missing!")
            return
        
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            
            logger.info("📡 Discovering available Gemini models...")
            
            # 1. Fetch all models from Google API
            all_raw_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # Filter out irrelevant models (e.g., Gemma, Nano, embedding models)
            filtered_models = [m for m in all_raw_models if "gemma" not in m and "nano" not in m and "embedding" not in m]

            # 2. SCORING ALGORITHM (Generic)
            # Assigns a score based on version number and capability (Pro/Flash).
            def model_scorer(model_name):
                name = model_name.lower()
                score = 0.0
                
                # Extract version number using Regex (e.g., gemini-1.5 -> 1.5)
                version_match = re.search(r'gemini-(\d+(\.\d+)?)', name)
                if version_match:
                    version = float(version_match.group(1))
                    score += version * 1000  # Version is the primary weight (3.0 > 1.5)

                # Tier Adjustments
                if "pro" in name: score += 50
                if "flash" in name: score += 20
                
                # 'Latest' or 'Exp' usually implies newer capabilities
                if "latest" in name: score += 10
                if "exp" in name or "preview" in name: score += 5
                
                # Deprioritize 'Lite' models slightly
                if "lite" in name: score -= 10
                
                return score

            # Sort descending (Highest score first)
            sorted_models = sorted(filtered_models, key=model_scorer, reverse=True)
            
            # 3. CONSTRUCTING THE CHAIN
            # Identify the ultimate fallback model (Gemini 1.5 Flash)
            fallback_target = "models/gemini-1.5-flash"
            
            # List to hold the final sequence
            final_chain = []
            
            # Add sorted models to chain, but skip the fallback target for now
            for m in sorted_models:
                if fallback_target not in m:
                    final_chain.append(m)
            
            # Force append the safety net at the very end
            # We check if it exists in the raw list to avoid adding invalid models
            fallback_candidates = [m for m in all_raw_models if "gemini-1.5-flash" in m and "latest" not in m]
            if fallback_candidates:
                # Use the specific 1.5 flash model found (e.g., models/gemini-1.5-flash-001)
                final_chain.append(fallback_candidates[0])
            elif fallback_target in all_raw_models:
                 final_chain.append(fallback_target)

            # If the chain is empty (API error?), hardcode a backup list
            if not final_chain:
                final_chain = ["models/gemini-2.0-flash-exp", "models/gemini-1.5-pro", "models/gemini-1.5-flash"]

            cls._available_models = final_chain
            
            logger.info(f"🧬 AI DNA (Generic Sort): {cls._available_models}")

        except Exception as e:
            logger.error(f"Failed to initialize Gemini Service: {e}")
            # Absolute fallback
            cls._available_models = ["models/gemini-1.5-flash"]

    @classmethod
    async def _generate_with_retry(cls, prompt: str, temperature: float = 0.8) -> str:
        """
        THE UNSTOPPABLE ENGINE:
        Iterates through the sorted model list.
        If Model A fails (Quota/Error), it seamlessly switches to Model B.
        """
        if not cls._available_models:
            cls.initialize()

        last_error = None

        for i, model_name in enumerate(cls._available_models):
            try:
                # Configure Tools (Google Search) for capable models (Pro/2.0+)
                tools = []
                # Enabling search only for high-tier models to avoid errors on lightweight ones
                if "pro" in model_name or "gemini-2" in model_name or "gemini-3" in model_name:
                    tools = [{"google_search_retrieval": {}}]

                # Initialize Model
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=cls.TOPI_SYSTEM_INSTRUCTION,
                    # tools=tools # Uncomment if your API key supports search tools
                )
                
                config = genai.types.GenerationConfig(temperature=temperature)
                
                # Execute Generation
                # logger.debug(f"🤖 Attempting generation with {model_name}...")
                response = model.generate_content(prompt, generation_config=config)
                
                if response.text:
                    return response.text

            except (ResourceExhausted, InternalServerError, ServiceUnavailable) as e:
                # 429 Quota Exceeded -> Log warning and CONTINUE to next model
                logger.warning(f"⚠️ Quota Hit on {model_name}. Switching to next model...")
                last_error = e
                continue 
            
            except InvalidArgument as e:
                # Model config mismatch -> Skip to next
                logger.warning(f"⚠️ Config Mismatch on {model_name}: {e}. Skipping...")
                last_error = e
                continue

            except Exception as e:
                # Other errors -> Log and continue
                logger.error(f"❌ Error on {model_name}: {e}")
                last_error = e
                continue

        # If we reach here, every single model in the chain failed.
        logger.critical(f"💀 All models failed. Last Error: {last_error}")
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
        return await cls._generate_with_retry(prompt, temperature=0.8)