import re
from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from app.ai.base import ClassifierProvider, ClassificationResult

# Recognized realistic domain categories
VALID_CATEGORIES = [
    "ELECTRICAL_SAFETY",
    "WATER_SUPPLY",
    "ROAD_INFRASTRUCTURE",
    "SANITATION",
    "PUBLIC_HEALTH",
    "STREET_LIGHTING",
    "TRAFFIC",
    "WASTE_MANAGEMENT",
    "PUBLIC_TRANSPORT",
    "EDUCATION",
    "DOCUMENTATION",
    "REVENUE",
    "LAW_AND_ORDER",
    "ENVIRONMENT",
    "OTHER"
]

# Training corpus for realistic domain classification
TRAINING_DATA: List[Tuple[str, str]] = [
    ("wire electrical shock transformer power outage spark line cut high voltage", "ELECTRICAL_SAFETY"),
    ("broken live electrical wire hanging near school door gate exposed cable", "ELECTRICAL_SAFETY"),
    ("short circuit pole transformer explosion fire hazard power shock meter", "ELECTRICAL_SAFETY"),
    
    ("water leakage pipe pipeline drinking water no supply contamination tank shortage dirty water", "WATER_SUPPLY"),
    ("water pressure low main pipe burst sewage mixed with water tap water bad smell", "WATER_SUPPLY"),
    
    ("pothole road crack damaged asphalt tar street crater pavement broken road highway", "ROAD_INFRASTRUCTURE"),
    ("road construction delay bridge collapse footpath damaged divider broken cobblestone", "ROAD_INFRASTRUCTURE"),
    
    ("sewage overflow drain blocked toilet sanitation garbage dump bio hazard manhole open", "SANITATION"),
    ("drainage blocked waste water stagnant water mosquito breeding gutter cleaning septic tank", "SANITATION"),
    
    ("dengue outbreak hospital bed shortage clinic medicine doctor missing vaccine disease epidemic", "PUBLIC_HEALTH"),
    ("garbage pile health risk food poisoning hospital emergency ward unhygienic center", "PUBLIC_HEALTH"),
    
    ("street light dark bulb fuse dark road night illumination pole broken light dark alley", "STREET_LIGHTING"),
    
    ("traffic jam signal light broken congestion bottleneck road block parking issue accident zone", "TRAFFIC"),
    
    ("garbage collector missing waste dumping recycling bin uncollected trash plastic waste", "WASTE_MANAGEMENT"),
    
    ("bus delay ticket counter train service depot transport stop route missing metro", "PUBLIC_TRANSPORT"),
    
    ("school fee teacher missing classroom roof falling blackboard university exam leak", "EDUCATION"),
    
    ("passport birth certificate ration card Aadhaar delay verification certificate office delay", "DOCUMENTATION"),
    
    ("tax bill wrong property tax bribery overcharge fee receipt refund land record", "REVENUE"),
    
    ("theft police station FIR delay crime safety patrolling assault noise disturbance harassment", "LAW_AND_ORDER"),
    
    ("tree cutting forest pollution smoke industry factory chemical spill river contamination air quality", "ENVIRONMENT"),
]

class MLClassifier(ClassifierProvider):
    def __init__(self):
        texts = [item[0] for item in TRAINING_DATA]
        labels = [item[1] for item in TRAINING_DATA]
        
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        X = self.vectorizer.fit_transform(texts)
        
        self.model = LogisticRegression(C=1.0, max_iter=200)
        self.model.fit(X, labels)

    def classify(self, title: str, description: str) -> ClassificationResult:
        combined_text = f"{title} {description}".lower()
        cleaned_text = re.sub(r"[^\w\s]", " ", combined_text)
        
        X_vec = self.vectorizer.transform([cleaned_text])
        probs = self.model.predict_proba(X_vec)[0]
        max_idx = probs.argmax()
        confidence = float(probs[max_idx])
        predicted_category = self.model.classes_[max_idx]
        
        # Keyword override boost for precise domain detection if confidence is borderline
        if confidence < 0.6:
            if any(k in combined_text for k in ["wire", "electric", "power", "current", "shock", "voltage", "transformer"]):
                predicted_category = "ELECTRICAL_SAFETY"
                confidence = max(confidence, 0.85)
            elif any(k in combined_text for k in ["water", "leak", "pipe", "tap", "drain", "sewage"]):
                predicted_category = "WATER_SUPPLY"
                confidence = max(confidence, 0.80)
            elif any(k in combined_text for k in ["road", "pothole", "asphalt", "crater", "pavement"]):
                predicted_category = "ROAD_INFRASTRUCTURE"
                confidence = max(confidence, 0.80)
            elif any(k in combined_text for k in ["garbage", "trash"]):
                predicted_category = "SANITATION"
                confidence = max(confidence, 0.75)
            elif any(k in combined_text for k in ["waste", "dump"]):
                predicted_category = "WASTE_MANAGEMENT"
                confidence = max(confidence, 0.75)
                
        if predicted_category not in VALID_CATEGORIES:
            predicted_category = "OTHER"
            
        return ClassificationResult(
            category=predicted_category,
            confidence=round(confidence, 2),
            provider="TFIDF-LogisticRegression",
            is_fallback=False
        )
