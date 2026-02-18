import re
from typing import List
from .output_schema import Candidate

class DiversityManager:
    """
    Manages diversity and duplication checks for generated candidates.
    """
    
    @staticmethod
    def calculate_jaccard_similarity(text1: str, text2: str) -> float:
        """
        Calculates Jaccard similarity between two texts based on word sets.
        Returns a float between 0.0 (no overlap) and 1.0 (identical).
        """
        # Simple tokenization: lower case, remove non-alphanumeric
        tokens1 = set(re.findall(r'\w+', text1.lower()))
        tokens2 = set(re.findall(r'\w+', text2.lower()))
        
        if not tokens1 and not tokens2:
            return 1.0 # Both empty
        if not tokens1 or not tokens2:
            return 0.0 # One empty
            
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        
        return intersection / union

    @staticmethod
    def filter_near_duplicates(candidates: List[Candidate], threshold: float = 0.5) -> List[Candidate]:
        """
        Filters out candidates that are too similar to previous ones in the list.
        Keeps the first occurrence (usually higher ranked/scored).
        """
        unique_candidates = []
        
        for candidate in candidates:
            is_duplicate = False
            for kept in unique_candidates:
                similarity = DiversityManager.calculate_jaccard_similarity(candidate.text, kept.text)
                if similarity > threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_candidates.append(candidate)
                
        return unique_candidates
