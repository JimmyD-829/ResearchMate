from typing import Tuple

class SentimentAnalyzer:
    POSITIVE_WORDS = {"好", "优秀", "增长", "上升", "盈利", "收益", "利好", "上涨", "成功", "创新", "领先", "强劲", "稳健", "改善", "提升", "增加", "突破", "利好"}
    NEGATIVE_WORDS = {"差", "亏损", "下降", "下跌", "风险", "利空", "失败", "下滑", "恶化", "减少", "暴跌", "低迷", "疲软", "危机", "负面", "问题"}

    @staticmethod
    def analyze(text: str) -> Tuple[str, float]:
        try:
            text_lower = text.lower()
            positive_count = sum(1 for word in SentimentAnalyzer.POSITIVE_WORDS if word in text_lower)
            negative_count = sum(1 for word in SentimentAnalyzer.NEGATIVE_WORDS if word in text_lower)
            
            total = positive_count + negative_count
            if total == 0:
                return ("neutral", 0)
            
            score = (positive_count - negative_count) / total * 100
            if score > 20:
                return ("positive", score)
            elif score < -20:
                return ("negative", score)
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