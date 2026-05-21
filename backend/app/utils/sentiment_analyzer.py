from snownlp import SnowNLP
from typing import Tuple

class SentimentAnalyzer:
    @staticmethod
    def analyze(text: str) -> Tuple[str, float]:
        try:
            s = SnowNLP(text)
            score = s.sentiments
            if score > 0.6:
                return ("positive", score * 100)
            elif score < 0.4:
                return ("negative", (score - 1) * 100)
            else:
                return ("neutral", 0)
        except Exception as e:
            return ("neutral", 0)
    
    @staticmethod
    def get_label(score: float) -> str:
        if score > 20:
            return "positive"
        elif score < -20:
            return "negative"
        else:
            return "neutral"
