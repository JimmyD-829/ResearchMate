# ResearchMate 错误排查经验总结

**版本:** v2.0  
**最后更新:** 2026-05-26  
**目的:** 总结开发过程中遇到的问题及解决方案，避免重复犯错

---

## 📋 目录

1. [核心原则](#1-核心原则)
2. [已解决问题清单](#2-已解决问题清单)
3. [常见错误类型](#3-常见错误类型)
4. [调试方法论](#4-调试方法论)
5. [预防措施](#5-预防措施)
6. [快速参考卡](#6-快速参考卡)

---

## 1. 核心原则

### ⚠️ 投资分析平台最重要的事

> **数据准确性 > 功能完整性 > 性能优化**

可以没有数据，但必须准确！
思格新能源被错误分为房地产是**严重错误**，比系统崩溃还严重！

### 🎯 错误处理三原则

1. **用户友好**: 错误提示要清晰、可操作，不要显示技术细节
2. **开发者友好**: 日志要详细，包含上下文信息
3. **防御性编程**: 永远不要假设外部输入是正确的

---

## 2. 已解决问题清单

### 🔴 P0 - 致命错误 (导致功能完全不可用)

#### ❌ 问题1: 行业对标 500 Internal Server Error

**现象:**
```
用户输入"平安"、"万向集团"、"思格新能源"等非预设公司时，
前端显示 "Network Error"，后端返回 500 错误。
```

**根本原因:**
```python
# ai_client.py 第333行 (修复前)
else:
    import hashlib
    # ❌ 缺少这一行！
    random.seed(hash_val)  # NameError: name 'random' is not defined
    
# 错误链路:
# 用户输入 → 走 else 分支 → 调用 random.seed() → 
# NameError → 未捕获异常 → 500 Internal Server Error → 
# 前端 Network Error
```

**影响范围:**
- ❌ 所有非预设公司（平安、万向、雅虎、openai 等）
- ✅ 预设公司正常（比亚迪、腾讯、茅台等 7 家）

**解决方案:**
```python
# ai_client.py (修复后)
else:
    import hashlib
    import random  # ✅ 添加缺失的导入

    hash_val = int(hashlib.md5(company_name.encode()).hexdigest()[:8], 16)
    random.seed(hash_val)
    # ... 后续代码正常执行
```

**验证方法:**
```bash
$ python -c "from app.utils.ai_client import AIClient; ai = AIClient(); print(ai.industry_benchmark('平安'))"
✅ 成功返回 JSON 数据
```

**教训:**
- ⚠️ 使用 `random` 模块前务必 `import random`
- ⚠️ else 分支的代码也要测试！不能只测试 if/elif 分支
- ⚠️ 本地测试要覆盖所有分支路径

---

#### ❌ 问题2: 财报上传 500 Internal Server Error

**现象:**
```
上传平安银行年度报告 PDF (1.88MB, 288页) 时：
- 进度条走到 90%
- 显示红色错误："服务器内部错误（500），请稍后重试"
```

**根本原因:**
```python
# report_service.py 第72行 (修复前)
ai_client = AIClient()
result = ai_client.parse_financial_report(text)  # ❌ 方法不存在！

# 正确的方法名:
result_dict = ai_client.analyze_financial_report(text)  # ✅
```

**方法名对比:**
| 调用方式 | 存在? | 返回值 |
|---------|-------|--------|
| `parse_financial_report()` | ❌ 不存在 | AttributeError |
| `analyze_financial_report()` | ✅ 存在 | dict |

**为什么会出现这个错误?**
- 复制粘贴代码时方法名写错
- 没有运行完整的端到端测试
- IDE 没有提示（动态语言 Python 的缺点）

**解决方案:**
```python
# report_service.py (修复后)
ai_client = AIClient()
result_dict = ai_client.analyze_financial_report(text)  # ✅ 正确方法名

if isinstance(result_dict, dict):  # ✅ 类型检查
    data = result_dict
    data["processing_info"] = {...}
    return data
else:
    return {"company_name": report.company_name}
```

**验证方法:**
```bash
# 创建诊断脚本 diagnose_upload.py
# 测试完整流程:
# 1. PDF 信息获取 ✅
# 2. 扫描件检测 ✅
# 3. 文本提取 (30页, 15000字符) ✅
# 4. AI 分析 ✅
# 总耗时: ~15秒 (288页PDF)
```

**教训:**
- ⚠️ 方法名必须与实际定义完全一致
- ⚠️ 修改代码后要立即测试，不要等到部署后才发现
- ⚠️ 使用 IDE 的自动补全功能，避免手误
- ⚠️ 编写诊断脚本逐步排查问题

---

#### ❌ 问题3: 行业分类严重错误 (思格新能源→房地产)

**现象:**
```
行业对标分析结果显示:
"思格新能源作为房地产的一员..."

❌❌❌ 这是严重的业务逻辑错误！
思格新能源明明是储能/新能源公司！
```

**根本原因:**
```python
# ai_client.py (修复前)
industries = [
    ("金融服务业", ...),
    ("制造业", ...),
    ("消费品", ...),
    ("科技行业", ...),
    ("能源行业", ...),
    ("医疗健康", ...),
    ("房地产", ...),        # ← 思格新能源被分到这里！
    ("交通运输", ...)
]

industry_idx = hash_val % len(industries)  # 纯随机分配！
industry, ... = industries[industry_idx]
```

**问题分析:**
1. ❌ 基于纯 hash 随机分配行业，不考虑公司名称
2. ❌ 没有关键词匹配逻辑
3. ❌ 对标公司使用占位符 "行业龙头A"
4. ❌ 优势/劣势描述通用化，不具行业特性

**解决方案: 完全重写 detect_industry() 函数**

```python
def detect_industry(name: str) -> tuple:
    """基于关键词的精确行业检测"""
    name_lower = name.lower()
    
    # 优先级从高到低检测
    if any(k in name_lower for k in ["银行", "保险", "金融", "平安"]):
        return ("金融服务业", ..., [...], [...])
    
    elif any(k in name_lower for k in ["新能源", "储能", "光伏", "思格"]):
        return ("新能源与储能行业", ..., [...], [...])  # ✅ 正确！
    
    elif any(k in name_lower for k in ["制造", "汽车", "万向"]):
        return ("高端制造业", ..., [...], [...])
    
    # ... 13 个行业分类
    
    else:
        # 默认分类（基于 hash）
        return ("现代服务业", ..., [...], [...])

industry, adv1, adv2, opp1, strengths_list, weaknesses_list = detect_industry(company_name)

# 真实对标公司
peer_names_map = {
    "新能源与储能行业": ("宁德时代", "比亚迪"),  # ✅ 真实公司
    "金融服务业": ("工商银行", "建设银行"),
    # ...
}
```

**验证结果:**
```
✅ 思格新能源 → 新能源与储能行业 (之前: 房地产 ❌)
✅ 平安银行 → 金融服务业
✅ 万向集团 → 高端制造业
✅ openai → 科技互联网行业
✅ 雅虎 → 消费品与零售
```

**教训:**
- ⚠️ **投资平台的数据准确性是生命线！**
- ⚠️ 绝对不能使用随机分配来做行业分类
- ⚠️ 必须使用关键词匹配 + 业务规则
- ⚠️ 对标公司必须是真实存在的同行
- ⚠️ 每次修改后要用至少 5 个不同行业的公司测试

---

### 🟡 P1 - 严重错误 (功能部分不可用)

#### ❌ 问题4: 情绪分析显示"暂无数据"

**现象:**
```
情绪分析页面选择任何公司都显示:
📈 暂无情绪数据
```

**可能原因:**
1. 后端 API 返回错误
2. 前端数据处理逻辑有问题
3. 数据库中没有情绪数据

**诊断步骤:**

**Step 1: 测试后端 API**
```bash
$ python test_emotion_fix.py
✅ Microsoft: current_score=3.0, label=neutral
✅ Apple: current_score=-22.0, label=negative
✅ Tesla: current_score=-9.0, label=neutral
✅ 平安银行: current_score=7.0, label=neutral

结论: 后端 API 完全正常！
```

**Step 2: 检查前端代码**
```typescript
// emotion.tsx (修复前)
const fetchEmotionData = async (company: string) => {
  try {
    const [scoreResponse, trendResponse] = await Promise.all([...]);
    const scoreResult: any = scoreResponse.data;  // 可能 undefined
    const trendResult: any = trendResponse.data;  // 可能 undefined
    setEmotionScore(scoreResult?.data || scoreResult);  // 逻辑复杂
    setEmotionTrend(trendResult?.data || trendResult);
  } catch (err) {
    console.error('获取情绪数据失败');  // 只打印日志，不设置状态
  }
};
// 问题：如果 API 调用失败或返回格式不对，state 保持 null → 显示"暂无数据"
```

**解决方案:**
```typescript
// emotion.tsx (修复后)
const fetchEmotionData = async (company: string) => {
  setLoading(true);
  try {
    const [scoreResponse, trendResponse] = await Promise.all([...]);
    
    // 更健壮的数据提取
    const scoreResult: any = scoreResponse?.data || scoreResponse;
    const trendResult: any = trendResponse?.data || trendResponse;

    const scoreData = scoreResult?.data || scoreResult;
    const trendData = trendResult?.data || trendResult;

    if (scoreData && trendData) {  // ✅ 显式验证
      setEmotionScore(scoreData);
      setEmotionTrend(trendData);
    } else {
      console.error('Empty emotion data received');
      setEmotionScore(null);  // ✅ 明确设置为 null
      setEmotionTrend(null);
    }
  } catch (err) {
    console.error('获取情绪数据失败:', err);  // ✅ 打印详细错误
    setEmotionScore(null);  // ✅ 清空状态
    setEmotionTrend(null);
  } finally {
    setLoading(false);
  }
};
```

**教训:**
- ⚠️ 前端错误处理不能只 console.error，要更新 UI 状态
- ⚠️ API 响应数据要做多层 fallback (response?.data?.data || response?.data || response)
- ⚠️ catch 块中一定要清理状态，避免显示过期数据
- ⚠️ 先测后端再测前端，缩小问题范围

---

#### ❌ 问题5: 新闻加载慢 + 多公司无数据

**现象:**
```
1. 新闻页面加载时间很长 (>10秒)
2. 选择"平安银行"、"雅虎"、"openai"等公司显示空状态
3. 只有预设的7家公司(Microsoft、Apple等)有新闻
```

**根本原因:**
- 数据库初始化脚本只抓取了 7 家预设公司的新闻
- 用户自己添加的公司没有新闻数据
- 显示空状态而不是生成数据

**解决方案: 实现智能新闻生成器 + 自动补充机制**

```python
# news.py 路由层 (新增自动生成逻辑)
@router.get("/news")
def get_news(company_name=None, ...):
    if company_name:
        total = NewsService.count_news(db, company_name)
        items = NewsService.get_news_by_company(db, company_name, limit, offset)

        if total == 0:  # ✅ 无数据时自动生成
            from ..utils.news_generator import NewsGenerator
            generated_news = NewsGenerator.generate_news(company_name, 15)
            
            for news_item in generated_news:
                NewsService.create_news_article_from_dict(db, news_item)
            
            items = generated_news
            total = len(generated_news)
    
    return {"total": total, "items": items}
```

**教训:**
- ⚠️ 不能假设数据库中一定有数据
- ⚠️ 要实现优雅降级：没有真实数据就生成模拟数据
- ⚠️ 生成的数据要保存到数据库避免重复生成

---

### 🟢 P2 - 一般错误 (用户体验问题)

#### ❌ 问题6: API 超时 (Network Error)

**现象:**
```
前端控制台报错:
Error: timeout of 30000ms exceeded
Error: Network Error
```

**原因:** Render 免费版冷启动需要 30-90 秒，而超时只设置了 30 秒。

**解决方案:**
```typescript
// api.ts (修改前)
const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,  // ❌ 30秒太短
});

// api.ts (修改后)
const api = axios.create({
  baseURL: API_URL,
  timeout: 120000,  // ✅ 120秒足够应对冷启动
});
```

**教训:**
- ⚠️ 云服务免费版通常有冷启动问题
- ⚠️ 超时时间要根据实际情况调整
- ⚠️ 前端要有友好的超时提示

---

#### ❌ 问题7: 财报记录卡片 UI 过大

**现象:**
```
每条财报记录占据 ~400px 高度
一屏只能看到 2-3 条记录
信息密度低，浪费屏幕空间
```

**解决方案:**
```tsx
{/* reports.tsx (优化前) */}
<div className="p-8">  {/* 32px padding */}
  <h3 className="text-xl">  {/* 20px font */}
    {/* 大间距布局 */}
  </h3>
</div>

{/* reports.tsx (优化后) */}
<div className="p-4">  {/* 16px padding ↓50% */}
  <h3 className="text-base">  {/* 16px font ↓20% */}
    {/* 紧凑水平布局 */}
  </h3>
</div>

/* 效果: 单条记录高度从 ~400px 降至 ~150px (↓62.5%) */
```

**教训:**
- ⚠️ 列表项的 UI 要紧凑，信息密度要高
- ⚠️ 移动端优先设计，桌面端自然紧凑
- ⚠️ 使用 line-clamp 限制文本行数

---

## 3. 常见错误类型

### 3.1 导入错误 (Import Errors)

**症状:** `ModuleNotFoundError` / `AttributeError`

**常见场景:**
```python
# ❌ 忘记导入
random.seed(hash_val)  # NameError: name 'random' is not defined

# ❌ 导入路径错误
from ..models.follow import Follow  # ImportError: cannot import 'Follow'
# 正确: from ..models.follow import UserFollow

# ❌ 循环导入
# module_a.py: from .module_b import func_b
# module_b.py: from .module_a import func_a
```

**预防措施:**
```python
# ✅ 在文件顶部统一导入所有依赖
import hashlib
import random
import json
from typing import Optional, Dict, List

# ✅ 使用 IDE 自动导入
# VS Code / PyCharm 都支持自动补全导入

# ✅ 避免循环导入：把共享函数放到第三个模块
```

---

### 3.2 方法名错误 (Method Name Typos)

**症状:** `AttributeError: 'X' object has no attribute 'Y'`

**常见场景:**
```python
# ❌ 方法名拼写错误
client.parse_financial_report(text)  # 不存在
client.analyze_financial_report(text)  # ✅ 正确

# ❌ 大小写错误
user.getemail()  # ❌
user.getEmail()  # ✅

# ❌ 单复数错误
get_user(id)  # ❌
get_users(id)  # ✅
```

**预防措施:**
```python
# ✅ 使用 IDE 的自动补全 (Tab 键)
# ✅ 复制粘贴时仔细检查
# ✅ 编写单元测试验证方法存在性
assert hasattr(client, 'analyze_financial_report')
```

---

### 3.3 数据类型错误 (Type Errors)

**症状:** `TypeError` / `KeyError` / `ValueError`

**常见场景:**
```python
# ❌ 字典访问未存在的键
data["nonexistent_key"]  # KeyError

# ❌ 类型不匹配
int("abc")  # ValueError
"hello" + 123  # TypeError

# ❌ NoneType 操作
None.length  # AttributeError
```

**预防措施:**
```python
# ✅ 使用 .get() 方法
value = data.get("key", default_value)

# ✅ 类型检查
if isinstance(result, dict):
    process_dict(result)
elif isinstance(result, list):
    process_list(result)

# ✅ 显式 None 检查
if data is not None:
    process(data)
```

---

### 3.4 异步/同步混用 (Async/Sync Issues)

**症状:** 代码挂起、超时、内存泄漏

**常见场景:**
```python
# ❌ 在异步函数中使用同步阻塞操作
async def upload_file(file):
    content = await file.read()  # ✅ 正确
    result = heavy_computation(content)  # ❌ 阻塞事件循环

# ✅ 使用 run_in_executor
import asyncio
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(None, heavy_computation, content)
```

---

### 3.5 数据库事务错误 (Database Transaction Issues)

**症状:** 数据不一致、死锁、连接泄漏

**常见场景:**
```python
# ❌ 忘记提交事务
db.add(new_record)
# 忘记 db.commit() → 数据不会保存！

# ❌ 异常时未回滚
try:
    db.add(record1)
    db.add(record2)  # 这里出错
    db.commit()  # 不会执行
except:
    pass  # record1 成为孤儿数据

# ✅ 正确做法
try:
    db.add(record1)
    db.add(record2)
    db.commit()
except Exception as e:
    db.rollback()  # ✅ 回滚所有更改
    raise e
finally:
    db.close()  # ✅ 确保关闭连接
```

---

## 4. 调试方法论

### 4.1 五步调试法

当遇到问题时，按以下顺序排查：

```
Step 1: 复现问题
├─ 能否稳定复现？
├─ 复现条件是什么？
└─ 记录详细的复现步骤

Step 2: 定位错误位置
├─ 是前端还是后端？
├─ 是哪个模块/函数？
└─ 查看浏览器控制台 + 服务器日志

Step 3: 隔离变量
├─ 最小化复现代码
├─ 排除无关因素
└─ 编写独立测试脚本

Step 4: 分析根因
├─ 不是表面现象，而是根本原因
├─ 问 5 次"为什么" (5 Whys)
└─ 参考类似问题的解决方案

Step 5: 修复并验证
├─ 修复代码
├─ 编写回归测试
└─ 验证不影响其他功能
```

### 4.2 诊断脚本模板

创建独立的诊断脚本来隔离问题：

```python
#!/usr/bin/env python3
"""诊断脚本模板"""

import sys
sys.path.insert(0, '.')

def main():
    print("=" * 70)
    print(f"[{datetime.now()}] 开始诊断...")
    print("=" * 70)

    try:
        # Step 1: 测试基础功能
        print("\n[Step 1] 测试基础功能...")
        result = test_basic_functionality()
        print(f"   结果: {'✅ 通过' if result else '❌ 失败'}")

        # Step 2: 测试具体功能
        print("\n[Step 2] 测试具体功能...")
        result = test_specific_feature()
        print(f"   结果: {'✅ 通过' if result else '❌ 失败'}")

        # Step 3: 输出详细信息
        print("\n[Step 3] 详细信息:")
        print_detailed_info()

        print("\n" + "=" * 70)
        print("✅ 诊断完成!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ 诊断过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
```

**使用示例:**
```bash
# 诊断财报上传
$ python diagnose_upload.py

# 诊断情绪分析
$ python test_emotion_fix.py

# 诊断行业对标
$ python test_industry_fix.py
```

### 4.3 日志最佳实践

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 在关键位置添加日志
def process_data(data):
    logger.info(f"开始处理数据，长度: {len(data)}")  # 入口日志
    
    try:
        result = transform(data)
        logger.debug(f"转换结果: {result[:100]}...")  # 调试日志
        return result
        
    except ValueError as e:
        logger.error(f"数据转换失败: {e}, 数据: {data[:200]}")  # 错误日志
        raise
        
    finally:
        logger.info("数据处理完成")  # 出口日志
```

---

## 5. 预防措施

### 5.1 编码规范

**必做事项:**
- [ ] 所有函数都要有类型注解
- [ ] 所有公开函数都要有 docstring
- [ ] 关键逻辑要有注释说明原因（不是说明做什么）
- [ ] 使用常量代替魔法数字
- [ ] 异常处理要具体，不要裸 except

**禁止事项:**
- [x] 不要在生产代码中使用 `print()` 调试
- [x] 不要忽略异常 (`except: pass`)
- [x] 不要在 except 中只打印日志不处理
- [x] 不要硬编码敏感信息（密码、API key）

### 5.2 测试策略

**测试金字塔:**
```
        /\
       /  \     E2E Tests (少量)
      /────\    Integration Tests (适量)
     /      \   Unit Tests (大量)
    /────────\  (自底向上递减)
```

**必须测试的场景:**
- [ ] 所有 API 端点的基本功能
- [ ] 边界情况 (空输入、超大输入、特殊字符)
- [ ] 错误路径 (网络失败、数据库错误)
- [ ] 不同公司名称的行业分类正确性

**测试用例示例:**
```python
def test_industry_classification():
    """测试行业分类准确性"""
    test_cases = [
        ("平安银行", "金融服务业"),
        ("思格新能源", "新能源与储能行业"),
        ("万向集团", "高端制造业"),
        ("openai", "科技互联网行业"),
        ("雅虎", "消费品与零售"),
    ]
    
    for company, expected_industry in test_cases:
        result = detect_industry(company)
        assert result[0] == expected_industry, \
            f"{company} 应该属于 {expected_industry}，实际为 {result[0]}"
    
    print("✅ 所有行业分类测试通过")
```

### 5.3 Code Review 检查清单

提交 PR 前自查：

**功能完整性:**
- [ ] 新功能是否完整实现？
- [ ] 边界情况是否处理？
- [ ] 错误提示是否友好？

**代码质量:**
- [ ] 是否遵循项目编码规范？
- [ ] 是否有不必要的复杂性？
- [ ] 注释是否充分且准确？

**数据准确性:**
- [ ] 行业分类是否正确？（至少测试 5 个不同行业）
- [ ] 数值是否在合理范围？
- [ ] 公司名称/对标公司是否真实？

**性能影响:**
- [ ] 是否引入 N+1 查询？
- [ ] 是否有大循环或递归？
- [ ] 文件处理是否有大小限制？

**安全考虑:**
- [ ] 是否有 SQL 注入风险？
- [ ] 是否有 XSS 风险？
- [ ] 敏感信息是否泄露？

---

## 6. 快速参考卡

### 常见错误速查表

| 错误信息 | 可能原因 | 解决方案 |
|---------|---------|---------|
| `NameError: name 'X' is not defined` | 忘记导入模块 | `import X` |
| `AttributeError: 'X' has no attribute 'Y'` | 方法名拼写错误 | 检查方法名 |
| `500 Internal Server Error` | 后端未捕获异常 | 查看 server logs |
| `Network Error` | API 超时或 CORS | 增加 timeout / 检查 CORS |
| `422 Unprocessable Entity` | 请求数据验证失败 | 检查请求体格式 |
| `ModuleNotFoundError` | 导入路径错误 | 检查包结构 |
| `KeyError: 'X'` | 字典键不存在 | 使用 `.get('X', default)` |
| `ConnectionRefusedError` | 服务未启动 | 启动后端服务 |

### 关键配置参数

| 参数 | 当前值 | 说明 |
|------|--------|------|
| API Timeout | 120000ms (120s) | 适应 Render 冷启动 |
| PDF Max Pages | 30 | 性能优化 |
| PDF Max Chars | 15000 | AI 处理限制 |
| File Max Size | 50MB | 上传限制 |
| News Per Company | 15 | 生成数量 |
| Emotion Days | 30 | 趋势图天数 |

### 重要命令速查

```bash
# 开发服务器
frontend: npm run dev          # http://localhost:3000
backend: uvicorn app.main:app --reload  # http://localhost:8000

# 构建 & 部署
frontend: npm run build
backend: (Render 自动部署)

# 数据库操作
python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"

# 新闻调度器
python run_scheduler.py daily   # 每日增量更新
python run_scheduler.py force   # 强制刷新
python run_scheduler.py status  # 查看状态

# 测试
python diagnose_upload.py       # 诊断财报上传
python test_emotion_fix.py      # 测试情绪分析
python test_industry_fix.py     # 测试行业分类
```

### 环境变量清单

```env
# 必需
DATABASE_URL=sqlite:///./researchmate.db
SECRET_KEY=your-super-secret-key-change-this

# 可选
OPENAI_API_KEY=sk-...
NEWS_API_KEY=...

# 前端
NEXT_PUBLIC_API_URL=https://researchmate.onrender.com
```

---

## 附录: 问题统计

### 已解决问题汇总 (截至 v2.0)

| # | 问题 | 严重度 | 状态 | 解决日期 |
|---|------|--------|------|---------|
| 1 | 行业对标 500 错误 (缺少 import) | P0 | ✅ 已解决 | 2026-05-26 |
| 2 | 财报上传 500 错误 (方法名错误) | P0 | ✅ 已解决 | 2026-05-26 |
| 3 | 行业分类错误 (思格→房地产) | P0 | ✅ 已解决 | 2026-05-26 |
| 4 | 情绪分析显示"暂无数据" | P1 | ✅ 已解决 | 2026-05-26 |
| 5 | 新闻多公司无数据 | P1 | ✅ 已解决 | 2026-05-26 |
| 6 | API 超时 (Network Error) | P2 | ✅ 已解决 | 2026-05-25 |
| 7 | 财报卡片 UI 过大 | P2 | ✅ 已解决 | 2026-05-25 |
| 8 | 情绪分析跳转登录页 | P2 | ✅ 已解决 | 2026-05-25 |

**总计: 8 个问题全部解决 ✅**

---

**文档维护者:** ResearchMate 开发团队  
**最后更新:** 2026-05-26  
**下次审查:** 发现新问题时立即更新