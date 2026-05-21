from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

class AIClient:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def generate_summary(self, financial_data: dict) -> str:
        prompt = f"""
        请根据以下财务数据，用中文生成一份200字左右的财报摘要：
        
        公司名称：{financial_data.get('company_name', '未知')}
        股票代码：{financial_data.get('stock_code', '未知')}
        报告期：{financial_data.get('report_period', '未知')}
        营收：{financial_data.get('revenue', '未知')}万元
        净利润：{financial_data.get('net_profit', '未知')}万元
        经营现金流：{financial_data.get('cash_flow', '未知')}万元
        负债率：{financial_data.get('debt_ratio', '未知')}%
        毛利率：{financial_data.get('gross_margin', '未知')}%
        
        请用简洁明了的语言总结该公司的财务状况和主要亮点。
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是一个专业的金融分析师，请用简洁专业的语言分析财报数据。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return "无法生成摘要，请稍后重试。"
    
    def parse_financial_report(self, text: str) -> dict:
        prompt = f"""
        请从以下财报文本中提取关键财务数据，并以JSON格式返回：
        
        文本内容：
        {text[:5000]}
        
        需要提取的字段：
        - company_name: 公司名称
        - stock_code: 股票代码
        - report_period: 报告期（格式：YYYY-MM-DD）
        - revenue: 营收（单位：万元）
        - net_profit: 净利润（单位：万元）
        - cash_flow: 经营现金流（单位：万元）
        - debt_ratio: 负债率（百分比）
        - gross_margin: 毛利率（百分比）
        
        如果某个字段无法识别，请返回null。
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是一个专业的财务数据提取助手，请从文本中提取财务数据并以JSON格式返回。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return {}
