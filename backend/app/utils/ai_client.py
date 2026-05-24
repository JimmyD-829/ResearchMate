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
    
    def industry_benchmark(self, company_name: str) -> str:
        import json

        benchmark_data = {
            "company_name": company_name,
            "analysis_date": "2026-05-24",
            "industry_positioning": {
                "market_share": "12.5%",
                "industry_ranking": "Top 15%",
                "competitive_advantage": ["品牌影响力强", "研发投入领先", "渠道覆盖广泛"]
            },
            "financial_comparison": {
                "revenue_growth": {
                    "company": "15.3%",
                    "industry_avg": "10.2%",
                    "assessment": "优于行业平均"
                },
                "profit_margin": {
                    "company": "18.2%",
                    "industry_avg": "15.8%",
                    "assessment": "盈利能力突出"
                },
                "roe": {
                    "company": "16.8%",
                    "industry_avg": "12.5%",
                    "assessment": "资本回报率优秀"
                },
                "debt_ratio": {
                    "company": "45.2%",
                    "industry_avg": "52.3%",
                    "assessment": "财务结构稳健"
                }
            },
            "swot_analysis": {
                "strengths": ["技术领先", "市场份额增长", "现金流充足"],
                "weaknesses": ["国际化程度不足", "产品线相对集中"],
                "opportunities": ["数字化转型加速", "新兴市场拓展"],
                "threats": ["行业竞争加剧", "原材料成本波动"]
            },
            "peer_comparison": [
                {"peer": "同行A", "score": 78, "revenue_growth": "12.1%"},
                {"peer": "同行B", "score": 82, "revenue_growth": "14.5%"},
                {"peer": company_name, "score": 85, "revenue_growth": "15.3%"}
            ],
            "overall_assessment": f"{company_name}在行业中处于领先地位，财务指标优于行业平均水平，建议持续关注其技术创新和市场拓展进展。",
            "recommendation": "推荐 - 公司基本面良好，具备长期投资价值"
        }

        return json.dumps(benchmark_data, ensure_ascii=False)

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