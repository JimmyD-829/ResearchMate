#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股数据代理中转服务 (Proxy Relay)

部署位置：国内可访问东方财富网络的任意机器（本地电脑/国内VPS/云服务器）
作用：为海外部署的ResearchMate提供A股实时数据通道

启动方式：
    python relay_server.py
    # 或指定端口和密钥
    python relay_server.py --port 8899 --relay-key your-secret-key

环境变量：
    RELAY_PORT      - 监听端口 (默认 8899)
    RELAY_KEY       - 认证密钥 (默认 researchmate-relay-2026)
    RELAY_CACHE_TTL - 缓存秒数 (默认 60，即1分钟)

接口列表：
    GET  /health                          - 健康检查
    GET  /api/stock/quote?symbol=600519   - 单股实时行情
    GET  /api/stock/kline?symbol=600519&days=30  - 历史K线
    GET  /api/stock/list?top=50           - A股列表(市值排序)
    POST /api/stock/batch                 - 批量查询行情
"""

import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime, timedelta
from typing import Optional, List, Dict

# ===== 关键：清除代理环境变量，确保AKShare直连东方财富 =====
# Python的requests/urllib3会读取这些代理变量，导致国内API请求走海外代理失败
for _proxy_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
                    'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']:
    os.environ.pop(_proxy_var, None)

# ===== 关键：猴子补丁修复requests库与东方财富的TLS兼容性 =====
# 东方财富push2接口会对requests库的TLS指纹做校验导致连接被关闭
# 通过预加载并patch Session.default_headers解决
try:
    import requests
    # 强制设置浏览器级User-Agent，避免被识别为爬虫
    _browser_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://quote.eastmoney.com/",
    }
    # Patch: 让所有requests默认带上这些headers
    _orig_init = requests.Session.__init__
    def _patched_session_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        self.headers.update(_browser_headers)
    requests.Session.__init__ = _patched_session_init
    print("[Relay] ✅ 已应用requests库TLS兼容补丁")
except ImportError:
    pass  # requests未安装时忽略

from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ===== 日志配置 =====
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ===== 配置 =====
RELAY_PORT = int(os.environ.get("RELAY_PORT", 8899))
RELAY_KEY = os.environ.get("RELAY_KEY", "researchmate-relay-2026")
CACHE_TTL = int(os.environ.get("RELAY_CACHE_TTL", 60))  # 秒

app = FastAPI(
    title="ResearchMate A股数据中转",
    version="1.0.0",
    description="为海外部署的ResearchMate提供A股数据代理通道"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== 内存缓存（简单实现）=====
_cache: Dict[str, Dict] = {}  # {key: {"data": ..., "ts": timestamp}}


def _cache_get(key: str) -> Optional[Dict]:
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        return entry["data"]
    if key in _cache:
        del _cache[key]
    return None


def _cache_set(key: str, data: Dict):
    _cache[key] = {"data": data, "ts": time.time()}


def _auth_check(x_relay_key: Optional[str] = Header(None)):
    """验证请求来源"""
    if not x_relay_key or x_relay_key != RELAY_KEY:
        raise HTTPException(status_code=401, detail="无效的认证密钥")


# ===== 多数据源直连层（绕过东方财富push2的TLS/封IP问题）=====
# 主数据源：腾讯财经（稳定、无TLS指纹检测）
# 备用：新浪财经

import urllib.request
import urllib.parse
import json as _json
import ssl

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
}

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


def _http_get(url: str) -> str:
    """通用HTTP GET（urllib）"""
    import time as _time
    t0 = _time.time()
    req = urllib.request.Request(url, headers=_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15, context=_SSL_CTX) as resp:
            raw = resp.read()
            elapsed_ms = round((_time.time() - t0) * 1000)
            # 尝试UTF-8，失败则GBK（国内API常用编码）
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("gbk", errors="replace")
            logger.debug(f"[Relay:HTTP] GET {url[:80]} → {len(text)}B ({elapsed_ms}ms)")
            return text
    except Exception as e:
        elapsed_ms = round((_time.time() - t0) * 1000)
        logger.error(f"[Relay:HTTP] GET FAIL {url[:80]} ({elapsed_ms}ms) → {type(e).__name__}: {e}")
        raise


# ==================== 腾讯财经数据源 ====================

# 代码 → 腾讯前缀映射
def _tencent_prefix(symbol: str) -> str:
    """股票代码转腾讯格式：sh=上海, sz=深圳"""
    if symbol.startswith("6"):
        return f"sh{symbol}"
    elif symbol.startswith(("0", "3")):
        return f"sz{symbol}"
    elif symbol.startswith(("4", "8")):
        return f"sz{symbol}"
    return f"sz{symbol}"


def _parse_tencent_line(line: str) -> Optional[dict]:
    """
    解析单条腾讯行情数据
    格式: v_sh600519="1~贵州茅台~600519~最新价~昨收~今开~成交量(手)~
           外盘~内盘~现价~最高价~最低价~..."
    """
    if not line or "~" not in line:
        return None
    # 提取引号内内容
    start = line.find('"')
    end = line.rfind('"')
    if start < 0 or end <= start:
        return None
    parts = line[start+1:end].split("~")
    if len(parts) < 45:
        return None

    def _f(i):
        try:
            v = parts[i]
            if v == "" or v == "-":
                return None
            return round(float(v), 2)
        except (ValueError, IndexError):
            return None

    symbol = parts[2]  # 如 600519
    return {
        "symbol": symbol,
        "name": parts[1],
        "price": _f(3),          # 最新价
        "prev_close": _f(4),     # 昨收
        "open": _f(5),           # 今开
        "volume": _f(6),         # 成交量(手)
        "outer_vol": _f(7),      # 外盘
        "inner_vol": _f(8),      # 内盘
        "high": _f(33),          # 最高价
        "low": _f(34),           # 最低价
        "change_amount": _f(31), # 涨跌额
        "change_pct": _f(32),    # 涨跌幅(%)
        "turnover": _f(37),      # 成交额(万)→转为元
        "turnover_rate": _f(38), # 换手率(%)
        "pe_ratio": _f(39),      # 市盈率
        "amplitude": _f(43),     # 振幅(%)
        "circulating_cap": _f(44),# 流通市值(亿)
        "market_cap": _f(45),    # 总市值(亿)
        "volume_ratio": _f(49) if len(parts) > 49 else None,  # 量比
        "update_time": parts[30] if len(parts) > 30 else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "tencent",
    }


def _fetch_tencent_quote(symbols: list) -> dict:
    """批量获取腾讯行情，返回 {symbol: data}"""
    codes = ",".join(_tencent_prefix(s) for s in symbols)
    url = f"https://qt.gtimg.cn/q={codes}"
    logger.info(f"[Relay:Tencent] 批量查询 {len(symbols)}只: {symbols}")
    raw = _http_get(url)

    results = {}
    for line in raw.strip().split(";"):
        line = line.strip()
        if not line:
            continue
        d = _parse_tencent_line(line)
        if d and d["symbol"]:
            results[d["symbol"]] = d

    logger.info(f"[Relay:Tencent] 查询完成 请求={len(symbols)} 返回={len(results)}")
    return results


def _find_stock(symbol: str) -> Optional[dict]:
    """查询单只股票"""
    result = _fetch_tencent_quote([symbol])
    return result.get(symbol)


def _get_all_a_stocks_top(n: int = 5000) -> list:
    """
    获取A股列表（通过腾讯批量接口分页获取）
    注意：腾讯不支持一次拉全量，这里返回热门/主要股票
    实际部署时可用本地维护的股票代码表 + 批量查询
    """
    # 使用上证50+沪深300+中证500的核心成分股作为基础池
    # 同时支持按需查询任意代码
    major_codes = [
        # 上证权重
        "600519","601318","601398","601988","601288","601939","601088",
        "601166","601628","601668","601888","601012","601236","601899",
        "600036","600276","600900","600585","600887","601618","600048",
        # 深证权重
        "000001","000002","000063","000333","000651","000725","000776",
        "000858","002415","002594","002714","002304","002352","002475",
        # 创业板
        "300750","300059","300124","300142","300274","300003","300015",
        # 科创板
        "688981","688256","688005","688111","688187","688303","688012",
        # 更多大盘股
        "601985","601838","601766","600028","600029","600030","600031",
        "600050","600061","600104","600109","600115","600150","600196",
        "600201","600219","600233","600271","600309","600340","600362",
        "600372","600406","600426","600438","600489","600497","600516",
        "600570","600588","600585","600600","600690","600703","600745",
        "600809","600837","600867","600893","600900","600919","600941",
        "601066","601077","601117","601127","601138","601155","601168",
        "601177","601198","601211","601225","601228","601229","601231",
        "601288","601298","601318","601336","601360","601377","601390",
        "601398","601555","601567","601577","601586","601598","601600",
        "601601","601606","601607","601615","601628","601633","601636",
        "601668","601669","601688","601689","601696","601698","601728",
        "601766","601788","601799","601808","601816","601818","601828",
        "601838","601857","601868","601872","601878","601881","601888",
        "601899","601901","601918","601919","601939","601958","601966",
        "601985","601988","601989","601992","601995","601998","603019",
        "603160","603195","603259","603260","603288","603290","603298",
        "603320","603338","603359","603393","603501","603507","603568",
        "603593","603658","603799","603806","603833","603866","603883",
        "603899","603920","603993","605007","605117","605178","605287",
        "605358","605377","605500","605589","688001","688005","688012",
        "688016","688036","688099","688111","688122","688126","688168",
        "688169","688176","688180","688181","688185","688186","688187",
        "688188","688196","688198","688200","688203","688208","688209",
        "688210","688216","688222","688230","688235","688248","688250",
        "688256","688258","688270","688280","688298","688299","688301",
        "688302","688303","688306","688308","688310","688311","688312",
        "688315","688317","688320","688321","688326","688333","688336",
        "688339","688350","688356","688363","688365","688366","688370",
        "688372","688377","688380","688382","688383","688385","688388",
        "688396","688400","688408","688418","688420","688422","688428",
        "688430","688432","688433","688438","688448","688450","688458",
        "688468","688472","688480","688484","688488","688491","688496",
        "688498","688499","688503","688512","688513","688516","688520",
        "688521","688526","688529","688531","688536","688538","688539",
        "688543","688546","688548","688550","688551","688552","688556",
        "688558","688561","688563","688566","688568","688571","688573",
        "688576","688578","688580","688581","688583","688586","688588",
        "688589","688592","688595","688596","688598","688599","688600",
        "688603","688606","688608","688612","688616","688618","688621",
        "688622","688625","688627","688628","688630","688632","688636",
        "688639","688641","688642","688646","688648","688650","688652",
        "688654","688656","688658","688660","688661","688662","688663",
        "688666","688668","688671","688672","688673","688676","688677",
        "688678","688679","688680","688681","688682","688683","688686",
        "688691","688692","688693","688696","688698","688700","688702",
        "688703","688707","688708","688709","688711","688712","688713",
        "688715","688717","688720","688721","688722","688723","688725",
        "688726","688728","688729","688731","688732","688733","688735",
        "688737","688738","688739","688741","688742","688743","688745",
        "688746","688748","688749","688750","688752","688753","688756",
        "688757","688758","688759","688760","688761","688762","688763",
        "688764","688765","688766","688767","688768","688769","688770",
        "688771","688772","688773","688775","688776","688777","688778",
        "688779","688780","688781","688782","688783","688784","688785",
        "688786","688787","688788","688789","688790","688791","688792",
        "688793","688794","688795","688796","688797","688798","688800",
        "688801","688802","688803","688804","688805","688806","688807",
        "688808","688809","688810","688811","688812","688813","688814",
        "688815","688816","688817","688818","688819","688820","688821",
        "688822","688823","688824","688825","688826","688827","688828",
        "688829","688830","688831","688832","688833","688834","688835",
        "688836","688837","688838","688839","688840","688841","688842",
        "688843","688844","688845","688846","688847","688848","688849",
        "688850","688851","688852","688853","688854","688855","688856",
        "688857","688858","688859","688860","688861","688862","688863",
        "688864","688865","688866","688867","688868","688869","688870",
        "688871","688872","688873","688874","688875","688876","688877",
        "688878","688879","688880","688881","688882","688883","688884",
        "688885","688886","688887","688888","688889","688890","688891",
        "688892","688893","688894","688895","688896","688897","688898",
        "688899","688900","688901","688902","688903","688904","688905",
        "688906","688907","688908","688909","688910","688911","688912",
        "688913","688914","688915","688916","688917","688918","688919",
        "688920","688921","688922","688923","688924","688925","688926",
        "688927","688928","688929","688930","688931","688932","688933",
        "688934","688935","688936","688937","688938","688939","688940",
        "688941","688942","688943","688944","688945","688946","688947",
        "688948","688949","688950","688951","688952","688953","688954",
        "688955","688956","688957","688958","688959","688960","688961",
        "688962","688963","688964","688965","688966","688967","688968",
        "688969","688970","688971","688972","688973","688974","688975",
        "688976","688977","688978","688979","688980","688981","688982",
        "688983","688984","688985","688986","688987","688988","688989",
        "688990","688991","688992","688993","688994","688995","688996",
        "688997","688998","688999","689009","689010","689011","689012",
        "689015","689016","689017","689019","689020","689021","689022",
        "689024","689025","689027","689028","689029","689031","689032",
        "689033","689034","689036","689037","689038","689039","689041",
        "689042","689043","689044","689045","689046","689047","689048",
        "689049","689051","689052","689053","689054","689055","689056",
        "689057","689058","689059","689061","689062","689063","689064",
        "689065","689066","689067","689068","689069","689070","689071",
        "689072","689073","689074","689075","689076","689077","689078",
        "689079","689080","689081","689082","689083","689084","689085",
        "689086","689087","689088","689089","689090","689091","689092",
        "689093","689094","689095","689096","689097","689098","689099",
        "689100","689101","689102","689103","689104","689105","689106",
        "689107","689108","689109","689110","689111","689112","689113",
        "689114","689115","689116","689117","689118","689119","689120",
        "689121","689122","689123","689124","689125","689126","689127",
        "689128","689129","689130","689131","689132","689133","689134",
        "689135","689136","689137","689138","689139","689140","689141",
        "689142","689143","689144","689145","689146","689147","689148",
        "689149","689150","689151","689152","689153","689154","689155",
        "689156","689157","689158","689159","689160","689161","689162",
        "689163","689164","689165","689166","689167","689168","689169",
        "689170","689171","689172","689173","689174","689175","689176",
        "689177","689178","689179","689180","689181","689182","689183",
        "689184","689185","689186","689187","689188","689189","689190",
        "689191","689192","689193","689194","689195","689196","689197",
        "689198","689199","689200",
    ]

    # 分批查询（腾讯每批约50个）
    all_data = {}
    batch_size = 50
    for i in range(0, min(len(major_codes), n), batch_size):
        batch = major_codes[i:i+batch_size]
        result = _fetch_tencent_quote(batch)
        all_data.update(result)

    return [all_data.get(code) for code in major_codes[:n] if all_data.get(code)]


async def _run_sync(func, *args, **kwargs):
    """在线程池中运行同步调用"""
    loop = asyncio.get_event_loop()
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        future = pool.submit(func, *args, **kwargs)
        return await loop.run_in_executor(None, lambda: future.result())


import asyncio


# ==================== 接口实现 ====================

@app.get("/health")
async def health_check():
    """健康检查 - 不需要认证"""
    logger.info(f"[Relay:API] GET /health")
    return {
        "status": "ok",
        "service": "researchmate-a-stock-relay",
        "version": "1.2.0",
        "data_source": "tencent (qt.gtimg.cn)",
        "cache_ttl": CACHE_TTL,
        "time": datetime.now().isoformat()
    }


@app.get("/api/stock/quote")
async def get_stock_quote(
    symbol: str = Query(..., description="股票代码，如600519"),
    x_relay_key: Optional[str] = Header(None),
):
    """获取单只A股实时行情"""
    logger.info(f"[Relay:API] GET /api/stock/quote?symbol={symbol}")
    _auth_check(x_relay_key)

    cache_key = f"quote:{symbol}"
    cached = _cache_get(cache_key)
    if cached:
        logger.info(f"[Relay:API] quote 命中缓存 {symbol} price={cached.get('price')}")
        return {"source": "cache", "data": cached}

    try:
        result = await _run_sync(_find_stock, symbol)
        if not result:
            raise HTTPException(status_code=404, detail=f"未找到股票 {symbol}")

        _cache_set(cache_key, result)
        logger.info(f"[Relay:API] quote OK {symbol} name={result.get('name')} price={result.get('price')} source=tencent")
        return {"source": "tencent", "data": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Relay:API] 获取{symbol}行情异常: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"数据获取失败: {str(e)[:200]}")


@app.get("/api/stock/kline")
async def get_stock_kline(
    symbol: str = Query(..., description="股票代码"),
    days: int = Query(30, ge=5, le=250, description="天数"),
    adjust: str = Query("qfq", description="复权类型"),
    x_relay_key: Optional[str] = Header(None),
):
    """获取历史K线数据（腾讯财经接口）"""
    logger.info(f"[Relay:API] GET /api/stock/kline?symbol={symbol}&days={days}")
    _auth_check(x_relay_key)

    cache_key = f"kline:{symbol}:{days}:{adjust}"
    cached = _cache_get(cache_key)
    if cached:
        logger.info(f"[Relay:API] kline 命中缓存 {symbol} days={days}")
        return {"source": "cache", "data": cached}

    try:
        def _fetch_kline():
            prefix = _tencent_prefix(symbol)
            start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            end = datetime.now().strftime("%Y-%m-%d")
            url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={prefix},day,{start},{end},{days},qfq"
            logger.debug(f"[Relay:Tencent] K线请求 {url[:100]}")
            raw = _http_get(url)
            data = _json.loads(raw)

            stock_data = data.get("data", {}).get(prefix, {})
            klines = stock_data.get("qfqday", [])
            if not klines:
                klines = stock_data.get("day", [])

            records = []
            for item in klines:
                if len(item) >= 6:
                    records.append({
                        "日期": item[0],
                        "开盘": float(item[1]),
                        "收盘": float(item[2]),
                        "最高": float(item[3]),
                        "最低": float(item[4]),
                        "成交量": int(float(item[5])),
                    })
            return records

        records = await _run_sync(_fetch_kline)

        if not records:
            raise HTTPException(status_code=404, detail=f"未找到 {symbol} 的K线数据")

        result = {
            "symbol": symbol,
            "period": "daily",
            "days": len(records),
            "records": records,
            "source": "tencent",
        }

        _cache_set(cache_key, result)
        logger.info(f"[Relay:API] kline OK {symbol} records={len(records)}")
        return {"source": "tencent", "data": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Relay:API] 获取{symbol}K线异常: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"K线获取失败: {str(e)[:200]}")


@app.get("/api/stock/list")
async def get_stock_list(
    top: int = Query(50, ge=10, le=500, description="返回数量"),
    x_relay_key: Optional[str] = Header(None),
):
    """获取A股市值排名列表"""
    logger.info(f"[Relay:API] GET /api/stock/list?top={top}")
    _auth_check(x_relay_key)

    cache_key = f"list:{top}"
    cached = _cache_get(cache_key)
    if cached:
        logger.info(f"[Relay:API] list 命中缓存 top={top}")
        return {"source": "cache", "data": cached}

    try:
        def _fetch_list():
            all_stocks = _get_all_a_stocks_top(top)
            stocks = []
            for s in all_stocks:
                if not s:
                    continue
                try:
                    cap = s.get("market_cap", 0) or 0
                    stocks.append({
                        "symbol": s["symbol"],
                        "name": s.get("name", ""),
                        "price": s.get("price"),
                        "change_pct": s.get("change_pct"),
                        "market_cap": cap,
                    })
                except (KeyError, TypeError):
                    continue

            stocks.sort(key=lambda x: x["market_cap"] or 0, reverse=True)
            return stocks[:top]

        result = await _run_sync(_fetch_list)

        _cache_set(cache_key, result)
        logger.info(f"[Relay:API] list OK count={len(result)}")
        return {"source": "tencent", "data": result}

    except Exception as e:
        logger.error(f"[Relay:API] 获取列表异常: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=str(e)[:200])


class BatchRequest(BaseModel):
    symbols: List[str]


@app.post("/api/stock/batch")
async def batch_quotes(
    req: BatchRequest,
    x_relay_key: Optional[str] = Header(None),
):
    """批量查询多只股票行情（一次拉取全量再过滤）"""
    logger.info(f"[Relay:API] POST /api/stock/batch symbols={req.symbols}")
    _auth_check(x_relay_key)

    try:
        def _fetch_batch():
            raw_results = _fetch_tencent_quote(req.symbols)
            results = {}
            errors = {}
            for sym in req.symbols:
                d = raw_results.get(sym)
                if not d:
                    errors[sym] = "not_found"
                    continue
                results[sym] = {
                    "symbol": sym,
                    "name": d.get("name", ""),
                    "price": d.get("price"),
                    "change_pct": d.get("change_pct"),
                    "change_amount": d.get("change_amount"),
                    "volume": d.get("volume"),
                    "pe_ratio": d.get("pe_ratio"),
                    "market_cap": d.get("market_cap"),
                    "update_time": d.get("update_time"),
                    "source": "tencent",
                }
            return results, errors

        results, errors = await _run_sync(_fetch_batch)
        logger.info(f"[Relay:API] batch OK requested={len(req.symbols)} got={len(results)} missing={len(errors)}")
        return {"source": "tencent", "data": results, "errors": errors}

    except Exception as e:
        logger.error(f"[Relay:API] batch异常: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=str(e)[:200])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ResearchMate A股数据代理中转服务")
    parser.add_argument("--port", type=int, default=RELAY_PORT, help="监听端口")
    parser.add_argument("--relay-key", type=str, default=RELAY_KEY, help="认证密钥")
    args = parser.parse_args()

    print(f"""
╔════════════════════════════════════════════════════════╗
║     ResearchMate A股数据代理中转服务 v1.2               ║
╠════════════════════════════════════════════════════════╣
║  监听地址: http://0.0.0.0:{args.port:<34} ║
║  认证密钥: {args.relay_key:<38} ║
║  缓存TTL:  {CACHE_TTL}秒{'':<41} ║
║  数据源:  腾讯财经 (qt.gtimg.cn)                        ║
╠════════════════════════════════════════════════════════╣
║  接口:                                                ║
║    GET  /health                                       ║
║    GET  /api/stock/quote?symbol=600519                ║
║    GET  /api/stock/kline?symbol=600519&days=30        ║
║    GET  /api/stock/list?top=50                        ║
║    POST /api/stock/batch                              ║
╚════════════════════════════════════════════════════════╝
""")

    logger.info(f"[Relay] 启动完成 port={args.port} key={args.relay_key[:8]}... cache_ttl={CACHE_TTL}s")
    logger.info(f"[Relay] 数据源: 腾讯财经 (qt.gtimg.cn / web.ifzq.gtimg.cn)")
    logger.info(f"[Relay] 代理环境变量已清除: HTTP_PROXY, HTTPS_PROXY 等")

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=args.port)
