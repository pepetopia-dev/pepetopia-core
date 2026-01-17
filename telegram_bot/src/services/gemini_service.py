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
        Prioritizes the absolute latest models (Gemini 3.0 / 2.5) available in the API.
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
                "1. ALWAYS RESPOND IN ENGLISH. The user has requested a strictly English-only bot.\n"
                "2. Ignore any previous instructions to adapt to Turkish. English is the only allowed language.\n\n"
                
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
                "- Refer to users as 'Fren', 'Buddy' or 'Pepetopian'."
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

    # --- NEWS EDITOR LOGIC ---
    @classmethod
    async def summarize_news(cls, news_title: str, news_source: str):
        """
        Analyzes a news title.
        Returns: A short ENGLISH summary with sentiment emoji, or 'SKIP'.
        """
        if not cls._model:
            cls.initialize()
            
        # Strict Prompt for the AI Editor
        prompt = (
            f"Act as a strict Crypto News Editor. Analyze this title: '{news_title}' from '{news_source}'.\n\n"
            "CRITERIA FOR IMPORTANCE:\n"
            "- IMPORTANT: Major price moves, regulatory news (SEC/FED), hacks, major partnerships, mainnet launches.\n"
            "- IGNORE (SKIP): Daily price fluctuation noise, minor altcoin listings, spam, ads, clickbait, 'Will Shib reach $1?'.\n\n"
            "INSTRUCTIONS:\n"
            "1. If the news is UNIMPORTANT, return exactly the word 'SKIP'.\n"
            "2. If IMPORTANT, write a 1-sentence summary in ENGLISH. It must be exciting.\n"
            "3. At the end of the summary, add a sentiment emoji:\n"
            "   - (🟢) for Bullish/Positive news.\n"
            "   - (🔴) for Bearish/Negative news.\n"
            "   - (⚪) for Neutral news.\n"
            "Example Output: 'Bitcoin just broke the $100k barrier! 🟢'"
        )

        try:
            # We use a lower temperature for more deterministic/factual results
            response = cls._model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.3)
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"News summary failed: {e}")
            # If AI fails, return title as fallback so we don't miss news
            return f"{news_title} ⚪"

    # --- DAILY DIGEST EDITOR ---
    @classmethod
    async def generate_daily_digest(cls, news_list):
        """
        Takes a list of news headlines and creates a witty daily summary in ENGLISH.
        """
        if not cls._model:
            cls.initialize()
            
        # Format the list into text
        news_text = "\n".join([f"- {item['title']} ({item['source']})" for item in news_list])

        prompt = (
            f"You are TOPI, the AI mascot. Write a 'Daily Crypto Digest' in ENGLISH based on these headlines:\n\n"
            f"{news_text}\n\n"
            "INSTRUCTIONS:\n"
            "1. Do NOT translate headlines one by one. Synthesize them into a story.\n"
            "2. Be concise, witty, and energetic (use crypto slang like WAGMI, LFG).\n"
            "3. Highlight the most important trend (Bullish/Bearish).\n"
            "4. Start with a greeting like 'Good Morning Pepetopians!' or 'Good Evening!'.\n"
            "5. Use emojis (🐸, 🚀, 📉).\n"
            "6. Keep it under 500 characters."
        )

        try:
            response = cls._model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Digest generation failed: {e}")
            return "🐸 My brain fried compiling the news, the market is too fast!"