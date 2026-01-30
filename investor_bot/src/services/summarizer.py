import google.generativeai as genai
from google.api_core import exceptions
import sys
import json
import re
from src.app_config import config

class CommitSummarizer:
    def __init__(self):
        if not config.gemini_api_key:
            print("CRITICAL: Gemini API Key missing.")
            sys.exit(1)
        genai.configure(api_key=config.gemini_api_key)

    def _get_sorted_models(self):
        """
        Fetches all available Gemini models and sorts them by version (Newest -> Oldest).
        Logic: High Version (1.5) > Model Type (Pro > Flash > Ultra)
        """
        try:
            # 1. Google'dan tüm modelleri çek
            all_models = genai.list_models()
            
            # 2. Sadece 'generateContent' yeteneği olan ve isminde 'gemini' geçenleri filtrele
            gemini_models = [
                m for m in all_models 
                if 'generateContent' in m.supported_generation_methods 
                and 'gemini' in m.name.lower()
            ]

            def model_sort_key(model):
                """
                Sorting Heuristic:
                1. Version Number (1.5 > 1.0)
                2. 'Pro' priority (Pro > Flash > others)
                """
                name = model.name.lower()
                
                # Regex ile versiyon numarasını bul (örn: gemini-1.5-pro -> 1.5)
                version_match = re.search(r'(\d+\.\d+)', name)
                version = float(version_match.group(1)) if version_match else 0.0
                
                # Model türüne puan ver
                type_score = 0
                if 'ultra' in name: type_score = 3
                elif 'pro' in name: type_score = 2
                elif 'flash' in name: type_score = 1
                
                return (version, type_score)

            # 3. Sırala (Büyükten küçüğe)
            sorted_models = sorted(gemini_models, key=model_sort_key, reverse=True)
            
            model_names = [m.name for m in sorted_models]
            print(f"DEBUG: Discovered Models (Sorted): {model_names}")
            return model_names

        except Exception as e:
            print(f"ERROR: Could not fetch model list. Defaulting to fallback list. {e}")
            # API çalışmazsa manuel bir yedek listesi
            return ["models/gemini-1.5-pro", "models/gemini-1.5-flash", "models/gemini-pro"]

    def analyze_and_split(self, commit_data: dict) -> list[str]:
        """
        Tries to generate content using the newest model. 
        Falls back to older models if rate limit or 404 occurs.
        """
        
        files_analysis = commit_data.get('files_analysis', 'No detailed file changes available.')

        prompt = (
            f"Role: You are the Lead Developer of 'Pepetopia', a Solana memecoin project.\n"
            f"Target Audience: Non-technical crypto investors.\n"
            f"Task: Create a story-driven update based on the code changes below.\n\n"
            
            f"STRICT RULES:\n"
            f"1. Ignore the raw commit message text. Focus on the 'Code Changes'.\n"
            f"2. Output MUST be a valid JSON List of strings. Example: [\"Update part 1\", \"Update part 2\"]\n"
            f"3. Do NOT use Markdown code blocks (```json). Just raw JSON.\n"
            f"4. Language: Turkish 🇹🇷.\n"
            f"5. If 'Code Changes' are empty or binary, make up a generic but professional update about 'System Optimization'.\n\n"
            
            f"INPUT CONTEXT:\n"
            f"Code Changes: \n{files_analysis}\n"
        )

        # Dinamik model listesini al
        available_models = self._get_sorted_models()

        last_error = None

        # Modelleri sırayla dene
        for model_name in available_models:
            try:
                print(f"INFO: Trying model: {model_name}...")
                model = genai.GenerativeModel(model_name)
                
                response = model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                
                text = response.text.strip()
                
                # Temizlik
                if text.startswith("```json"):
                    text = text.replace("```json", "").replace("```", "")
                elif text.startswith("```"):
                    text = text.replace("```", "")
                
                updates = json.loads(text)
                
                print(f"SUCCESS: Model {model_name} generated response successfully.")
                
                if isinstance(updates, list):
                    return updates
                return [text]

            except exceptions.NotFound:
                print(f"WARNING: Model {model_name} not found (404). Trying next...")
                continue # Bir sonrakine geç
            except exceptions.ResourceExhausted:
                print(f"WARNING: Model {model_name} rate limit exceeded (429). Trying next...")
                continue # Bir sonrakine geç
            except Exception as e:
                print(f"ERROR: Failed with {model_name}. Details: {e}")
                last_error = e
                continue # Diğer hatalarda da şansımızı diğer modelde deneyelim

        # Eğer döngü biter ve hiçbir model çalışmazsa:
        print("CRITICAL: All AI models failed.")
        return [
            "🛠️ **Altyapı Güçlendirme Çalışması**\n\n"
            "Ekibimiz bugün sistemin çekirdek modüllerinde performans optimizasyonları gerçekleştirdi. "
            "Sistem kararlılığını artırmak adına arka planda önemli bakım işlemleri tamamlandı."
        ]