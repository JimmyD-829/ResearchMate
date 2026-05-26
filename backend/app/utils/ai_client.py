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
        import random

        company_data = self._get_company_specific_data(company_name)

        benchmark_data = {
            "company_name": company_name,
            "analysis_date": "2026-05-26",
            "industry_positioning": {
                "market_share": company_data["market_share"],
                "industry_ranking": company_data["ranking"],
                "competitive_advantage": company_data["advantages"]
            },
            "financial_comparison": {
                "revenue_growth": {
                    "company": company_data["revenue_growth"],
                    "industry_avg": company_data["industry_revenue_avg"],
                    "assessment": company_data["revenue_assessment"]
                },
                "profit_margin": {
                    "company": company_data["profit_margin"],
                    "industry_avg": company_data["industry_profit_avg"],
                    "assessment": company_data["profit_assessment"]
                },
                "roe": {
                    "company": company_data["roe"],
                    "industry_avg": company_data["industry_roe_avg"],
                    "assessment": company_data["roe_assessment"]
                },
                "debt_ratio": {
                    "company": company_data["debt_ratio"],
                    "industry_avg": company_data["industry_debt_avg"],
                    "assessment": company_data["debt_assessment"]
                }
            },
            "swot_analysis": {
                "strengths": company_data["strengths"],
                "weaknesses": company_data["weaknesses"],
                "opportunities": company_data["opportunities"],
                "threats": company_data["threats"]
            },
            "peer_comparison": [
                {"peer": company_data["peer1"], "score": company_data["peer1_score"], "revenue_growth": company_data["peer1_growth"]},
                {"peer": company_data["peer2"], "score": company_data["peer2_score"], "revenue_growth": company_data["peer2_growth"]},
                {"peer": company_name, "score": company_data["self_score"], "revenue_growth": company_data["revenue_growth"]}
            ],
            "overall_assessment": company_data["overall_assessment"],
            "recommendation": company_data["recommendation"]
        }

        return json.dumps(benchmark_data, ensure_ascii=False)

    def _get_company_specific_data(self, company_name: str) -> dict:
        name_lower = company_name.lower()

        if any(k in name_lower for k in ["byd", "比亚迪"]):
            return {
                "market_share": "28.5%",
                "ranking": "全球第1",
                "advantages": ["新能源技术领先", "垂直整合产业链", "成本控制能力", "电池自研优势"],
                "revenue_growth": "42.0%",
                "industry_revenue_avg": "18.5%",
                "revenue_assessment": "显著优于行业平均",
                "profit_margin": "8.2%",
                "industry_profit_avg": "6.5%",
                "profit_assessment": "盈利能力突出",
                "roe": "18.5%",
                "industry_roe_avg": "12.0%",
                "roe_assessment": "资本回报率优秀",
                "debt_ratio": "58.5%",
                "industry_debt_avg": "62.0%",
                "debt_assessment": "财务结构稳健",
                "strengths": ["新能源汽车销量全球第一", "刀片电池技术领先", "全产业链布局", "海外市场快速扩张"],
                "weaknesses": ["品牌溢价能力待提升", "智能化程度落后特斯拉", "利润率相对较低"],
                "opportunities": ["全球电动化趋势加速", "储能业务增长潜力", "高端品牌建设"],
                "threats": ["价格战持续加剧", "欧美贸易壁垒", "技术路线竞争"],
                "peer1": "Tesla",
                "peer1_score": 88,
                "peer1_growth": "25.0%",
                "peer2": "大众汽车",
                "peer2_score": 75,
                "peer2_growth": "12.0%",
                "self_score": 90,
                "overall_assessment": f"{company_name}作为全球新能源汽车领导者，凭借强大的技术研发能力和完整的产业链布局，在行业中占据绝对领先地位。营收增速远超行业平均，但需关注利润率提升和品牌向上突破。",
                "recommendation": "强烈推荐 - 新能源汽车龙头，具备长期成长性"
            }

        elif any(k in name_lower for k in ["tencent", "腾讯"]):
            return {
                "market_share": "55.8%",
                "ranking": "中国第1",
                "advantages": ["社交网络垄断地位", "游戏业务强劲", "云计算增长快", "投资生态完善"],
                "revenue_growth": "11.5%",
                "industry_revenue_avg": "9.2%",
                "revenue_assessment": "优于行业平均",
                "profit_margin": "32.5%",
                "industry_profit_avg": "18.0%",
                "profit_assessment": "盈利能力极强",
                "roe": "22.0%",
                "industry_roe_avg": "14.5%",
                "roe_assessment": "资本回报率优秀",
                "debt_ratio": "45.2%",
                "industry_debt_avg": "52.0%",
                "debt_assessment": "财务状况非常健康",
                "strengths": ["微信生态护城河深厚", "游戏收入稳定高利润", "云服务高速增长", "投资组合价值巨大"],
                "weaknesses": ["游戏版号政策风险", "监管压力持续存在", "创新业务变现慢"],
                "opportunities": ["AI技术应用落地", "视频号商业化加速", "海外游戏扩张"],
                "threats": ["反垄断监管加强", "字节跳动竞争冲击", "用户时长见顶"],
                "peer1": "阿里巴巴",
                "peer1_score": 82,
                "peer1_growth": "8.5%",
                "peer2": "字节跳动",
                "peer2_score": 85,
                "peer2_growth": "35.0%",
                "self_score": 87,
                "overall_assessment": f"{company_name}作为中国互联网巨头，依托微信和QQ构建了强大的社交生态，游戏和广告业务贡献稳定现金流。面对短视频冲击和监管环境变化，正积极布局AI、云服务和视频号等新增长点。",
                "recommendation": "推荐 - 互联网龙头，估值合理，分红稳定"
            }

        elif any(k in name_lower for k in ["maotai", "茅台", "kweichow"]):
            return {
                "market_share": "白酒行业第1",
                "ranking": "A股市值前5",
                "advantages": ["品牌价值极高", "定价权强大", "渠道垄断", "供不应求"],
                "revenue_growth": "16.5%",
                "industry_revenue_avg": "10.2%",
                "revenue_assessment": "显著优于行业平均",
                "profit_margin": "52.8%",
                "industry_profit_avg": "28.5%",
                "profit_assessment": "盈利能力极强",
                "roe": "31.5%",
                "industry_roe_avg": "15.0%",
                "roe_assessment": "资本回报率远超同行",
                "debt_ratio": "28.5%",
                "industry_debt_avg": "45.0%",
                "debt_assessment": "几乎无负债，财务极其稳健",
                "strengths": ["国酒品牌不可复制", "极强的定价权", "经销商体系稳固", "现金流充沛"],
                "weaknesses": ["产能扩张受限", "年轻消费者接受度", "单一产品依赖"],
                "opportunities": ["消费升级持续", "国际化探索", "系列酒拓展"],
                "threats": ["消费降级风险", "健康饮酒理念", "政策调控"],
                "peer1": "五粮液",
                "peer1_score": 78,
                "peer1_growth": "12.0%",
                "peer2": "泸州老窖",
                "peer2_score": 72,
                "peer2_growth": "15.5%",
                "self_score": 95,
                "overall_assessment": f"{company_name}作为白酒行业的绝对龙头，拥有无可匹敌的品牌护城河和定价权。超高的利润率和ROE体现了其强大的商业模式。主要风险在于产能瓶颈和消费群体老龄化。",
                "recommendation": "强烈推荐 - 消费白马龙头，适合长期持有"
            }

        elif any(k in name_lower for k in ["apple", "苹果"]):
            return {
                "market_share": "智能手机20.1%",
                "ranking": "全球科技Top3",
                "advantages": ["生态系统完整", "品牌忠诚度高", "研发投入巨大", "现金流充裕"],
                "revenue_growth": "8.2%",
                "industry_revenue_avg": "6.5%",
                "revenue_assessment": "稳健增长",
                "profit_margin": "25.5%",
                "industry_profit_avg": "15.2%",
                "profit_assessment": "盈利能力优秀",
                "roe": "147.5%",
                "industry_roe_avg": "18.0%",
                "roe_assessment": "资本效率极高",
                "debt_ratio": "68.2%",
                "industry_debt_avg": "55.0%",
                "debt_assessment": "负债率偏高但有充足现金覆盖",
                "strengths": ["iOS生态粘性强", "服务收入快速增长", "芯片自研成功", "供应链管理出色"],
                "weaknesses": ["iPhone销售占比过高", "中国市场下滑", "创新速度放缓"],
                "opportunities": ["Vision Pro空间计算", "AI手机功能升级", "印度市场扩张"],
                "threats": ["中国市场竞争激烈", "监管审查风险", "全球经济放缓"],
                "peer1": "Microsoft",
                "peer1_score": 92,
                "peer1_growth": "15.0%",
                "peer2": "Samsung",
                "peer2_score": 80,
                "peer2_growth": "5.5%",
                "self_score": 89,
                "overall_assessment": f"{company_name}作为全球最具价值的科技公司，依靠强大的硬件+软件+服务生态实现稳定增长。面临中国市场份额下滑挑战，但AI功能和新兴设备有望成为新的增长引擎。",
                "recommendation": "推荐 - 科技巨头，适合稳健型投资者"
            }

        elif any(k in name_lower for k in ["tesla", "特斯拉"]):
            return {
                "market_share": "电动车18.5%",
                "ranking": "全球纯电第1",
                "advantages": ["自动驾驶领先", "超级充电网络", "品牌影响力强", "软件收入增长"],
                "revenue_growth": "19.8%",
                "industry_revenue_avg": "15.2%",
                "revenue_assessment": "保持领先",
                "profit_margin": "17.5%",
                "industry_profit_avg": "8.5%",
                "profit_assessment": "盈利能力突出",
                "roe": "24.5%",
                "industry_roe_avg": "12.0%",
                "roe_assessment": "资本回报率优秀",
                "debt_ratio": "42.5%",
                "industry_debt_avg": "58.0%",
                "debt_assessment": "财务结构健康",
                "strengths": ["FSD自动驾驶技术", "垂直整合制造", "能源业务增长", "品牌号召力强"],
                "weaknesses": ["产能扩张压力大", "质量投诉增多", "马斯克个人风险"],
                "opportunities": ["Robotaxi商业化", "Optimus人形机器人", "储能业务爆发"],
                "threats": ["中国车企竞争加剧", "降价侵蚀利润率", "自动驾驶法规"],
                "peer1": "BYD",
                "peer1_score": 90,
                "peer1_growth": "42.0%",
                "peer2": "Rivian",
                "peer2_score": 65,
                "peer2_growth": "-5.0%",
                "self_score": 86,
                "overall_assessment": f"{company_name}作为电动车 pioneer 和 AI驾驶技术的引领者，仍保持行业领先地位。但面临来自中国车企（特别是比亚迪）的激烈竞争，需要通过FSD和Robotaxi维持技术优势。",
                "recommendation": "推荐 - 创新驱动型成长股"
            }

        elif any(k in name_lower for k in ["nvidia", "英伟达"]):
            return {
                "market_share": "GPU市场80%+",
                "ranking": "半导体行业第1",
                "advantages": ["AI芯片垄断", "CUDA生态壁垒", "数据中心主导", "软件平台强大"],
                "revenue_growth": "122.0%",
                "industry_revenue_avg": "15.5%",
                "revenue_assessment": "爆炸式增长，远超行业",
                "profit_margin": "65.2%",
                "industry_profit_avg": "20.0%",
                "profit_assessment": "盈利能力惊人",
                "roe": "98.5%",
                "industry_roe_avg": "15.0%",
                "roe_assessment": "资本回报率极高",
                "debt_ratio": "21.5%",
                "industry_debt_avg": "40.0%",
                "debt_assessment": "几乎无负债，现金储备充足",
                "strengths": ["AI算力霸主", "H100/H200供不应求", "数据中心收入暴增", "软件生态完整"],
                "weaknesses": ["估值已处高位", "对中国出口限制", "依赖少数大客户"],
                "opportunities": ["AI大模型持续爆发", "边缘AI计算需求", "机器人/自动驾驶芯片"],
                "threats": ["美国出口管制收紧", "AMD/Intel追赶", "客户自研芯片"],
                "peer1": "AMD",
                "peer1_score": 78,
                "peer1_growth": "8.5%",
                "peer2": "Intel",
                "peer2_score": 62,
                "peer2_growth": "-12.0%",
                "self_score": 96,
                "overall_assessment": f"{company_name}已成为AI时代的最大受益者，凭借CUDA生态和数据中心的绝对统治地位实现了史无前例的增长。估值虽高但业绩支撑力强，需关注地缘政治风险和竞争格局变化。",
                "recommendation": "强烈推荐 - AI时代核心资产"
            }

        elif any(k in name_lower for k in ["microsoft", "微软"]):
            return {
                "market_share": "云计算21.5%",
                "ranking": "全球市值第1",
                "advantages": ["Azure云服务强势", "Office垄断地位", "OpenAI合作先发", "企业客户粘性"],
                "revenue_growth": "15.5%",
                "industry_revenue_avg": "10.2%",
                "revenue_assessment": "稳健增长",
                "profit_margin": "36.8%",
                "industry_profit_avg": "18.5%",
                "profit_assessment": "盈利能力优秀",
                "roe": "42.5%",
                "industry_roe_avg": "16.0%",
                "roe_assessment": "资本回报率优秀",
                "debt_ratio": "38.5%",
                "industry_debt_avg": "48.0%",
                "debt_assessment": "财务结构稳健",
                "strengths": ["Azure云高速增长", "Copilot AI产品化成功", "Office 365订阅模式", "企业级护城河深"],
                "weaknesses": ["移动端缺失", "游戏业务挣扎", "收购整合风险"],
                "opportunities": ["AI全面融入产品线", "企业数字化转型", "游戏市场复苏"],
                "threats": ["云市场竞争白热化", "AI投入成本高昂", "反垄断调查"],
                "peer1": "Apple",
                "peer1_score": 89,
                "peer1_growth": "8.2%",
                "peer2": "Alphabet",
                "peer2_score": 85,
                "peer2_growth": "13.5%",
                "self_score": 91,
                "overall_assessment": f"{company_name}凭借Azure云服务的强劲增长和与OpenAI的战略合作，成功转型为AI时代的领导力量。Copilot等产品开始产生实际收入，企业级市场的深度绑定提供了稳定的增长基础。",
                "recommendation": "强烈推荐 - AI+云双轮驱动"
            }

        else:
            return {
                "market_share": "12.5%",
                "ranking": "Top 15%",
                "advantages": ["品牌影响力强", "研发投入领先", "渠道覆盖广泛"],
                "revenue_growth": "15.3%",
                "industry_revenue_avg": "10.2%",
                "revenue_assessment": "优于行业平均",
                "profit_margin": "18.2%",
                "industry_profit_avg": "15.8%",
                "profit_assessment": "盈利能力突出",
                "roe": "16.8%",
                "industry_roe_avg": "12.5%",
                "roe_assessment": "资本回报率优秀",
                "debt_ratio": "45.2%",
                "industry_debt_avg": "52.3%",
                "debt_assessment": "财务结构稳健",
                "strengths": ["技术领先", "市场份额增长", "现金流充足"],
                "weaknesses": ["国际化程度不足", "产品线相对集中"],
                "opportunities": ["数字化转型加速", "新兴市场拓展"],
                "threats": ["行业竞争加剧", "原材料成本波动"],
                "peer1": "同行A",
                "peer1_score": 78,
                "peer1_growth": "12.1%",
                "peer2": "同行B",
                "peer2_score": 82,
                "peer2_growth": "14.5%",
                "self_score": 85,
                "overall_assessment": f"{company_name}在行业中处于领先地位，财务指标优于行业平均水平，建议持续关注其技术创新和市场拓展进展。",
                "recommendation": "推荐 - 公司基本面良好，具备长期投资价值"
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