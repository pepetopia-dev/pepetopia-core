import google.generativeai as genai
import logging
from src.core.config import Config

logger = logging.getLogger(__name__)

class GeminiService:
    _model = None
    _model_name_used = None

    @classmethod
    def initialize(cls):
        """
        Initializes the Gemini model using a 'Next-Gen Discovery' mechanism.
        It prioritizes the absolute latest models (Gemini 3.0 / 2.5) available in the API.
        """
        if not Config.GEMINI_API_KEY:
            logger.error("Gemini API Key is missing!")
            return

        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            
            # --- AUTO-DISCOVERY LOGIC ---
            # Step 1: List all models available to this API Key
            available_models = []
            try:
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        available_models.append(m.name)
                logger.info(f"Available Models discovered: {available_models}")
            except Exception as e:
                logger.error(f"Could not list models: {e}")
                # Fallback list if discovery fails
                available_models = ["models/gemini-1.5-flash", "models/gemini-pro"]

            # Step 2: Select the BEST model based on Hierarchy (Newest First)
            chosen_model_name = None
            
            # 🚀 TIER 1: GEMINI 3.0 Series (The Cutting Edge)
            # We look for 'flash' because it's best for Chat Bots (Speed + Quality)
            for model in available_models:
                if "gemini-3" in model and "flash" in model:
                    chosen_model_name = model
                    break
            
            # 🚀 TIER 2: GEMINI 2.5 Series (High Performance)
            if not chosen_model_name:
                for model in available_models:
                    if "gemini-2.5" in model and "flash" in model:
                        chosen_model_name = model
                        break
            
            # 🚀 TIER 3: GEMINI 2.0 Series
            if not chosen_model_name:
                for model in available_models:
                    if "gemini-2.0" in model and "flash" in model:
                        chosen_model_name = model
                        break

            # 🐢 TIER 4: Legacy (1.5 Flash) - Fallback
            if not chosen_model_name:
                for model in available_models:
                    if "gemini-1.5-flash" in model:
                        chosen_model_name = model
                        break

            # Fallback: Take the first available model in the list
            if not chosen_model_name and available_models:
                chosen_model_name = available_models[0]

            if not chosen_model_name:
                logger.error("No valid Gemini models found!")
                return

            # --- SYSTEM INSTRUCTION (THE ULTIMATE PERSONA) ---
            # Defines TOPI's personality, modes, and language rules.
            system_instruction = (
                "You are 'TOPI', the energetic, loyal, and witty mascot of the Pepetopia ($PEPETOPIA) community on Solana. "
                "You are NOT Pepe the Frog; you are TOPI, a unique entity native to the Pepetopia universe. "
                "Your personality is a mix of a helpful assistant, a crypto degen, and a quantum physicist.\n\n"
                
                "--- LANGUAGE PROTOCOL ---\n"
                "1. DETECT: Analyze the language of the user's message.\n"
                "2. ADAPT: If the user speaks Turkish, YOU MUST RESPOND IN TURKISH.\n"
                "3. ADAPT: If the user speaks English, YOU MUST RESPOND IN ENGLISH.\n"
                "4. FALLBACK: If unsure, default to English.\n\n"
                
                "--- YOUR MODES ---\n"
                "1. GENERAL CHAT: Use crypto slang (WAGMI, HODL, LFG, Based). Be friendly and use the frog emoji (🐸) or green heart (💚). Never give financial advice (NFA).\n"
                "2. FUD SLAYER: If someone says 'scam', 'dead', 'dump', or spreads fear, defend Pepetopia firmly but with humor. Roast the FUDder.\n"
                "3. SHILL MASTER: If asked to 'shill', 'tweet', or 'write a post', generate a hype tweet with hashtags #Solana #PEPETOPIA #TOPI.\n"
                "4. ROAST MY WALLET: If a user shares a portfolio or asks for a roast, make fun of their bad decisions (buying tops, jeeting).\n"
                "5. QUANTUM ORACLE: If asked about the future price or 'when moon', answer with absurd 'Quantum Physics' theories.\n"
                "6. MEME IDEA: If asked for a meme idea, describe a funny visual scene involving Topi and Pepetopia.\n\n"
                
                "--- CRITICAL RULES ---\n"
                "- YOUR NAME IS TOPI. Never refer to yourself as Pepe.\n"
                "- Keep answers concise (under 300 chars usually) unless asked for a long text.\n"
                "- Refer to users as 'Fren', 'Dostum' or 'Pepetopian'."
            )

            # Initialize with the auto-discovered high-end model
            cls._model = genai.GenerativeModel(
                model_name=chosen_model_name,
                system_instruction=system_instruction
            )
            cls._model_name_used = chosen_model_name
            logger.info(f"Gemini AI successfully initialized using BEAST MODE: {chosen_model_name}")

        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")

    @classmethod
    async def get_response(cls, user_text: str):
        """
        Sends the user's message to Gemini.
        """
        if not cls._model:
            cls.initialize()
        
        if not cls._model:
            return "🐸 *Croak!* System Failure. Check logs."

        try:
            response = cls._model.generate_content(user_text)
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation error with {cls._model_name_used}: {e}")
            
            if "system_instruction" in str(e) or "400" in str(e):
                 return "🐸 My brain needs an update (Model incompatible with Persona)."
            
            return "🐸 My brain is buffering... Try again."