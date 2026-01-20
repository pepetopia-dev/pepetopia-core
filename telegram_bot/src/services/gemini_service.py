import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable
import logging
from src.core.app_config import Config

# Initialize Logger
logger = logging.getLogger(__name__)

class GeminiService:
    """
    Manages AI interactions with a dynamic fallback system.
    It discovers available models at startup and prioritizes them (Newest -> Oldest).
    """

    # --- PRIORITY CONFIGURATION ---
    # The bot will search for these patterns in the available model list.
    # Order matters: It will prioritize matching models in this order.
    # We prioritize 'flash' models for speed/cost efficiency in chat bots.
    MODEL_PRIORITY_ORDER = [
        "gemini-3-flash-preview",  # 🚀 Theoretical / Future Access
        "gemini-2.0-flash-exp",    # ⚡ Cutting Edge
        "gemini-1.5-pro",          # 🧠 High Intelligence
        "gemini-1.5-flash",        # 🏎️ High Speed & Rate Limits
        "gemini-1.0-pro"           # 🐢 Legacy Fallback
    ]

    # This list will be populated dynamically at runtime
    AVAILABLE_MODELS = []

    # --- PERSONA DEFINITION ---
    TOPI_SYSTEM_INSTRUCTION = (
        "You are 'TOPI', the energetic, loyal, and witty mascot of the Pepetopia ($PEPETOPIA) community on Solana. "
        "You are NOT Pepe the Frog; you are TOPI, a unique entity native to the Pepetopia universe.\n"
        "Your personality is a mix of a helpful assistant, a crypto degen, and a quantum physicist.\n\n"
        
        "--- LANGUAGE PROTOCOL ---\n"
        "1. ALWAYS RESPOND IN ENGLISH.\n"
        "2. Be concise and fun.\n"
        "3. Use crypto slang (WAGMI, LFG, Based) and emojis (🐸, 🚀).\n"
        "4. If asked about price prediction, give a vague 'Quantum Oracle' answer."
    )

    @classmethod
    def initialize(cls):
        """
        Initializes the Gemini API and discovers available models.
        Sorts them based on the MODEL_PRIORITY_ORDER.
        """
        if not Config.GEMINI_API_KEY:
            logger.error("Gemini API Key is missing!")
            return
        
        try:
            # Configure the global API key
            genai.configure(api_key=Config.GEMINI_API_KEY)
            
            # --- DYNAMIC DISCOVERY ---
            logger.info("📡 Discovering available Gemini models...")
            all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # Filter and Sort based on our Priority List
            cls.AVAILABLE_MODELS = []
            
            # 1. Add models that explicitly match our priority list (in order)
            for priority_pattern in cls.MODEL_PRIORITY_ORDER:
                # We look for partial matches (e.g. "models/gemini-1.5-flash-001" matches "gemini-1.5-flash")
                for model_id in all_models:
                    if priority_pattern in model_id:
                        if model_id not in cls.AVAILABLE_MODELS:
                            cls.AVAILABLE_MODELS.append(model_id)
            
            # 2. Safety Fallback: If discovery failed to match anything preferred, use a default
            if not cls.AVAILABLE_MODELS:
                logger.warning("⚠️ No preferred models found. Using hardcoded fallback.")
                cls.AVAILABLE_MODELS = ["models/gemini-1.5-flash", "models/gemini-pro"]
            
            logger.info(f"✅ Final Model Chain: {cls.AVAILABLE_MODELS}")

        except Exception as e:
            logger.error(f"Failed to initialize Gemini Service: {e}")
            # Absolute fallback to prevent crash
            cls.AVAILABLE_MODELS = ["models/gemini-1.5-flash"]

    @classmethod
    async def _generate_with_retry(cls, prompt: str, temperature: float = 0.7) -> str:
        """
        CORE ENGINE: Iterates through the discovered AVAILABLE_MODELS.
        If a model hits a Rate Limit (429) or Error, it switches to the next one in the chain.
        """
        if not cls.AVAILABLE_MODELS:
            cls.initialize()

        if not cls.AVAILABLE_MODELS:
            return "🐸 *Croak!* System initialization failed."

        errors = []

        # Loop through the prioritized model chain
        for model_name in cls.AVAILABLE_MODELS:
            try:
                # Initialize the specific model
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=cls.TOPI_SYSTEM_INSTRUCTION
                )
                
                # Set config
                config = genai.types.GenerationConfig(temperature=temperature)
                
                # Attempt generation
                response = model.generate_content(prompt, generation_config=config)
                
                # If successful, return immediately
                return response.text

            except (ResourceExhausted, InternalServerError, ServiceUnavailable) as e:
                # 429 Rate Limit or 500 Server Error -> Try Next Model
                logger.warning(f"⚠️ Model {model_name} exhausted/failed: {e}. Switching to next...")
                errors.append(f"{model_name}: {type(e).__name__}")
                continue 
            
            except Exception as e:
                # Critical Error (e.g., Invalid API Key, Bad Request) -> Stop
                logger.error(f"❌ Critical error with {model_name}: {e}")
                if "400" in str(e): 
                    return "🐸 My brain hurts. (Invalid Request - 400)"
                errors.append(str(e))
                # Usually no point retrying other models for a 400 error, but we continue just in case
                continue

        # If we exit the loop, all models failed
        logger.error(f"💀 All AI models failed. Chain trace: {errors}")
        return "🐸 My brain is buffering... All circuits busy! Try again in 1 min."

    @classmethod
    async def get_response(cls, user_text: str):
        """
        Chat wrapper for General Conversation.
        """
        return await cls._generate_with_retry(user_text, temperature=0.8)

    @classmethod
    async def summarize_news(cls, news_title: str, news_source: str):
        """
        News wrapper: Analyzes news importance.
        """
        prompt = (
            f"Act as a strict Crypto News Editor. Analyze this: '{news_title}' from '{news_source}'.\n"
            "Rules:\n"
            "1. Return 'SKIP' if it's spam, ads, or minor fluctuation.\n"
            "2. If IMPORTANT, write a 1-sentence exciting summary in English with a sentiment emoji (🟢/🔴).\n"
        )
        return await cls._generate_with_retry(prompt, temperature=0.3)

    @classmethod
    async def generate_daily_digest(cls, news_list):
        """
        Digest wrapper: Summarizes a list of news.
        """
        news_text = "\n".join([f"- {item['title']} ({item['source']})" for item in news_list])
        
        prompt = (
            f"Write a 'Daily Crypto Digest' in ENGLISH based on these headlines:\n\n{news_text}\n\n"
            "Style: Witty, energetic, crypto-native (use WAGMI, LFG).\n"
            "Format: Intro -> Bullet points -> Outro.\n"
            "Keep it under 500 chars."
        )
        return await cls._generate_with_retry(prompt, temperature=0.7)