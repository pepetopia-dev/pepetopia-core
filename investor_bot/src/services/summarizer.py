"""
Commit Summarizer Service Module

Provides intelligent summarization of GitHub commits using Google's Gemini AI models.
Implements dynamic model discovery, intelligent sorting by version and capability,
and automatic fallback mechanism for rate limit handling.

Features:
    - Dynamic fetching of all available Gemini models via API
    - Regex-based version extraction and intelligent model sorting
    - Automatic model fallback on rate limits or errors
    - Non-technical summary generation for stakeholder communication

Author: Pepetopia Development Team
"""

import json
import re
import sys
import time
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Dict, List, Optional, Tuple

import google.generativeai as genai
from google.api_core import exceptions

from src.app_config import config
from src.utils.logger import get_logger


# Initialize module logger
logger = get_logger(__name__)


class ModelTier(IntEnum):
    """
    Enumeration representing Gemini model capability tiers.
    
    Higher values indicate more capable models that should be
    prioritized in the selection process.
    """
    NANO = 0
    FLASH = 1
    PRO = 2
    ULTRA = 3


@dataclass
class GeminiModelInfo:
    """
    Data class representing parsed information about a Gemini model.
    
    Attributes:
        name: Full model identifier (e.g., 'models/gemini-2.0-pro')
        version: Extracted version number (e.g., 2.0)
        tier: Model capability tier (NANO, FLASH, PRO, ULTRA)
        is_experimental: Whether the model is marked as experimental
    """
    name: str
    version: float
    tier: ModelTier
    is_experimental: bool = False
    
    @property
    def sort_key(self) -> Tuple[float, int, int]:
        """
        Generates a sorting key for model prioritization.
        
        Returns:
            Tuple of (version, tier_value, experimental_penalty)
            Higher values indicate higher priority models.
        """
        # Experimental models get lower priority
        experimental_penalty = 0 if not self.is_experimental else -1
        return (self.version, self.tier.value, experimental_penalty)


