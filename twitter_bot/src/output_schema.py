from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class Analysis:
    topic: str
    intent: str
    tone: str
    sentiment: str

@dataclass
class Candidate:
    id: int
    text: str
    score: int
    rationale: str
    risk_flags: List[str] = field(default_factory=list)
    
@dataclass
class EngineResponse:
    analysis: Analysis
    candidates: List[Candidate]
    model_used: str = "Unknown"
    persona: str = "Unknown"
    
    def to_dict(self):
        return {
            "analysis": self.analysis.__dict__,
            "candidates": [c.__dict__ for c in self.candidates],
            "model_used": self.model_used,
            "persona": self.persona
        }
