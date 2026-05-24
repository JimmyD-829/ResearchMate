from typing import Tuple

class SentimentAnalyzer:
    POSITIVE_WORDS = {
        "好", "优秀", "增长", "上升", "盈利", "收益", "利好", "上涨", "成功",
        "创新", "领先", "强劲", "稳健", "改善", "提升", "增加", "突破",
        "利好", "看好", "推荐", "买入", "超预期", "大幅增长", "创新高",
        "反弹", "回升", "繁荣", "发展", "扩张", "合作", "收购", "投资",
        "发布", "推出", "获奖", "认证", "通过", "达成", "签署", "完成",
        "positive", "good", "growth", "rise", "profit", "gain", "success",
        "bullish", "outperform", "upgrade", "beat", "strong"
    }
    NEGATIVE_WORDS = {
        "差", "亏损", "下降", "下跌", "风险", "利空", "失败", "下滑",
        "恶化", "减少", "暴跌", "低迷", "疲软", "危机", "负面", "问题",
        "警告", "下调", "减持", "卖出", "低于预期", "大幅下跌", "创新低",
        "崩盘", "衰退", "裁员", "关闭", "违约", "调查", "诉讼", "罚款",
        "暂停", "推迟", "取消", "亏损", "负债", "破产", "困难", "挑战",
        "negative", "bad", "loss", "fall", "drop", "risk", "crisis",
        "bearish", "underperform", "downgrade", "miss", "weak"
    }

    @staticmethod
    def analyze(text: str) -> Tuple[str, float]:
        try:
            if not text:
                return ("neutral", 0)
            
            text_lower = text.lower()
            positive_count = sum(1 for word in SentimentAnalyzer.POSITIVE_WORDS if word in text_lower)
            negative_count = sum(1 for word in SentimentAnalyzer.NEGATIVE_WORDS if text_lower.find(word) != -1)
            
            total = positive_count + negative_count
            if total == 0:
                return ("neutral", 0.01)
            
            score = (positive_count - negative_count) / total * 100
            
            if score > 20:
                return ("positive", round(score, 2))
            elif score < -20:
                return ("negative", round(score, 2))
            else:
                return ("neutral", round(score, 2))
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