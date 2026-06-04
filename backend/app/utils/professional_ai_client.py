import os
import json
import logging
from typing import Optional, Dict, Any
from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class ProfessionalAIClient:
    """
    专业级AI财务分析客户端
    
    特性：
    - 真实OpenAI API调用（支持GPT-3.5/4）
    - 专业Prompt Engineering
    - 结构化JSON输出保证
    - 智能错误处理与降级
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # 默认使用免费版GPT-3.5
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"✅ AI客户端初始化成功 | Model: {self.model}")
        else:
            self.client = None
            logger.warning("⚠️ 未配置OPENAI_API_KEY，将使用模拟数据")
    
    def analyze_financial_report_v2(self, 
                                   pdf_text: str, 
                                   chunks_info: Optional[Dict] = None) -> Dict[str, Any]:
        """
        专业财报分析 - 完整版V2
        
        Args:
            pdf_text: PDF完整文本内容
            chunks_info: 分块信息元数据
            
        Returns:
            标准化的结构化JSON分析结果
        """
        
        if not self.client:
            logger.warning("API未配置，返回模拟分析结果")
            return self._generate_fallback_analysis(pdf_text)
        
        try:
            # 阶段1: 提取核心财务数据
            logger.info("[阶段1] 开始提取核心财务数据...")
            financial_data = self._extract_financial_data(pdf_text)
            
            if not financial_data or "error" in financial_data:
                raise Exception(f"财务数据提取失败: {financial_data}")
            
            # 阶段2: 生成专业分析报告
            logger.info("[阶段2] 生成投资分析报告...")
            analysis_report = self._generate_analysis_report(financial_data, pdf_text)
            
            if not analysis_report:
                raise Exception("分析报告生成失败")
            
            # 合并最终结果
            final_result = {
                **financial_data,
                "analysis_report": analysis_report,
                "metadata": {
                    "analysis_model": self.model,
                    "analysis_method": "two_phase_extraction",
                    "text_length": len(pdf_text),
                    "chunks_processed": chunks_info.get("total_chunks", 1) if chunks_info else 1,
                    "confidence_score": self._calculate_confidence(financial_data)
                }
            }
            
            logger.info(f"[✅ 完成] 财报分析完成 | 置信度: {final_result['metadata']['confidence_score']}%")
            return final_result
            
        except Exception as e:
            logger.error(f"[❌ 错误] AI分析失败: {str(e)}")
            return {
                "error": str(e),
                "fallback_data": self._generate_fallback_analysis(pdf_text)
            }
    
    def _extract_financial_data(self, text: str) -> Optional[Dict]:
        """阶段1: 提取结构化财务数据"""
        
        prompt = f"""你是一位专业的财务分析师。请从以下年报文本中提取关键财务信息，并以严格的JSON格式返回。

【提取要求】
1. 提取公司基本信息（名称、股票代码、报告期等）
2. 提取三大财务报表的核心数据：
   - 资产负债表（总资产、总负债、股东权益、货币资金、存货等）
   - 利润表（营业收入、营业成本、净利润、EBITDA等）
   - 现金流量表（经营现金流、投资现金流、筹资现金流）
3. 计算关键财务指标：
   - 盈利能力：毛利率、净利率、ROE、ROA、EPS
   - 偿债能力：资产负债率、流动比率、速动比率
   - 运营能力：存货周转率、应收账款周转率、总资产周转率
4. 识别同比变化（营收增长率、净利润增长率等）

【重要】
- 所有金额单位统一为"亿元"
- 百分比保留2位小数
- 如果某些数据无法从文本中找到，标记为null
- 必须返回有效的JSON格式

【年报文本】（前20000字符）：
{text[:20000]}

