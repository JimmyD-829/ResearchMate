#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股代理中转方案 - 完整测试脚本

功能：
1. 测试Relay服务是否正常运行
2. 测试Render端通过代理获取A股数据
3. 验证直连/代理双模式切换
4. 端到端连通性测试

使用方法：
    # 步骤1：先启动Relay（国内节点）
    python backend/relay_server.py &

    # 步骤2：运行本测试脚本
    python test_relay_proxy.py

    # 或一步到位（自动启动relay+测试）
    python test_relay_proxy.py --auto-start-relay
"""

import os
import sys
import time
import json
import asyncio
import argparse
import subprocess

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))


async def test_relay_health(relay_url: str, relay_key: str):
    """测试1: Relay健康检查"""
    print("\n" + "="*60)
    print("🧪 测试1: Relay健康检查")
    print("="*60)

    import aiohttp
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(
                f"{relay_url}/health",
                headers={"X-Relay-Key": relay_key}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Relay在线!")
                    print(f"   服务: {data.get('service')}")
                    print(f"   版本: {data.get('version')}")
                    print(f"   AKShare: {data.get('akshare')}")
                    print(f"   缓存TTL: {data.get('cache_ttl')}秒")
                    return True
                else:
                    text = await resp.text()
                    print(f"❌ Relay返回异常: HTTP {resp.status} - {text[:100]}")
                    return False
    except Exception as e:
        print(f"❌ 无法连接Relay: {e}")
        print("   请确认:")
        print("   1. Relay服务已启动: python backend/relay_server.py")
        print(f"   2. 地址正确: {relay_url}")
        return False


async def test_single_quote(relay_url: str, relay_key: str, symbol: str = "600519"):
    """测试2: 单股行情查询"""
    print("\n" + "="*60)
    print(f"🧪 测试2: 单股行情查询 ({symbol} 贵州茅台)")
    print("="*60)

    import aiohttp
    start = time.time()

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.get(
                f"{relay_url}/api/stock/quote",
                params={"symbol": symbol},
                headers={"X-Relay-Key": relay_key}
            ) as resp:
                elapsed = time.time() - start

                if resp.status == 200:
                    body = await resp.json()
                    data = body.get("data", {})
                    source = body.get("source", "?")

                    print(f"✅ 查询成功! 耗时: {elapsed:.2f}s | 数据源: {source}")
                    print(f"\n   📊 {data.get('name', '?')} ({data.get('symbol', '?')})")
                    print(f"   ┌──────────────────────────────┐")
                    print(f"   │ 最新价:  ¥{data.get('price', '?'):>12}     │")
                    print(f"   │ 涨跌幅:  {data.get('change_pct', '?'):>12}%     │")
                    print(f"   │ 成交量:  {data.get('volume', '?'):>12}       │")
                    print(f"   │ 市盈率:  {data.get('pe_ratio', '?'):>12}       │")
                    print(f"   │ 总市值:  {data.get('market_cap', '?'):>12} 亿   │")
                    print(f"   └──────────────────────────────┘")

                    # 验证数据合理性
                    price = data.get('price', 0)
                    if isinstance(price, (int, float)) and price > 100:
                        print(f"   ✅ 数据验证通过 (价格合理)")
                        return True
                    else:
                        print(f"   ⚠️ 数据异常: 价格={price}")
                        return False

                elif resp.status == 404:
                    print(f"⚠️ 未找到股票 {symbol}")
                    return False
                else:
                    text = await resp.text()
                    print(f"❌ 查询失败: HTTP {resp.status} - {text[:150]}")
                    return False

    except asyncio.TimeoutError:
        print(f"❌ 请求超时 (>15s)，可能网络不通或AKShare响应慢")
        return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


async def test_kline_data(relay_url: str, relay_key: str, symbol: str = "000001"):
    """测试3: K线历史数据"""
    print("\n" + "="*60)
    print(f"🧪 测试3: 历史K线数据 ({symbol} 平安银行)")
    print("="*60)

    import aiohttp
    start = time.time()

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.get(
                f"{relay_url}/api/stock/kline",
                params={"symbol": symbol, "days": 10},
                headers={"X-Relay-Key": relay_key}
            ) as resp:
                elapsed = time.time() - start

                if resp.status == 200:
                    body = await resp.json()
                    data = body.get("data", {})
                    records = data.get("records", [])

                    print(f"✅ K线查询成功! 耗时: {elapsed:.2f}s")
                    print(f"   记录数: {len(records)}条")

                    if records:
                        first = records[0]
                        last = records[-1]
                        print(f"   最新: {first.get('日期', '?')} 收盘{first.get('收盘', '?')}")
                        print(f"   最旧: {last.get('日期', '?')} 收盘{last.get('收盘', '?')}")
                        return True
                    return False
                else:
                    text = await resp.text()
                    print(f"❌ K线查询失败: {resp.status} - {text[:150]}")
                    return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


async def test_batch_query(relay_url: str, relay_key: str):
    """测试4: 批量查询"""
    print("\n" + "="*60)
    print("🧪 测试4: 批量查询 (3只股票)")
    print("="*60)

    import aiohttp
    symbols = ["600519", "000001", "002594"]
    start = time.time()

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.post(
                f"{relay_url}/api/stock/batch",
                json={"symbols": symbols},
                headers={"X-Relay-Key": relay_key}
            ) as resp:
                elapsed = time.time() - start

                if resp.status == 200:
                    body = await resp.json()
                    data = body.get("data", {})

                    print(f"✅ 批量查询成功! 总耗时: {elapsed:.2f}s (均摊{elapsed/len(symbols):.2f}s/只)")
                    for sym, quote in data.items():
                        name = quote.get('name', '?')
                        price = quote.get('price', '?')
                        chg = quote.get('change_pct', '?')
                        status = "✅" if quote else "❌"
                        print(f"   {status} {sym} {name}: ¥{price} ({chg}%)")
                    return len(data) == len(symbols)
                else:
                    print(f"❌ 批量查询失败: {resp.status}")
                    return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


async def test_stock_list(relay_url: str, relay_key: str):
    """测试5: 股票列表"""
    print("\n" + "="*60)
    print("🧪 测试5: A股列表(Top10)")
    print("="*60)

    import aiohttp
    start = time.time()

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.get(
                f"{relay_url}/api/stock/list",
                params={"top": 10},
                headers={"X-Relay-Key": relay_key}
            ) as resp:
                elapsed = time.time() - start

                if resp.status == 200:
                    body = await resp.json()
                    data = body.get("data", [])
                    print(f"✅ 列表获取成功! 耗时: {elapsed:.2f}s | 共{len(data)}只")
                    for i, s in enumerate(data[:5], 1):
                        print(f"   {i}. {s['symbol']} {s['name']:<8} ¥{s['price']:>10}  市值{s['market_cap']:.0f}亿")
                    return True
                else:
                    print(f"❌ 失败: {resp.status}")
                    return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


async def test_provider_proxy_mode(relay_url: str, relay_key: str):
    """测试6: 通过Provider接口调用（模拟Render端行为）"""
    print("\n" + "="*60)
    print("🧪 测试6: Provider代理模式集成测试 (模拟Render端)")
    print("="*60)

    # 设置环境变量，模拟Render上的配置
    os.environ["AKSHARE_RELAY_URL"] = relay_url
    os.environ["AKSHARE_RELAY_KEY"] = relay_key

    from app.providers.akshare_provider import AKShareProvider

    provider = AKShareProvider()
    print(f"   Provider模式: {provider.mode}")
    print(f"   Provider描述: {provider.description}")

    # 健康检查
    health = await provider.health_check()
    print(f"   健康检查: {json.dumps(health, ensure_ascii=False)}")

    if health.get("status") != "ok":
        print("   ❌ Provider健康检查未通过")
        return False

    # 查询茅台
    print(f"\n   正在查询 600519(贵州茅台)...")
    start = time.time()
    quote = await provider.get_realtime_quote("600519")
    elapsed = time.time() - start

    if quote:
        print(f"   ✅ 查询成功! ({elapsed:.2f}s)")
        print(f"      {quote['name']}: ¥{quote['price']} ({quote['change_pct']}%) source={quote.get('source')}")
        return True
    else:
        print(f"   ❌ 查询失败 ({elapsed:.2f}s)")
        return False


async def run_all_tests(relay_url: str, relay_key: str):
    """运行全部测试"""
    total_start = time.time()

    results = {
        "Relay健康检查": await test_relay_health(relay_url, relay_key),
        "单股行情(茅台)": await test_single_quote(relay_url, relay_key),
        "历史K线(平安)": await test_kline_data(relay_url, relay_key),
        "批量查询(3只)": await test_batch_query(relay_url, relay_key),
        "A股列表Top10": await test_stock_list(relay_url, relay_key),
        "Provider集成": await test_provider_proxy_mode(relay_url, relay_key),
    }

    total_time = time.time() - total_start

    # 汇总
    print("\n" + "="*60)
    print("📊 测试汇总")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, ok in results.items():
        icon = "✅" if ok else "❌"
        print(f"   {icon} {name}")

    score = passed / total * 100
    print(f"\n   结果: {passed}/{total} 通过 ({score:.0f}%)")
    print(f"   总耗时: {total_time:.1f}s")

    if score >= 80:
        print("\n🎉 代理中转方案运行正常！可以在Render上设置环境变量使用了。")
    elif score >= 50:
        print("\n⚠️ 部分测试通过，请检查失败项。")
    else:
        print("\n❌ 大部分测试失败，请检查Relay是否正确启动。")

    return score >= 80


def main():
    parser = argparse.ArgumentParser(description="ResearchMate A股代理中转测试工具")
    parser.add_argument("--relay-url", default="http://localhost:8899", help="Relay地址")
    parser.add_argument("--relay-key", default="researchmate-relay-2026", help="认证密钥")
    parser.add_argument("--auto-start-relay", action="store_true", help="自动启动Relay服务")
    args = parser.parse_args()

    print("""
╔════════════════════════════════════════════════════════╗
║    ResearchMate A股代理中转 - 连通性测试                 ║
╠════════════════════════════════════════════════════════╣
║  Relay地址:  %-40s ║
║  认证密钥:  %-40s ║
╚════════════════════════════════════════════════════════╝
""" % (args.relay_url, args.relay_key))

    relay_process = None

    if args.auto_start_relay:
        print("[自动模式] 正在启动Relay服务...")
        relay_script = os.path.join(os.path.dirname(__file__), "backend", "relay_server.py")
        relay_process = subprocess.Popen(
            [sys.executable, relay_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"   Relay PID: {relay_process.pid}")
        time.sleep(3)  # 等待Relay启动

    try:
        ok = asyncio.run(run_all_tests(args.relay_url, args.relay_key))
        sys.exit(0 if ok else 1)
    finally:
        if relay_process:
            print("\n正在关闭Relay...")
            relay_process.terminate()
            relay_process.wait()


if __name__ == "__main__":
    main()
