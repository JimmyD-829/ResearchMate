import hashlib
import random
from datetime import datetime, timedelta
from typing import List, Dict

class NewsGenerator:
    INDUSTRIES = {
        "金融": {
            "keywords": ["营收", "净利润", "资产", "不良率", "资本充足率", "贷款", "存款", "理财", "保险", "证券"],
            "events": [
                "发布{year}年业绩报告，营收达{revenue}亿元",
                "宣布新一轮融资计划，规模达{amount}亿元",
                "获监管部门批准开展{business}业务",
                "与{partner}达成战略合作协议",
                "数字化转型取得重大进展，线上业务增长{growth}%",
                "发布ESG报告，绿色金融产品规模突破{amount}亿",
                "国际业务拓展至{region}市场",
                "金融科技子公司完成{amount}亿元融资",
                "不良贷款率降至{rate}%，资产质量持续改善",
                "推出面向{target}的创新金融产品"
            ],
            "sources": ["21世纪经济报道", "财新网", "上海证券报", "证券时报", "第一财经", "中国证券报"]
        },
        "制造": {
            "keywords": ["产能", "订单", "出口", "研发", "技术", "供应链", "智能制造", "新能源", "芯片", "材料"],
            "events": [
                "{quarter}季度订单量同比增长{growth}%",
                "新建{location}生产基地，总投资{amount}亿元",
                "成功研发{product}技术，打破国外垄断",
                "获得{client}大额订单，合同金额{amount}亿元",
                "出口业务增长{growth}%，主要销往{region}",
                "启动IPO计划，拟募资{amount}亿元",
                "与{partner}建立联合实验室",
                "智能制造升级项目投产，效率提升{growth}%",
                "新能源汽车零部件订单暴增{growth}%",
                "荣获国家科技进步奖，{product}技术领先"
            ],
            "sources": ["界面新闻", "每日经济新闻", "经济观察报", "华夏时报", "时代周报"]
        },
        "科技": {
            "keywords": ["AI", "算法", "云服务", "大数据", "用户增长", "生态", "创新", "专利", "芯片", "5G"],
            "events": [
                "发布新一代{product}，性能提升{growth}%",
                "用户数突破{number}亿，月活增长{growth}%",
                "开源{project}项目，推动行业技术进步",
                "获得{amount}亿美元战略投资",
                "AI大模型能力再升级，参数量达{number}亿",
                "云计算业务收入增长{growth}%，市场份额提升",
                "与{partner}共建{field}生态",
                "发布{number}项新专利，技术创新能力突出",
                "国际版图扩张，进入{region}市场",
                "元宇宙/数字人业务商业化落地"
            ],
            "sources": ["36氪", "虎嗅网", "钛媒体", "雷锋网", "量子位", "机器之心"]
        },
        "消费": {
            "keywords": ["品牌", "渠道", "消费升级", "新品", "市场份额", "电商", "直播", "国潮", "Z世代", "下沉市场"],
            "events": [
                "新品{product}上市首日销量破{number}万件",
                "线上渠道销售额增长{growth}%，直播带货贡献突出",
                "品牌年轻化战略成效显著，Z世代用户占比达{rate}%",
                "拓展{channel}渠道，门店数量突破{number}家",
                "国潮系列产品受到热捧，销量同比增长{growth}%",
                "布局下沉市场，三四线城市增速达{growth}%",
                "与IP{ip}联名，跨界营销引发热议",
                "可持续发展理念融入产品线，环保系列受追捧",
                "海外业务增长{growth}%，全球化布局加速",
                "数字化转型成果显著，会员数突破{number}万"
            ],
            "sources": ["联商网", "赢商网", "北京商报", "新京报", "澎湃新闻"]
        },
        "能源": {
            "keywords": ["新能源", "光伏", "风电", "储能", "碳中和", "绿电", "装机容量", "发电量", "转型", "减排"],
            "events": [
                "新增装机容量达{capacity}GW，同比增长{growth}%",
                "储能项目并网发电，规模居行业前列",
                "发布碳中和路线图，2030年前实现{goal}",
                "绿电交易量增长{growth}%，清洁能源占比提升",
                "海外光伏项目落地{region}，国际化步伐加快",
                "氢能业务取得突破性进展",
                "与{partner}签署长期能源供应协议",
                "研发投入占营收{rate}%，技术创新驱动发展",
                "碳减排效果显著，年度减少排放{amount}万吨",
                "智能电网建设项目投产，运营效率提升{growth}%"
            ],
            "sources": ["能源杂志", "中国能源报", "电力新闻网", "新能源网"]
        },
        "医疗": {
            "keywords": ["创新药", "临床", "审批", "研发", "医疗器械", "疫苗", "集采", "医保", "生物药", "基因治疗"],
            "events": [
                "创新药{drug}获批上市，填补国内空白",
                "III期临床试验结果积极，疗效显著优于对照组",
                "研发管线丰富，{number}款新药处于不同阶段",
                "医疗器械产品获FDA认证，进军国际市场",
                "集采中标，多款药品降价幅度超{rate}%",
                "与跨国药企{partner}达成授权合作",
                "生物药基地投产，产能大幅提升",
                "mRNA疫苗技术平台建设完成",
                "数字化医疗解决方案推广，覆盖{number}家医院",
                "基因检测业务快速增长，精准医疗布局完善"
            ],
            "sources": ["健康界", "医学界", "丁香园", "动脉网", "亿欧大健康"]
        },
        "房地产": {
            "keywords": ["销售", "拿地", "去库存", "交付", "物业", "商业地产", "租赁", "城市更新", "REITs", "转型"],
            "events": [
                "{quarter}月销售额达{amount}亿元，环比增长{growth}%",
                "新增土地储备{area}万平方米，聚焦核心城市",
                "去库存成效显著，存货周转率提升",
                "高品质交付{number}套房源，客户满意度创新高",
                "物业管理面积突破{area}万平米",
                "商业地产租金收入稳定，出租率达{rate}%",
                "探索REITs发行，盘活存量资产",
                "城市更新项目启动，老旧小区改造推进",
                "转型轻资产模式，代建业务增长{growth}%",
                "绿色建筑认证项目增加，ESG评级提升"
            ],
            "sources": ["观点地产网", "房天下", "乐居财经", "中国房地产报"]
        },
        "交通": {
            "keywords": ["运力", "航线", "物流", "快递", "港口", "航空", "高铁", "自动驾驶", "智慧交通", "冷链"],
            "events": [
                "新增{route}航线/线路，运力提升{growth}%",
                "物流网络覆盖{number}个城市，时效提速",
                "港口吞吐量创历史新高，同比增长{growth}%",
                "自动驾驶技术测试里程突破{number}公里",
                "冷链物流体系建设加快，生鲜配送时效提升",
                "与{partner}战略合作，共建智慧交通生态",
                "绿色交通工具投放，碳排放降低{rate}%",
                "国际货运业务增长{growth}%，跨境电商物流发力",
                "数字化调度系统上线，运营效率提升{growth}%",
                "多式联运体系完善，一站式服务能力增强"
            ],
            "sources": ["运输人网", "物流指闻", "民航资源网", "高铁网"]
        },
        "新能源": {
            "keywords": ["储能", "光伏", "风电", "锂电池", "新能源车", "充电桩", "氢能", "碳中和", "清洁能源", "宁德时代"],
            "events": [
                "{quarter}季度储能系统出货量达{capacity}GWh，同比增长{growth}%",
                "新一代{product}电池量产下线，能量密度提升{growth}%",
                "光伏组件转换效率突破{rate}%，刷新行业纪录",
                "获得{client}{amount}GWh储能订单，合同金额超百亿",
                "海外{region}工厂投产，国际化布局加速推进",
                "固态电池研发取得重大进展，安全性大幅提升",
                "充电网络覆盖{number}个城市，服务用户超{number}万",
                "与{partner}共建新能源汽车换电生态",
                "绿氢项目落地{location}，年产能达{capacity}万吨",
                "碳足迹认证通过，产品获欧盟市场准入"
            ],
            "sources": ["中国能源报", "新能源网", "储能网", "光伏头条", "电动汽车观察家"]
        },
        "半导体": {
            "keywords": ["芯片", "集成电路", "晶圆", "光刻机", "EDA", "半导体材料", "先进封装", "AI芯片", "中芯国际"],
            "events": [
                "{nm}nm制程良率提升至{rate}%，产能爬坡顺利",
                "自主研发的{product}芯片流片成功，性能对标国际一线",
                "宣布投资{amount}亿元建设{nm}nm晶圆厂",
                "与{partner}达成深度合作，共同开发下一代芯片",
                "汽车芯片出货量暴增{growth}%，缺芯问题缓解",
                "先进封装技术实现突破，Chiplet方案量产在即",
                "AI训练芯片算力提升{growth}%，能效比行业领先",
                "半导体设备国产化率达{rate}%，供应链安全增强",
                "获得{number}项核心专利，构建技术护城河",
                "第三季度营收达{amount}亿元，创历史新高"
            ],
            "sources": ["半导体行业观察", "电子工程专辑", "集微网", "全球半导体观察", "芯片之家"]
        },
        "教育": {
            "keywords": ["在线教育", "K12", "职业教育", "素质教育", "留学", "考研", "公考", "技能培训", "AI教育", "新东方"],
            "events": [
                "推出AI驱动的{product}学习系统，学习效率提升{growth}%",
                "{quarter}季度营收达{amount}亿元，付费用户增长{growth}%",
                "与{partner}合作，共同打造{field}人才培养体系",
                "职业培训业务拓展至{number}个城市，就业率达{rate}%",
                "上线元宇宙教学平台，沉浸式体验获好评",
                "考研/公考培训学员人数突破{number}万，市占率第一",
                "素质教育课程体系升级，STEAM教育受家长青睐",
                "国际教育业务恢复，留学咨询量增长{growth}%",
                "企业内训解决方案签约{number}家企业客户",
                "发布年度教育行业白皮书，洞察未来趋势"
            ],
            "sources": ["芥末堆看教育", "多知网", "蓝鲸EDU", "中国教育报", "鲸媒体"]
        },
        "文化传媒": {
            "keywords": ["影视", "游戏", "动漫", "直播", "短视频", "IP运营", "广告", "出版", "体育", "腾讯音乐"],
            "events": [
                "自研游戏{product}全球收入突破{amount}亿美元，MAU超{number}亿",
                "影视作品{title}播放量破{number}亿，口碑票房双丰收",
                "短视频平台日活用户达{number}亿，创作者生态繁荣",
                "与{ip}达成IP授权合作，衍生品市场空间广阔",
                "元宇宙演唱会成功举办，线上观众超{number}万",
                "数字藏品(NFT)平台上线，首期发售秒罄",
                "电竞战队夺得世界冠军，品牌价值飙升",
                "AIGC工具赋能内容生产，效率提升{growth}%",
                "海外发行收入增长{growth}%，文化出海成效显著",
                "体育赛事版权运营创新，商业化模式多元化"
            ],
            "sources": ["娱乐资本论", "三文娱", "新文化商业", "传媒内参", "游戏葡萄"]
        }
    }

    @staticmethod
    def _get_industry(company_name: str) -> str:
        name_lower = company_name.lower()

        if any(k in name_lower for k in ["银行", "保险", "证券", "金融", "平安", "招商", "中信", "浦发", "兴业"]):
            return "金融"
        elif any(k in name_lower for k in ["新能源", "储能", "光伏", "风电", "电池", "锂电", "宁德", "隆基", "思格", "比亚迪"]):
            return "新能源"
        elif any(k in name_lower for k in ["汽车", "制造", "万向", "格力", "美的", "海尔", "富士康"]):
            return "制造"
        elif any(k in name_lower for k in ["影视", "游戏", "动漫", "直播", "短视频", "传媒", "音乐", "字节跳动"]):
            return "文化传媒"
        elif any(k in name_lower for k in ["科技", "腾讯", "阿里", "百度", "华为", "小米", "openai", "微软", "apple", "nvidia", "meta", "字节"]):
            return "科技"
        elif any(k in name_lower for k in ["茅台", "五粮液", "消费", "零售", "京东", "拼多多", "美团", "雅虎", "亚马逊"]):
            return "消费"
        elif any(k in name_lower for k in ["能源", "电力", "石油", "石化", "煤炭", "天然气", "国家电网"]):
            return "能源"
        elif any(k in name_lower for k in ["医药", "生物", "健康", "恒瑞", "药明", "迈瑞"]):
            return "医疗"
        elif any(k in name_lower for k in ["地产", "万科", "碧桂园", "保利", "恒大"]):
            return "房地产"
        elif any(k in name_lower for k in ["交通", "物流", "快递", "航空", "铁路", "港口", "顺丰", "中通"]):
            return "交通"
        elif any(k in name_lower for k in ["半导体", "芯片", "电子", "中芯", "台积电", "高通", "英特尔"]):
            return "半导体"
        elif any(k in name_lower for k in ["教育", "新东方", "好未来", "网易有道", "培训"]):
            return "教育"
        else:
            industries = list(NewsGenerator.INDUSTRIES.keys())
            hash_val = int(hashlib.md5(company_name.encode()).hexdigest()[:4], 16)
            return industries[hash_val % len(industries)]

    @staticmethod
    def _generate_number(company_name: str, seed_type: str, min_val: int, max_val: int) -> str:
        hash_input = f"{company_name}_{seed_type}"
        hash_val = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
        random.seed(hash_val)

        if max_val >= 10000:
            return f"{random.randint(min_val, max_val):,}"
        else:
            return str(random.randint(min_val, max_val))

    @staticmethod
    def _generate_percentage(company_name: str, seed_type: str, min_val: float = -10, max_val: float = 50) -> str:
        hash_input = f"{company_name}_{seed_type}"
        hash_val = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
        random.seed(hash_val)

        value = round(random.uniform(min_val, max_val), 1)
        if value > 0:
            return f"+{value}"
        return str(value)

    @staticmethod
    def generate_news(company_name: str, count: int = 15) -> List[Dict]:
        industry = NewsGenerator._get_industry(company_name)
        industry_data = NewsGenerator.INDUSTRIES.get(industry, NewsGenerator.INDUSTRIES["科技"])

        news_list = []
        base_date = datetime.now()

        for i in range(count):
            hash_seed = f"{company_name}_news_{i}"
            hash_val = int(hashlib.md5(hash_seed.encode()).hexdigest()[:8], 16)
            random.seed(hash_val)

            days_ago = random.randint(0, 30)
            news_date = base_date - timedelta(days=days_ago)

            event_template = random.choice(industry_data["events"])

            event = event_template.format(
                year=2025 + random.randint(0, 1),
                quarter=random.choice(["Q1", "Q2", "Q3", "Q4"]),
                revenue=NewsGenerator._generate_number(company_name, f"rev_{i}", 100, 5000),
                amount=NewsGenerator._generate_number(company_name, f"amt_{i}", 10, 500),
                growth=NewsGenerator._generate_percentage(company_name, f"grw_{i}", -15, 80),
                rate=round(random.uniform(1, 20), 2),
                number=NewsGenerator._generate_number(company_name, f"num_{i}", 100, 99999),
                capacity=NewsGenerator._generate_number(company_name, f"cap_{i}", 1, 50),
                area=NewsGenerator._generate_number(company_name, f"area_{i}", 10, 5000),
                product=random.choice(["智能", "新一代", "旗舰级", "创新型", "高端", "绿色"]),
                business=random.choice(["财富管理", "投资银行", "资产管理", "普惠金融", "跨境金融"]),
                partner=random.choice(["华为", "腾讯", "阿里巴巴", "字节跳动", "中国移动", "政府机构", "高校", "科研院所"]),
                region=random.choice(["东南亚", "欧洲", "北美", "中东", "非洲", "拉美", "日韩", "一带一路沿线国家"]),
                target=random.choice(["年轻人", "中小企业", "高净值人群", "Z世代", "银发族", "企业客户"]),
                channel=random.choice(["线下门店", "电商平台", "社交电商", "社区团购", "直播电商", "跨境电商"]),
                ip=random.choice(["迪士尼", "故宫", "世界杯", "奥运会", "知名艺术家"]),
                project=random.choice(["开源框架", "开发工具", "AI模型", "数据库", "操作系统"]),
                field=random.choice(["人工智能", "云计算", "区块链", "物联网", "大数据"]),
                drug=random.choice(["单抗药物", "靶向药", "免疫疗法", "细胞治疗", "基因治疗"]),
                route=random.choice(["京沪", "中欧", "中亚", "东盟", "中非"]),
                goal=random.choice(["碳达峰", "碳中和", "全面绿色转型", "零碳排放"]),
                client=random.choice(["比亚迪", "特斯拉", "苹果", "华为", "小米", "大众", "丰田", "宝马"]),
                location=random.choice(["长三角", "珠三角", "成渝", "京津冀", "中部地区", "海外"]),
                nm=random.choice([3, 5, 7, 14, 28]),
                title=random.choice(["《星际迷航》", "《未来世界》", "《科技革命》", "《商业帝国》"])
            )

            emotion_score = round(random.uniform(-30, 30), 2)
            if emotion_score > 10:
                emotion_label = "positive"
            elif emotion_score < -10:
                emotion_label = "negative"
            else:
                emotion_label = "neutral"

            source = random.choice(industry_data["sources"])
            url = f"https://example.com/news/{hash_val}"

            news_item = {
                "id": f"gen_{hash_val}",
                "company_name": company_name,
                "title": event,
                "source": source,
                "url": url,
                "publish_time": news_date.strftime("%Y-%m-%d %H:%M:%S"),
                "emotion_score": emotion_score,
                "emotion_label": emotion_label,
                "created_at": news_date.strftime("%Y-%m-%d %H:%M:%S")
            }

            news_list.append(news_item)

        news_list.sort(key=lambda x: x["publish_time"], reverse=True)

        return news_list

    @staticmethod
    def generate_news_for_companies(companies: List[str], per_company: int = 15) -> Dict[str, List[Dict]]:
        result = {}
        for company in companies:
            result[company] = NewsGenerator.generate_news(company, per_company)
        return result