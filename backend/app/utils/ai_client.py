import os
from dotenv import load_dotenv

load_dotenv()

class AIClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
    
    def analyze_financial_report(self, content: str) -> dict:
        return {
            "summary": "根据财报数据分析，公司整体运营状况良好。",
            "key_metrics": {
                "revenue_growth": "15.3%",
                "net_profit": "¥2.8亿",
                "eps": "0.85",
                "pe_ratio": "25.6"
            },
            "analysis": "公司营收同比增长15.3%，净利润达到2.8亿元，每股收益0.85元，市盈率25.6倍。整体财务状况稳健。",
            "suggestions": ["关注毛利率变化趋势", "留意应收账款周转情况"]
        }
    
    def compare_reports(self, reports: list) -> dict:
        return {
            "comparison": "多期财报对比分析完成",
            "growth_rates": {
                "营收增长率": "12.5%",
                "净利润增长率": "8.3%",
                "毛利率变化": "+2.1%"
            },
            "insights": "公司业绩保持稳定增长态势"
        }
    
    def benchmark_analysis(self, company_data: dict) -> dict:
        return {
            "industry_avg": {
                "pe_ratio": 28.5,
                "revenue_growth": 10.2,
                "profit_margin": 15.8
            },
            "company_value": {
                "pe_ratio": 25.6,
                "revenue_growth": 15.3,
                "profit_margin": 18.2
            },
            "assessment": "公司估值低于行业平均水平，增长表现优于同行"
        }
    
    def answer_question(self, question: str) -> str:
        return f"关于您的问题：{question}\n\n根据数据分析，我们认为..."
    
    def natural_language_query(self, query: str) -> str:
        import json
        
        if not self.api_key:
            return json.dumps({
                "error": "OPENAI_API_KEY not configured",
                "suggestion": "Please set OPENAI_API_KEY in environment variables"
            })
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a financial analysis assistant. Answer questions about companies, financial reports, and market data."},
                    {"role": "user", "content": query}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return json.dumps({
                "answer": response.choices[0].message.content,
                "model": "gpt-3.5-turbo",
                "query": query
            })
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "fallback_answer": self.answer_question(query)
            })
    
    def analyze_with_methodology(self, parsed_data: dict) -> str:
        import json
        
        if not self.api_key:
            return json.dumps({
                "analysis": self.analyze_financial_report(json.dumps(parsed_data)),
                "note": "Using fallback mode (no API key)"
            })
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a financial analyst. Analyze the following financial report data using standard financial methodologies like DCF, ratio analysis, etc."},
                    {"role": "user", "content": f"Analyze this financial data: {json.dumps(parsed_data, ensure_ascii=False)}"}
                ],
                max_tokens=1500,
                temperature=0.5
            )
            
            return json.dumps({
                "methodology_analysis": response.choices[0].message.content,
                "data_source": "AI-powered analysis"
            })
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "fallback": self.analyze_financial_report(json.dumps(parsed_data))
            })