from typing import List
from .output_schema import Candidate

class ScoringManager:
    """
    Manages scoring adjustments and safety filtering.
    """
    
    # Financial keywords to flag/penalize
    FINANCE_KEYWORDS = {
        "buy", "sell", "pump", "dump", "moon", "price", "prediction", "forecast", "financial advice"
    }
    
    # Promo keywords (allow if context is appropriate, otherwise penalize)
    PROMO_KEYWORDS = {
        "pepetopia", "bio", "check my bio", "link in bio", "subscribe"
    }

    @staticmethod
    def check_safety(text: str) -> List[str]:
        """
        Returns a list of safety flags triggered by the text.
        """
        flags = []
        text_lower = text.lower()
        
        # Check financial advice
        for word in ScoringManager.FINANCE_KEYWORDS:
            if f" {word} " in f" {text_lower} " or text_lower.startswith(word) or text_lower.endswith(word):
                flags.append("FINANCE_RISK")
                break
                
        # Check promo (blind check, context awareness is handled in apply_filters)
        for word in ScoringManager.PROMO_KEYWORDS:
             if f" {word} " in f" {text_lower} " or text_lower.startswith(word) or text_lower.endswith(word):
                flags.append("PROMO_RISK")
                break
        
        return flags

    @staticmethod
    def apply_filters(candidates: List[Candidate], topic: str) -> List[Candidate]:
        """
        Applies safety filters and adjusts scores.
        - Penalizes financial advice heavily.
        - Penalizes promo content unless topic is related to project.
        """
        filtered_candidates = []
        topic_lower = topic.lower() if topic else ""
        is_project_topic = "pepetopia" in topic_lower or "topi" in topic_lower
        
        for cand in candidates:
            flags = ScoringManager.check_safety(cand.text)
            
            # Penalties
            if "FINANCE_RISK" in flags:
                cand.score -= 50
                cand.risk_flags.append("FINANCE")
            
            if "PROMO_RISK" in flags:
                # If topic is NOT about the project, promo is spammy.
                if not is_project_topic:
                    cand.score -= 30
                    cand.risk_flags.append("UNSOLICITED_PROMO")
                else:
                    # If topic IS about project, promo might be okay, but still flag it as such.
                    cand.risk_flags.append("PROMO")

            # Final check: Don't show candidates with critical negative scores 
            # (unless we want to debug, but for now let's keep them if > 0)
            if cand.score > 0:
                filtered_candidates.append(cand)
                
        # Re-sort by score descending
        filtered_candidates.sort(key=lambda x: x.score, reverse=True)
        return filtered_candidates
