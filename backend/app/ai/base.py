from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class ClassificationResult(BaseModel):
    category: str
    confidence: float
    provider: str
    is_fallback: bool = False

class PriorityResult(BaseModel):
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    priority_score: int  # 0 to 100
    signals: List[str]
    explanation: str

class SummaryResult(BaseModel):
    summary: str
    key_facts: List[str]
    affected_area: Optional[str] = None
    urgency: Optional[str] = None
    provider: str
    is_fallback: bool = False

class DuplicateMatch(BaseModel):
    possible_duplicate: bool
    similarity: float
    matched_grievance_id: Optional[str] = None
    reason: Optional[str] = None

class ClassifierProvider(ABC):
    @abstractmethod
    def classify(self, title: str, description: str) -> ClassificationResult:
        pass

class PriorityAssessorProvider(ABC):
    @abstractmethod
    def assess_priority(self, title: str, description: str, location: str, category: str) -> PriorityResult:
        pass

class SummarizerProvider(ABC):
    @abstractmethod
    def summarize(self, title: str, description: str) -> SummaryResult:
        pass

class EmbeddingProvider(ABC):
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        pass
