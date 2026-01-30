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
        Fetches all available Gemini models and sorts them by version.
        """
        try:
            all_models = genai.list_models()
            
            gemini_models = [
                m for m in all_models 
                if 'generateContent' in m.supported_generation_methods 
                and 'gemini' in m.name.lower()
            ]

            def model_sort_key(model):
                name = model.name.lower()
                version_match = re.search(r'(\d+\.\d+)', name)
                version = float(version_match.group(1)) if version_match else 0.0
                
                type_score = 0
                if 'ultra' in name: type_score = 3
                elif 'pro' in name: type_score = 2
                elif 'flash' in name: type_score = 1
                
                return (version, type_score)

            sorted_models = sorted(gemini_models, key=model_sort_key, reverse=True)
            model_names = [m.name for m in sorted_models]
            print(f"DEBUG: Discovered Models: {model_names}")
            return model_names

        except Exception as e:
            print(f"ERROR: Could not fetch model list. {e}")
            return ["models/gemini-1.5-pro", "models/gemini-1.5-flash"]

    def analyze_and_split(self, commit_data: dict) -> list[str]:
        files_analysis = commit_data.get('files_analysis', 'No detailed file changes available.')

        # Prompt'u daha da sertleştirdik ki parametre olmadan da JSON versin
        prompt = (
            f"Role: You are the Lead Developer of 'Pepetopia'.\n"
            f"Task: Create a story-driven update based on the code changes.\n\n"
            
            f"STRICT RULES:\n"
            f"1. Ignore the raw commit message text.\n"
            f"2. Output MUST be a valid JSON List of strings. Example: [\"Update part 1\", \"Update part 2\"]\n"
            f"3. Do NOT use Markdown code blocks (like ```json). Just raw JSON text.\n"
            f"4. Language: Turkish 🇹🇷.\n"
            f"5. If changes are empty, return a generic update JSON.\n\n"
            
            f"INPUT CONTEXT:\n"
            f"Code Changes: \n{files_analysis}\n"
        )

        available_models = self._get_sorted_models()

        for model_name in available_models:
            try:
                print(f"INFO: Trying model: {model_name}...")
                model = genai.GenerativeModel(model_name)
                
                # KRİTİK DÜZELTME: generation_config parametresini kaldırdık.
                # Artık kütüphane hatası almayacağız, prompt ile JSON alacağız.
                response = model.generate_content(prompt)
                
                text = response.text.strip()
                
                # Temizlik (AI bazen inatçıdır, markdown eklerse temizle)
                if text.startswith("```json"):
                    text = text.replace("```json", "").replace("```", "")
                elif text.startswith("```"):
                    text = text.replace("```", "")
                
                # JSON Validation
                updates = json.loads(text)
                
                print(f"SUCCESS: Model {model_name} worked.")
                
                if isinstance(updates, list):
                    return updates
                return [text]

            except exceptions.NotFound:
                print(f"WARNING: Model {model_name} 404. Next...")
                continue
            except exceptions.ResourceExhausted:
                print(f"WARNING: Model {model_name} Rate Limit. Next...")
                continue
            except Exception as e:
                print(f"ERROR: Failed with {model_name}. Details: {e}")
                continue

        return [
            "🛠️ **Altyapı Güçlendirme Çalışması**\n\n"
            "Ekibimiz bugün sistemin çekirdek modüllerinde performans optimizasyonları gerçekleştirdi."
        ]