class ModelDiscoveryService:
    """
    Service responsible for discovering and managing available Gemini models.
    
    Handles API communication with Google's model listing endpoint,
    parses model information using regex patterns, and provides
    sorted model lists for optimal selection.
    """
    
    # Regex patterns for model parsing
    VERSION_PATTERN = re.compile(r'gemini[- ]?(\d+(?:\.\d+)?)', re.IGNORECASE)
    TIER_PATTERNS = {
        ModelTier.ULTRA: re.compile(r'ultra', re.IGNORECASE),
        ModelTier.PRO: re.compile(r'pro', re.IGNORECASE),
        ModelTier.FLASH: re.compile(r'flash', re.IGNORECASE),
        ModelTier.NANO: re.compile(r'nano', re.IGNORECASE),
    }
    EXPERIMENTAL_PATTERN = re.compile(r'exp|experimental|preview', re.IGNORECASE)
    
    # Fallback models if API discovery fails
    FALLBACK_MODELS = [
        "models/gemini-2.0-flash",
        "models/gemini-1.5-pro",
        "models/gemini-1.5-flash",
    ]
    
    def __init__(self):
        """Initializes the model discovery service."""
        self._cached_models: Optional[List[str]] = None
        self._cache_timestamp: Optional[float] = None
    
    def _parse_model_info(self, model: Any) -> Optional[GeminiModelInfo]:
        """
        Parses a model object into structured GeminiModelInfo.
        
        Args:
            model: Raw model object from the Gemini API
            
        Returns:
            GeminiModelInfo if parsing succeeds, None otherwise
        """
        try:
            name = model.name
            name_lower = name.lower()
            
            # Extract version using regex
            version_match = self.VERSION_PATTERN.search(name_lower)
            version = float(version_match.group(1)) if version_match else 1.0
            
            # Determine model tier
            tier = ModelTier.FLASH  # Default tier
            for tier_enum, pattern in self.TIER_PATTERNS.items():
                if pattern.search(name_lower):
                    tier = tier_enum
                    break
            
            # Check if experimental
            is_experimental = bool(self.EXPERIMENTAL_PATTERN.search(name_lower))
            
            return GeminiModelInfo(
                name=name,
                version=version,
                tier=tier,
                is_experimental=is_experimental
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse model info: {e}")
            return None
    
    def discover_models(self) -> List[str]:
        """
        Discovers all available Gemini models supporting content generation.
        
        Fetches the complete model list from Google's API, filters for
        models supporting generateContent, and sorts them by capability.
        
        Returns:
            List of model names sorted by version and capability (newest first)
        """
        try:
            logger.info("Discovering available Gemini models...")
            
            # Fetch all models from API
            all_models = genai.list_models()
            
            # Filter for content generation capable Gemini models
            gemini_models: List[GeminiModelInfo] = []
            
            for model in all_models:
                # Check if model supports content generation
                if 'generateContent' not in model.supported_generation_methods:
                    continue
                
                # Check if it's a Gemini model
                if 'gemini' not in model.name.lower():
                    continue
                
                # Parse model information
                model_info = self._parse_model_info(model)
                if model_info:
                    gemini_models.append(model_info)
            
            # Sort models by capability (highest first)
            sorted_models = sorted(
                gemini_models,
                key=lambda m: m.sort_key,
                reverse=True
            )
            
            # Extract model names
            model_names = [m.name for m in sorted_models]
            
            # Log discovered models
            logger.info(f"Discovered {len(model_names)} Gemini models")
            logger.debug(f"Model priority order: {model_names[:5]}...")
            
            return model_names if model_names else self.FALLBACK_MODELS
            
        except Exception as e:
            logger.error(f"Model discovery failed: {e}")
            logger.info("Using fallback model list")
            return self.FALLBACK_MODELS


class CommitSummarizer:
    """
    Main service for generating non-technical summaries of code commits.
    
    Transforms technical commit information into engaging, easy-to-understand
    updates suitable for non-technical stakeholders. Implements automatic
    model fallback for resilient operation.
    
    Attributes:
        model_discovery: Service for discovering available models
        available_models: List of models to try in priority order
    """
    
    # Summary generation prompt template
    SUMMARY_PROMPT_TEMPLATE = """
Role: You are the Lead Developer of 'Pepetopia', a community-driven project.

Task: Transform the following code changes into an engaging, non-technical update 
for our community members who are not developers.

STRICT OUTPUT RULES:
1. Output MUST be a valid JSON array of strings
2. Each string is a separate update message (for multi-part updates)
3. Do NOT use markdown code blocks - output raw JSON only
4. Language: Turkish (TR)
5. Use emojis to make updates engaging
6. Focus on WHAT was improved, not HOW (no technical jargon)
7. Make it sound exciting and positive
8. If changes are minimal, create a brief but positive update

EXAMPLE OUTPUT FORMAT:
["🎮 Oyun deneyimini iyileştiren güncellemeler yaptık!", "🚀 Sistem performansı artırıldı."]

CODE CHANGES TO SUMMARIZE:
{files_analysis}

Remember: Our community members are investors and supporters, not developers.
Make them feel excited about the progress!
"""
    
    # Fallback message when all models fail
    FALLBACK_MESSAGE = [
        "🛠️ **Infrastructure Enhancement**\n\n"
        "Our team completed performance optimizations on core system modules today. "
        "These improvements will enhance the overall user experience."
    ]
    
    # BUG FIX #3: Add retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 5
    
    def __init__(self):
        """
        Initializes the CommitSummarizer with API configuration.
        
        Raises:
            SystemExit: If Gemini API key is not configured
        """
        if not config.gemini_api_key:
            logger.critical("Gemini API Key is missing. Cannot initialize summarizer.")
            sys.exit(1)
        
        # Configure the Gemini API
        genai.configure(api_key=config.gemini_api_key)
        
        # Initialize model discovery service
        self.model_discovery = ModelDiscoveryService()
        self._available_models: Optional[List[str]] = None
        
        logger.info("CommitSummarizer initialized successfully")
    
    @property
    def available_models(self) -> List[str]:
        """
        Lazily loads and caches the list of available models.
        
        Returns:
            List of model names in priority order
        """
        if self._available_models is None:
            self._available_models = self.model_discovery.discover_models()
        return self._available_models
    
    def _build_prompt(self, commit_data: Dict[str, Any]) -> str:
        """
        Constructs the summarization prompt from commit data.
        
        Args:
            commit_data: Dictionary containing commit information
            
        Returns:
            Formatted prompt string for the AI model
        """
        files_analysis = commit_data.get(
            'files_analysis',
            'No detailed file changes available.'
        )
        
        return self.SUMMARY_PROMPT_TEMPLATE.format(files_analysis=files_analysis)
    
    def _parse_response(self, response_text: str) -> List[str]:
        """
        Parses and validates the AI model's response.
        
        Handles various response formats including markdown-wrapped JSON
        and extracts the update messages.
        
        Args:
            response_text: Raw response text from the AI model
            
        Returns:
            List of update message strings
            
        Raises:
            ValueError: If response cannot be parsed as valid JSON
        """
        text = response_text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]  # Remove ```json
        if text.startswith("```"):
            text = text[3:]  # Remove ```
        if text.endswith("```"):
            text = text[:-3]  # Remove trailing ```
        
        text = text.strip()
        
        # Parse JSON
        parsed = json.loads(text)
        
        # Ensure we return a list
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
        elif isinstance(parsed, str):
            return [parsed]
        else:
            return [str(parsed)]
    
    def _try_generate_with_model(
        self,
        model_name: str,
        prompt: str
    ) -> Optional[List[str]]:
        """
        Attempts to generate a summary using a specific model.
        
        Args:
            model_name: The Gemini model identifier to use
            prompt: The summarization prompt
            
        Returns:
            List of update messages if successful, None otherwise
        """
        try:
            logger.info(f"Attempting generation with model: {model_name}")
            
            # Create model instance
            model = genai.GenerativeModel(model_name)
            
            # Generate content
            response = model.generate_content(prompt)
            
            # Parse response
            updates = self._parse_response(response.text)
            
            logger.info(f"Successfully generated summary with {model_name}")
            return updates
            
        except exceptions.NotFound:
            logger.warning(f"Model {model_name} not found (404). Trying next model...")
            return None
            
        except exceptions.ResourceExhausted:
            logger.warning(f"Rate limit reached for {model_name}. Trying next model...")
            return None
            
        except exceptions.InvalidArgument as e:
            logger.warning(f"Invalid argument for {model_name}: {e}. Trying next model...")
            return None
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response from {model_name}: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error with {model_name}: {e}")
            return None
    
    def analyze_and_split(self, commit_data: Dict[str, Any]) -> List[str]:
        """
        Analyzes commit data and generates non-technical summary updates.
        
        Iterates through available models in priority order, attempting
        to generate a summary. Automatically falls back to the next model
        if rate limits or errors are encountered.
        
        BUG FIX #3: Implements retry logic with delays for rate limit handling.
        
        Args:
            commit_data: Dictionary containing commit information including:
                - files_analysis: String describing file changes
                - sha: Commit SHA
                - author: Commit author
                - message: Original commit message
                
        Returns:
            List of summary message strings suitable for Telegram posting
        """
        logger.info("Starting commit analysis and summarization")
        
        # Build the prompt
        prompt = self._build_prompt(commit_data)
        
        # BUG FIX #3: Implement retry logic for rate limit handling
        for attempt in range(self.MAX_RETRIES):
            if attempt > 0:
                logger.info(f"Retry attempt {attempt + 1}/{self.MAX_RETRIES} after delay...")
                time.sleep(self.RETRY_DELAY_SECONDS * attempt)  # Exponential backoff
            
            # Try each model in priority order
            for model_name in self.available_models:
                result = self._try_generate_with_model(model_name, prompt)
                
                if result is not None:
                    logger.info(f"Summary generation completed with {len(result)} update(s)")
                    return result
            
            logger.warning(f"All models exhausted on attempt {attempt + 1}")
        
        # All retries failed - return fallback message
        logger.error(f"All {self.MAX_RETRIES} retry attempts failed. Returning fallback message.")
        return self.FALLBACK_MESSAGE
    
    def refresh_models(self) -> None:
        """
        Forces a refresh of the available models list.
        
        Useful when models may have been added or removed, or when
        cached models are no longer responding.
        """
        logger.info("Refreshing available models list")
        self._available_models = None
        _ = self.available_models  # Trigger lazy load
