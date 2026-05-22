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
    
    def natural_language_query(self, query: str) -> str:
        prompt = f"""
        请分析用户的问题并提供专业的财务分析回答：
        
        用户问题：{query}
        
        请用专业但易懂的语言回答，包括相关财务指标和分析建议。
        如果涉及具体公司，请提供行业背景和参考数据。
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是一个专业的金融分析师和投资顾问，请用专业但易懂的语言回答用户的问题。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"无法处理您的问题，请稍后重试。"
    
    def analyze_with_methodology(self, data: dict) -> str:
        prompt = f"""
        请根据以下财务数据，使用专业的财务分析方法论进行全面分析：
        
        财务数据：
        {data}
        
        请按照以下结构输出分析报告：
        1. 核心财务指标分析（营收、净利润、现金流）
        2. 盈利能力分析（毛利率、净利率、ROE、ROA）
        3. 偿债能力分析（资产负债率、流动比率、速动比率）
        4. 运营能力分析（应收账款周转、存货周转）
        5. 综合评价与投资建议
        
        请用JSON格式返回，包含analysis_summary、key_findings和suggestions字段。
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是一个专业的CFA持证人，擅长财务报表分析。请用专业方法论进行分析。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return '{"analysis_summary": "分析失败", "key_findings": [], "suggestions": ["请稍后重试"]}'
    
    def compare_reports(self, reports: list) -> str:
        prompt = f"""
        请对比以下多期财报数据：
        
        财报数据：
        {reports}
        
        请分析：
        1. 同比变化（增长率、变化趋势）
        2. 关键指标对比
        3. 趋势分析与预测
        
        请用JSON格式返回，包含comparison_summary、growth_rates和trend_analysis字段。
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是一个专业的财务分析师，擅长财报对比分析。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return '{"comparison_summary": "对比失败", "growth_rates": {}, "trend_analysis": "请稍后重试"}'
    
    def industry_benchmark(self, company_name: str) -> str:
        prompt = f"""
        请分析以下公司的行业对标情况：
        
        公司名称：{company_name}
        
        请提供：
        1. 所属行业及行业特点
        2. 主要竞争对手
        3. 行业平均财务指标对比
        4. 公司在行业中的定位和竞争力分析
        
        请用JSON格式返回，包含industry、competitors、benchmark_data和competitive_position字段。
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是一个行业分析专家，熟悉各行业的竞争格局和财务指标。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return '{"industry": "未知", "competitors": [], "benchmark_data": {}, "competitive_position": "分析失败"}'