请直接返回JSON，不要包含其他文字说明：
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是专业的财务数据提取专家，必须严格按JSON格式输出。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 低温度确保准确性
                max_tokens=4000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 清理可能的markdown标记
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            # 解析JSON
            data = json.loads(result_text)
            
            # 标准化字段名
            standardized = self._standardize_financial_data(data)
            
            logger.info(f"[✅ 成功] 财务数据提取完成，包含{len(standardized)}个字段")
            return standardized
            
        except json.JSONDecodeError as e:
            logger.error(f"[JSON解析错误] {e}\n原始响应:\n{result_text[:500]}")
            return {"error": f"JSON解析失败: {str(e)}"}
        except Exception as e:
            logger.error(f"[API调用错误] {e}")
            return {"error": str(e)}
    
    def _generate_analysis_report(self, financial_data: Dict, original_text: str) -> Optional[Dict]:
        """阶段2: 基于提取的数据生成专业分析报告"""
        
        # 准备摘要数据用于分析
        summary_for_analysis = json.dumps(financial_data, ensure_ascii=False, indent=2)[:3000]
        
        prompt = f"""基于以下提取的财务数据，撰写一份专业的投资分析报告（约1000字）。

【财务数据摘要】
{summary_for_analysis}

【要求】
请生成包含以下部分的分析报告（JSON格式）：

1. **executive_summary** (200字): 执行摘要
   - 公司整体表现概述
   - 关键亮点和不足
   - 总体评价

2. **financial_health_analysis** (250字): 财务健康度分析
   - 盈利能力评估（毛利率、净利率、ROE水平及变化趋势）
   - 财务结构稳健性（负债率、流动性）
   - 现金流质量（经营现金流是否充裕）

3. **business_performance_review** (250字): 经营业绩回顾
   - 主营业务收入增长情况
   - 成本控制能力
   - 与行业对比的竞争力

4. **investment_outlook** (200字): 投资展望
   - 未来增长驱动因素
   - 潜在风险点
   - 投资价值判断

5. **risk_factors**: 风险因素列表
   - [{"risk": "风险描述", "impact": "高/中/低", "probability": "高/中/低"}]

6. **investment_recommendation**: 投资建议
   - rating: "强烈推荐/推荐/中性/回避/强烈回避" + 星级(⭐1-5)
   - target_price_range: "目标价区间"
   - time_horizon: "建议持有期限"
   - rationale: "核心理由(150字以内)"

【风格要求】
- 专业但不晦涩，适合个人投资者阅读
- 数据驱动，每个结论都要有数据支撑
- 客观中立，既指出优势也不回避风险
- 语言简洁有力，避免空话套话

请直接返回JSON格式：
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位资深投资分析师，擅长撰写清晰专业的分析报告。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # 适度创造性
                max_tokens=3000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 清理JSON
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            report = json.loads(result_text)
            
            logger.info("[✅ 成功] 分析报告生成完成")
            return report
            
        except Exception as e:
            logger.error(f"[报告生成错误] {e}")
            return None
    
    def _standardize_financial_data(self, raw_data: Dict) -> Dict:
        """标准化财务数据字段"""
        
        standardized = {
            "report_metadata": {
                "company_name": raw_data.get("company_name") or raw_data.get("公司名称", "未知"),
                "stock_code": raw_data.get("stock_code") or raw_data.get("股票代码"),
                "report_type": raw_data.get("report_type") or raw_data.get("报告类型", "年度报告"),
                "report_period": raw_data.get("report_period") or raw_data.get("报告期间"),
                "data_source": "AI-GPT提取",
                "extraction_timestamp": __import__("datetime").datetime.now().isoformat()
            },
            
            "basic_info": {
                "company_overview": raw_data.get("company_overview") or raw_data.get("公司概况"),
                "main_business": raw_data.get("main_business") or raw_data.get("主营业务"),
                "industry_classification": raw_data.get("industry") or raw_data.get("所属行业")
            },
            
            "financial_statements": {
                "balance_sheet": {
                    "total_assets": raw_data.get("total_assets") or raw_data.get("总资产"),
                    "total_liabilities": raw_data.get("total_liabilities") or raw_data.get("总负债"),
                    "shareholders_equity": raw_data.get("shareholders_equity") or raw_data.get("股东权益"),
                    "cash_and_equivalents": raw_data.get("cash") or raw_data.get("货币资金"),
                    "inventory": raw_data.get("inventory") or raw_data.get("存货"),
                    "fixed_assets": raw_data.get("fixed_assets") or raw_data.get("固定资产")
                },
                
                "income_statement": {
                    "total_revenue": raw_data.get("revenue") or raw_data.get("营业收入"),
                    "operating_cost": raw_data.get("operating_cost") or raw_data.get("营业成本"),
                    "net_profit": raw_data.get("net_profit") or raw_data.get("净利润"),
                    "ebitda": raw_data.get("ebitda"),
                    "year_over_year": {
                        "revenue_growth": raw_data.get("revenue_growth") or raw_data.get("营收增长率"),
                        "profit_growth": raw_data.get("profit_growth") or raw_data.get("净利润增长率")
                    }
                },
                
                "cash_flow": {
                    "operating_cash_flow": raw_data.get("ocf") or raw_data.get("经营活动现金流"),
                    "investing_cash_flow": raw_data.get("icf") or raw_data.get("投资活动现金流"),
                    "financing_cash_flow": raw_data.get("fcf") or raw_data.get("筹资活动现金流"),
                    "free_cash_flow": raw_data.get("free_cash_flow") or raw_data.get("自由现金流")
                }
            },
            
            "key_metrics": {
                "profitability": {
                    "gross_margin": raw_data.get("gross_margin") or raw_data.get("毛利率"),
                    "net_margin": raw_data.get("net_margin") or raw_data.get("净利率"),
                    "roe": raw_data.get("roe") or raw_data.get("净资产收益率"),
                    "roa": raw_data.get("roa") or raw_data.get("总资产收益率"),
                    "eps": raw_data.get("eps") or raw_data.get("每股收益")
                },
                
                "solvency": {
                    "debt_ratio": raw_data.get("debt_ratio") or raw_data.get("资产负债率"),
                    "current_ratio": raw_data.get("current_ratio") or raw_data.get("流动比率")
                },
                
                "growth": {
                    "revenue_growth_yoy": raw_data.get("revenue_growth"),
                    "profit_growth_yoy": raw_data.get("profit_growth")
                }
            }
        }
        
        return standardized
    
    def _calculate_confidence(self, data: Dict) -> int:
        """计算数据置信度评分(0-100)"""
        score = 100
        
        critical_fields = [
            ("revenue", data.get("financial_statements", {}).get("income_statement", {}).get("total_revenue")),
            ("net_profit", data.get("financial_statements", {}).get("income_statement", {}).get("net_profit")),
            ("gross_margin", data.get("key_metrics", {}).get("profitability", {}).get("gross_margin")),
        ]
        
        for field_name, value in critical_fields:
            if value is None or value == "":
                score -= 15
                logger.warning(f"关键字段缺失: {field_name}, 置信度-15")
        
        return max(0, min(100, score))
    
    def _generate_fallback_analysis(self, text: str) -> Dict:
        """降级方案：当API不可用时生成基础分析"""
        logger.warning("⚠️ 使用降级分析模式（基于规则的简单提取）")
        
        import re
        
        # 尝试从文本中提取基础数字
        revenue_match = re.search(r'营业收入[^0-9]*([0-9,.]+)\s*亿', text)
        profit_match = re.search(r'净利润[^0-9]*([0-9,.]+)\s*亿', text)
        
        return {
            "report_metadata": {
                "company_name": "待确认",
                "data_source": "规则提取(Fallback)",
                "confidence_score": 30,
                "note": "API不可用，仅提取了少量基础数据"
            },
            "basic_info": {},
            "financial_statements": {
                "income_statement": {
                    "total_revenue": revenue_match.group(1) if revenue_match else None,
                    "net_profit": profit_match.group(1) if profit_match else None
                }
            },
            "key_metrics": {},
            "analysis_report": {
                "executive_summary": "⚠️ 当前为演示模式，未连接到AI服务。完整的智能分析需要配置有效的OpenAI API Key。",
                "investment_recommendation": {
                    "rating": "N/A ⭐",
                    "rationale": "请检查环境变量 OPENAI_API_KEY 是否正确配置。"
                }
            },
            "fallback_mode": True
        }

# 兼容旧接口
AIClient = ProfessionalAIClient
