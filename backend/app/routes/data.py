"""
数据API路由 - 提供真实金融数据接口
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
from datetime import datetime
import logging

from ..providers.akshare_provider import AKShareProvider
from ..providers.alpha_vantage_provider import AlphaVantageProvider

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/data", tags=["data"])

akshare_provider = AKShareProvider()
alpha_vantage_provider = AlphaVantageProvider()

@router.get("/realtime/{symbol}")
async def get_realtime_quote(symbol: str):
    """
    获取股票实时行情

    支持A股代码（如600519）和美股代码（如AAPL）
    自动识别市场并选择合适的数据源
    """
    logger.info(f"[DataRoute] GET /api/data/realtime/{symbol}")
    try:
        data = None
        source = "unknown"

        if _is_cn_stock(symbol):
            logger.info(f"[DataRoute] 识别为A股 → AKShareProvider (mode={akshare_provider.mode})")
            data = await akshare_provider.get_realtime_quote(symbol)
            source = "akshare"
        else:
            logger.info(f"[DataRoute] 识别为美股 → AlphaVantage")
            data = await alpha_vantage_provider.get_us_stock_quote(symbol)
            source = "alpha_vantage"

        if data:
            logger.info(f"[DataRoute] quote OK {symbol} source={source} price={data.get('price')}")
            return {
                "success": True,
                "data": data,
                "metadata": {
                    "source": source,
                    "update_time": datetime.now().isoformat(),
                    "cache_hit": False
                }
            }
        else:
            logger.warning(f"[DataRoute] quote 返回空 {symbol}")
            raise HTTPException(status_code=404, detail=f"未找到{symbol}的行情数据")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DataRoute] 获取{symbol}实时行情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取行情数据失败: {str(e)}")

@router.get("/history/{symbol}")
async def get_history_kline(
    symbol: str,
    period: str = Query("daily", description="K线周期: daily/weekly/monthly"),
    days: int = Query(30, ge=1, le=365, description="获取天数"),
    adjust: str = Query("qfq", description="复权方式: qfq/hfq/")
):
    """
    获取历史K线数据
    
    主要支持A股市场
    返回DataFrame格式的JSON数据
    """
    try:
        if not _is_cn_stock(symbol):
            raise HTTPException(status_code=400, detail="历史K线目前仅支持A股")
        
        df = await akshare_provider.get_history_kline(
            symbol=symbol,
            period=period,
            days=days,
            adjust=adjust
        )
        
        if df is not None and not df.empty:
            records = df.to_dict('records')
            
            summary = {
                "total_records": len(records),
                "symbol": symbol,
                "period": period,
                "adjust": adjust,
                "latest_price": float(records[0]['收盘']) if records else 0,
                "source": "akshare"
            }
            
            return {
                "success": True,
                "data": records,
                "summary": summary,
                "metadata": {
                    "source": "akshare",
                    "update_time": datetime.now().isoformat()
                }
            }
        else:
            raise HTTPException(status_code=404, detail=f"未找到{symbol}的历史数据")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取{symbol}历史K线失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史数据失败: {str(e)}")

@router.get("/stocks")
async def get_stock_list(limit: int = Query(50, ge=1, le=200)):
    """
    获取热门股票列表
    
    用于情绪分析页面的公司选择器
    默认返回前50只股票
    """
    try:
        stocks = await akshare_provider.get_stock_list()
        
        if stocks:
            return {
                "success": True,
                "data": stocks[:limit],
                "total": len(stocks),
                "metadata": {
                    "source": "akshare",
                    "update_time": datetime.now().isoformat()
                }
            }
        else:
            return {
                "success": True,
                "data": [],
                "total": 0,
                "message": "暂时无法获取股票列表，请检查网络连接或稍后重试"
            }
            
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        return {
            "success": False,
            "error": f"获取股票列表失败: {str(e)}",
            "data": [],
            "fallback_available": True
        }

@router.get("/market-index")
async def get_market_index():
    """
    获取主要市场指数
    
    包括：上证指数、深证成指、创业板指等
    """
    try:
        indices = await akshare_provider.get_market_index()
        
        return {
            "success": True,
            "data": indices,
            "metadata": {
                "source": "akshare",
                "update_time": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"获取市场指数失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取市场指数失败: {str(e)}")

@router.get("/company/{symbol}")
async def get_company_overview(symbol: str):
    """
    获取公司概览信息
    
    主要用于美股公司（通过Alpha Vantage）
    A股公司可使用实时行情接口获取基本信息
    """
    try:
        data = None
        source = "unknown"
        
        if _is_us_stock(symbol):
            data = await alpha_vantage_provider.get_company_overview(symbol)
            source = "alpha_vantage"
        else:
            quote_data = await akshare_provider.get_realtime_quote(symbol)
            if quote_data:
                data = {
                    'symbol': symbol,
                    'name': quote_data.get('name', ''),
                    'price': quote_data.get('price'),
                    'market_cap': quote_data.get('market_cap'),
                    'pe_ratio': quote_data.get('pe_ratio'),
                    'source': 'akshare'
                }
                source = "akshare"
        
        if data:
            return {
                "success": True,
                "data": data,
                "metadata": {
                    "source": source,
                    "update_time": datetime.now().isoformat()
                }
            }
        else:
            raise HTTPException(status_code=404, detail=f"未找到{symbol}的公司信息")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取{symbol}公司信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取公司信息失败: {str(e)}")

@router.get("/forex")
async def get_forex_rate(
    from_currency: str = Query(..., description="源货币代码，如USD"),
    to_currency: str = Query("CNY", description="目标货币代码")
):
    """
    获取汇率信息
    
    示例：/api/data/forex?from_currency=USD&to_currency=CNY
    """
    try:
        rate = await alpha_vantage_provider.get_forex_rate(from_currency, to_currency)
        
        if rate:
            return {
                "success": True,
                "data": {
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "rate": rate,
                    "update_time": datetime.now().isoformat()
                },
                "metadata": {
                    "source": "alpha_vantage"
                }
            }
        else:
            raise HTTPException(status_code=404, detail="未获取到汇率数据")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取汇率失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取汇率失败: {str(e)}")

def _is_cn_stock(symbol: str) -> bool:
    """判断是否为A股代码"""
    symbol = str(symbol).upper()
    return (
        (symbol.isdigit() and len(symbol) == 6) or
        (symbol.startswith(('SH', 'SZ'))) or
        (len(symbol) == 6 and symbol[0] in ('0', '3', '6'))
    )

def _is_us_stock(symbol: str) -> bool:
    """判断是否为美股代码"""
    symbol = str(symbol).upper()
    us_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 
                  'V', 'JNJ', 'WMT', 'PG', 'MA', 'UNH', 'HD', 'BAC', 'CVX', 'ABBV']
    return symbol in us_stocks or (symbol.isalpha() and len(symbol) <= 5)

@router.get("/debug/relay-test")
async def debug_relay_test():
    """调试端点：测试Render到Relay的完整链路连通性"""
    import time as _time
    import os
    t_start = _time.time()

    result = {
        "timestamp": datetime.now().isoformat(),
        "env": {
            "AKSHARE_RELAY_URL": os.environ.get("AKSHARE_RELAY_URL", "(not set)"),
            "AKSHARE_RELAY_KEY": os.environ.get("AKSHARE_RELAY_KEY", "(not set)")[:10] + "...",
            "HTTP_PROXY": os.environ.get("HTTP_PROXY", "(not set)"),
            "HTTPS_PROXY": os.environ.get("HTTPS_PROXY", "(not set)"),
            "ALL_PROXY": os.environ.get("ALL_PROXY", "(not set)"),
        },
        "provider_mode": akshare_provider.mode,
        "provider_url": getattr(akshare_provider, 'relay_url', 'N/A'),
        "provider_headers": list(getattr(akshare_provider, '_relay_headers', {}).keys()),
        "tests": {},
        "error": None,
    }

    # 测试1: 直接requests调Relay health（验证网络连通性）
    try:
        import requests
        t0 = _time.time()
        s = requests.Session()
        s.trust_env = False
        s.headers.update({"ngrok-skip-browser-warning": "1"})
        url = akshare_provider.relay_url + "/health"
        r = s.get(url, headers={"X-Relay-Key": akshare_provider.relay_key}, timeout=20)
        elapsed = round((_time.time() - t0) * 1000)
        body = r.json()
        result["tests"]["health"] = {
            "status": r.status_code,
            "elapsed_ms": elapsed,
            "ok": r.status_code == 200,
            "relay_service": body.get("service"),
            "relay_version": body.get("version"),
            "data_source": body.get("data_source"),
            "body_preview": str(body)[:200],
        }
        logger.info(f"[Debug] health test: HTTP {r.status_code} ({elapsed}ms)")
        s.close()
    except Exception as e:
        elapsed = round((_time.time() - t0) * 1000)
        result["tests"]["health"] = {"status": "ERROR", "elapsed_ms": elapsed, "error": str(e)[:200]}
        result["error"] = f"health check: {e}"
        logger.error(f"[Debug] health test FAIL: {e}")

    # 测试2: 调quote接口（验证数据获取）
    try:
        import requests
        t0 = _time.time()
        s = requests.Session()
        s.trust_env = False
        s.headers.update({"ngrok-skip-browser-warning": "1"})
        url = akshare_provider.relay_url + "/api/stock/quote"
        r = s.get(url, params={"symbol": "600519"},
                  headers={"X-Relay-Key": akshare_provider.relay_key}, timeout=20)
        elapsed = round((_time.time() - t0) * 1000)
        quote_data = r.json().get("data") if r.status_code == 200 else None
        result["tests"]["quote_600519"] = {
            "status": r.status_code,
            "elapsed_ms": elapsed,
            "ok": r.status_code == 200 and quote_data is not None,
            "name": quote_data.get("name") if quote_data else None,
            "price": quote_data.get("price") if quote_data else None,
            "change_pct": quote_data.get("change_pct") if quote_data else None,
            "source": quote_data.get("source") if quote_data else None,
            "body_preview": r.text[:300],
        }
        logger.info(f"[Debug] quote test: HTTP {r.status_code} ({elapsed}ms) price={quote_data.get('price') if quote_data else 'N/A'}")
        s.close()
    except Exception as e:
        elapsed = round((_time.time() - t0) * 1000)
        result["tests"]["quote_600519"] = {"status": "ERROR", "elapsed_ms": elapsed, "error": str(e)[:200]}
        err_msg = f"quote test: {e}"
        result["error"] = (result["error"] + " | " + err_msg) if result["error"] else err_msg
        logger.error(f"[Debug] quote test FAIL: {e}")

    # 测试3: 通过Provider接口调用（完整链路验证）
    try:
        t0 = _time.time()
        provider_result = await akshare_provider.health_check()
        elapsed = round((_time.time() - t0) * 1000)
        result["tests"]["provider_health"] = {
            "elapsed_ms": elapsed,
            **provider_result,
        }
        logger.info(f"[Debug] provider health: {provider_result.get('status')} ({elapsed}ms)")
    except Exception as e:
        result["tests"]["provider_health"] = {"error": str(e)[:200]}
        logger.error(f"[Debug] provider health FAIL: {e}")

    total_elapsed = round((_time.time() - t_start) * 1000)
    result["total_elapsed_ms"] = total_elapsed
    return result

# ---- 简易请求日志记录（进程内内存缓存，用于Dashboard展示）----
_request_log: List[Dict] = []
_MAX_LOG_ENTRIES = 20


def _log_request(entry: Dict):
    """记录一条请求到内存日志（线程安全）"""
    global _request_log
    _request_log.append(entry)
    if len(_request_log) > _MAX_LOG_ENTRIES:
        _request_log = _request_log[-_MAX_LOG_ENTRIES:]


def _get_recent_requests(count: int = 10) -> List[Dict]:
    """获取最近的请求日志"""
    return list(reversed(_request_log[-count:]))


@router.get("/pipeline-status")
async def get_pipeline_status():
    """
    数据链路聚合状态接口 - 供前端 Dashboard 使用

    检测全链路各节点状态：Render API → ngrok → Relay → 数据源
    返回结构化数据供前端渲染 Pipeline 可视化
    """
    import time as _time
    t0 = _time.time()
    import os

    pipeline = {
        "timestamp": datetime.now().isoformat(),
        "pipeline": {},
        "recent_requests": _get_recent_requests(10),
        "alerts": [],
        "env_summary": {
            "relay_url_set": bool(os.environ.get("AKSHARE_RELAY_URL")),
            "relay_key_set": bool(os.environ.get("AKSHARE_RELAY_KEY")),
            "proxy_vars": len([v for v in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY'] if os.environ.get(v)]),
            "provider_mode": akshare_provider.mode,
        },
    }

    # ====== 节点1: Render API (自身) ======
    pipeline["pipeline"]["render_api"] = {
        "name": "Render API",
        "status": "ok",
        "latency_ms": 1,
        "detail": f"mode={akshare_provider.mode}",
    }

    # ====== 节点2: ngrok + Relay (连通性) ======
    ngrok_status = {"name": "ngrok Tunnel", "status": "unknown", "latency_ms": None, "url": "N/A", "detail": ""}
    relay_status = {"name": "Relay Server", "status": "unknown", "version": "-", "data_source": "-", "detail": ""}

    if akshare_provider.mode == "proxy":
        try:
            import requests as _req
            _t = _time.time()
            _s = _req.Session()
            _s.trust_env = False
            _s.headers.update({"ngrok-skip-browser-warning": "1"})
            _url = akshare_provider.relay_url + "/health"
            _r = _s.get(_url, headers={"X-Relay-Key": akshare_provider.relay_key}, timeout=15)
            _elapsed = round((_time.time() - _t) * 1000)

            if _r.status_code == 200:
                _body = _r.json()
                ngrok_status["status"] = "ok"
                ngrok_status["latency_ms"] = _elapsed
                ngrok_status["url"] = akshare_provider.relay_url.replace("https://", "").split(".")[0] + "***"
                ngrok_status["detail"] = f"{_elapsed}ms"

                relay_status["status"] = "ok"
                relay_status["version"] = _body.get("version", "?")
                relay_status["data_source"] = _body.get("data_source", "?")
                relay_status["detail"] = f"v{_body.get('version','?')} via {_body.get('data_source','?')}"
            else:
                ngrok_status["status"] = "error"
                ngrok_status["latency_ms"] = _elapsed
                ngrok_status["detail"] = f"HTTP {_r.status_code}"
                relay_status["status"] = "error"
                relay_status["detail"] = f"upstream returned {_r.status_code}"
                pipeline["alerts"].append({
                    "level": "error",
                    "node": "ngrok",
                    "message": f"Relay返回异常状态码 {_r.status_code}",
                })
            _s.close()
        except Exception as e:
            _elapsed = round((_time.time() - _t) * 1000)
            ngrok_status["status"] = "error"
            ngrok_status["latency_ms"] = _elapsed
            ngrok_status["detail"] = f"{type(e).__name__}"
            relay_status["status"] = "error"
            relay_status["detail"] = "unreachable"
            pipeline["alerts"].append({
                "level": "error",
                "node": "ngrok",
                "message": f"无法连接Relay: {type(e).__name__}",
            })
    else:
        # 直连模式，没有ngrok/relay
        ngrok_status["status"] = "skipped"
        ngrok_status["detail"] = "直连模式，不经过隧道"
        relay_status["status"] = "skipped"
        relay_status["detail"] = "直连模式"

    pipeline["pipeline"]["ngrok"] = ngrok_status
    pipeline["pipeline"]["relay_server"] = relay_status

    # ====== 节点3: A股数据源 (腾讯财经 / Relay内部) ======
    cn_source_status = {"name": "腾讯财经 (A股)", "status": "unknown", "last_query_ms": None, "detail": ""}

    if akshare_provider.mode == "proxy":
        # 通过Relay间接判断数据源健康度
        cn_source_status["status"] = relay_status["status"]
        cn_source_status["detail"] = "via Relay" if relay_status["status"] == "ok" else "Relay不可达"
    else:
        # 直连模式：快速测试AKShare
        try:
            _t2 = _time.time()
            _test_data = await akshare_provider.get_realtime_quote("600519")
            _elapsed2 = round((_time.time() - _t2) * 1000)
            if _test_data:
                cn_source_status["status"] = "ok"
                cn_source_status["last_query_ms"] = _elapsed2
                cn_source_status["detail"] = f"600519 ¥{_test_data.get('price','?')} ({_elapsed2}ms)"
            else:
                cn_source_status["status"] = "warning"
                cn_source_status["detail"] = "查询成功但返回空数据"
        except Exception as e:
            cn_source_status["status"] = "error"
            cn_source_status["detail"] = str(e)[:80]
            pipeline["alerts"].append({
                "level": "error",
                "node": "cn_source",
                "message": f"A股数据源异常: {str(e)[:60]}",
            })

    pipeline["pipeline"]["cn_data_source"] = cn_source_status

    # ====== 节点4: 美股数据源 (AlphaVantage) ======
    us_source_status = {"name": "AlphaVantage (美股)", "status": "unknown", "calls_remaining": None, "detail": ""}
    try:
        _t3 = _time.time()
        _us_test = await alpha_vantage_provider.get_us_stock_quote("AAPL")
        _elapsed3 = round((_time.time() - _t3) * 1000)
        if _us_test:
            us_source_status["status"] = "ok"
            us_source_status["last_query_ms"] = _elapsed3
            us_source_status["detail"] = f"AAPL ${_us_test.get('price','?')} ({_elapsed3}ms)"
        else:
            us_source_status["status"] = "warning"
            us_source_status["detail"] = "查询成功但返回空数据"
    except Exception as e:
        us_source_status["status"] = "error"
        us_source_status["detail"] = str(e)[:80]
        pipeline["alerts"].append({
            "level": "warning",
            "node": "us_source",
            "message": f"美股数据源异常: {str(e)[:60]}",
        })

    pipeline["pipeline"]["us_data_source"] = us_source_status

    # ====== 计算整体状态 ======
    all_nodes = pipeline["pipeline"]
    error_count = sum(1 for v in all_nodes.values() if v["status"] == "error")
    ok_count = sum(1 for v in all_nodes.values() if v["status"] == "ok")

    if error_count > 0:
        pipeline["overall"] = "error"
    elif ok_count >= 3:
        pipeline["overall"] = "healthy"
    elif ok_count >= 1:
        pipeline["overall"] = "degraded"
    else:
        pipeline["overall"] = "unknown"

    total_elapsed = round((_time.time() - t0) * 1000)
    pipeline["query_elapsed_ms"] = total_elapsed
    logger.info(f"[PipelineStatus] overall={pipeline['overall']} ok={ok_count} err={error_count} ({total_elapsed}ms)")

    return pipeline


@router.get("/indicators/{symbol}")
async def get_technical_indicators(
    symbol: str,
    period: str = Query("daily", description="K线周期: daily/weekly/monthly"),
    days: int = Query(120, ge=30, le=365, description="K线天数，至少30天"),
    adjust: str = Query("qfq", description="复权方式: qfq/hfq/"),
):
    """
    技术指标综合接口 — 供投资分析面板使用

    一次性返回全部技术指标计算结果：
    - MA (5/10/20/60) + 金叉死叉信号
    - MACD (12,26,9) + DIF/DEA/柱状图
    - RSI (14) + 超买超卖判断
    - KDJ (9,3,3) + 交叉信号
    - BOLL (20,2) + 带宽分析
    - 风险指标（区间收益/最大回撤/夏普比率/波动率）
    """
    import time as _time
    t0 = _time.time()
    logger.info(f"[DataRoute] GET /api/data/indicators/{symbol} period={period} days={days}")

    try:
        if not _is_cn_stock(symbol):
            raise HTTPException(status_code=400, detail="技术指标目前仅支持A股")

        # 1. 获取K线数据
        df = await akshare_provider.get_history_kline(
            symbol=symbol, period=period, days=days, adjust=adjust
        )

        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"未找到{symbol}的历史数据")

        # 2. 转换为记录列表（从旧到新排列）
        df_sorted = df.sort_values('日期', ascending=True)
        records = df_sorted.to_dict('records')

        # 3. 注入symbol信息
        for r in records:
            r['symbol'] = symbol

        # 4. 计算全部技术指标
        from ..services.indicator_service import indicator_service
        result = indicator_service.calculate_all(records)

        if "error" in result:
            raise HTTPException(status_code=422, detail=result["error"])

        # 5. 补充元信息
        elapsed = round((_time.time() - t0) * 1000)
        result["metadata"] = {
            "source": "akshare",
            "symbol": symbol,
            "period": period,
            "adjust": adjust,
            "kline_count": len(records),
            "calculate_elapsed_ms": elapsed,
            "update_time": datetime.now().isoformat(),
        }

        logger.info(f"[DataRoute] indicators OK {symbol} {len(records)}bars ({elapsed}ms)")
        return {"success": True, "data": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DataRoute] 指标计算失败 {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"指标计算失败: {str(e)}")


@router.get("/investment-overview/{symbol}")
async def get_investment_overview(symbol: str):
    """
    投资概览聚合接口 — 供投资分析面板使用

    聚合：实时行情 + 技术指标 + 基本面 + 风险指标
    前端一次请求即可获得面板所需的全部数据
    """
    import time as _time
    import asyncio
    t0 = _time.time()
    logger.info(f"[DataRoute] GET /api/data/investment-overview/{symbol}")

    try:
        # 并行获取：实时行情 + K线数据 + 公司概览
        tasks = {}
        if _is_cn_stock(symbol):
            tasks["quote"] = akshare_provider.get_realtime_quote(symbol)
            tasks["kline"] = akshare_provider.get_history_kline(symbol=symbol, days=120, adjust="qfq")
            # 公司基本面（如果有）
            try:
                tasks["company"] = akshare_provider.get_company_info(symbol)
            except Exception:
                pass
        else:
            tasks["quote"] = alpha_vantage_provider.get_us_stock_quote(symbol)

        results = await asyncio.gather(*list(tasks.values()), return_exceptions=True)
        task_keys = list(tasks.keys())

        overview = {
            "symbol": symbol,
            "market": "CN" if _is_cn_stock(symbol) else "US",
            "timestamp": datetime.now().isoformat(),
            "quote": None,
            "indicators": None,
            "company": None,
            "risk": None,
        }

        for i, key in enumerate(task_keys):
            if isinstance(results[i], Exception):
                logger.warning(f"[InvestmentOverview] {key} failed: {results[i]}")
                continue
            data = results[i]

            if key == "quote":
                overview["quote"] = data
            elif key == "kline":
                if data is not None and not data.empty:
                    from ..services.indicator_service import indicator_service
                    df_sorted = data.sort_values('日期', ascending=True)
                    records = df_sorted.to_dict('records')
                    for r in records:
                        r['symbol'] = symbol
                    ind_result = indicator_service.calculate_all(records)
                    overview["indicators"] = ind_result
                    overview["risk"] = ind_result.get("risk")
            elif key == "company":
                overview["company"] = data

        elapsed = round((_time.time() - t0) * 1000)
        overview["elapsed_ms"] = elapsed
        logger.info(f"[DataRoute] investment-overview {symbol} ({elapsed}ms)")

        return {"success": True, "data": overview}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DataRoute] investment-overview 失败 {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取投资概览失败: {str(e)}")


# 在现有的 get_realtime_quote 等接口中注入日志记录
_original_get_realtime_quote = get_realtime_quote.__wrapped__ if hasattr(get_realtime_quote, '__wrapped__') else None


@router.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    await alpha_vantage_provider.close()
