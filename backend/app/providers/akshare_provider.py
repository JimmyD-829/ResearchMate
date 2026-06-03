"""
AKShare数据提供者 - V2 双模式版

运行模式（由环境变量自动切换）：
  1. 直连模式（默认）: 本地直接调用AKShare库 → 需要国内网络
  2. 代理模式: 通过Relay中转服务获取数据 → 海外服务器可用

环境变量控制：
  AKSHARE_RELAY_URL   - 设置后启用代理模式，如 http://your-cn-server:8899
  AKSHARE_RELAY_KEY   - Relay认证密钥（需与Relay端一致）
"""

import os
import asyncio
import logging
from typing import Optional, List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class AKShareProvider:
    """
    AKShare 数据提供者 - 支持直连/代理双模式

    模式自动选择逻辑：
    ┌────────────────────────────────────────────────────┐
    │ AKSHARE_RELAY_URL 已设置？                          │
    │   YES → 代理模式 (HTTP调用国内Relay)                │
    │   NO  → 直连模式 (本地AKShare库)                    │
    └────────────────────────────────────────────────────┘
    """

    def __init__(self):
        self.relay_url = os.environ.get("AKSHARE_RELAY_URL", "").rstrip("/")
        self.relay_key = os.environ.get("AKSHARE_RELAY_KEY", "researchmate-relay-2026")

        if self.relay_url:
            self.mode = "proxy"
            self.name = "akshare-proxy"
            self.description = f"A股数据(代理模式→{self.relay_url})"
            logger.info(f"📡 AKShareProvider 启用[代理模式] → {self.relay_url}")
        else:
            self.mode = "direct"
            self.name = "akshare"
            self.description = "A股数据(直连模式)"
            self._ak = None
            logger.info(f"🔗 AKShareProvider 启用[直连模式]")

        # 代理模式使用requests库（aiohttp在Render上连ngrok不稳定）
        self._relay_headers = {
            "X-Relay-Key": self.relay_key,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "ngrok-skip-browser-warning": "1",  # 绕过ngrok免费版警告页
        }

    # ==================== 代理模式：HTTP客户端 (requests) ====================

    def _get_session(self):
        """创建不读取代理环境变量的Session（兼容旧版requests）"""
        import requests
        s = requests.Session()
        s.trust_env = False  # 忽略HTTP_PROXY等，直连ngrok
        s.headers.update(self._relay_headers)
        logger.debug(f"[RelayClient] Session创建 trust_env=False, headers={list(self._relay_headers.keys())}")
        return s

    def _http_get(self, url: str, params: Dict = None) -> Optional[Dict]:
        """同步GET请求Relay"""
        import time as _time
        _t0 = _time.time()
        session = self._get_session()
        try:
            full_url = f"{url}?{self._encode_params(params)}" if params else url
            logger.info(f"[RelayClient] GET {full_url[:120]}")
            resp = session.get(url, params=params, timeout=20)
            elapsed = round((_time.time() - _t0) * 1000)
            if resp.status_code == 200:
                data = resp.json().get("data")
                source = data.get("source", "unknown") if isinstance(data, dict) else "unknown"
                name = data.get("name", "") if isinstance(data, dict) else ""
                price = data.get("price") if isinstance(data, dict) else None
                logger.info(f"[RelayClient] GET OK {resp.status_code} ({elapsed}ms) source={source} name={name} price={price} size={len(resp.content)}B")
                return data
            elif resp.status_code == 404:
                logger.warning(f"[RelayClient] GET 404 Not Found: {full_url[:100]}")
                return None
            else:
                logger.warning(f"[RelayClient] GET 返回 {resp.status_code} ({elapsed}ms): {resp.text[:200]}")
                return None
        except Exception as e:
            elapsed = round((_time.time() - _t0) * 1000)
            logger.error(f"[RelayClient] GET 失败 ({elapsed}ms): {url[:100]} -> {type(e).__name__}: {e}")
            return None
        finally:
            session.close()

    def _http_post(self, url: str, json_body: Dict) -> Optional[Dict]:
        """同步POST请求Relay"""
        import time as _time
        _t0 = _time.time()
        session = self._get_session()
        try:
            symbols = json_body.get("symbols", []) if json_body else []
            logger.info(f"[RelayClient] POST {url[:120]} symbols={symbols}")
            resp = session.post(url, json=json_body, timeout=20)
            elapsed = round((_time.time() - _t0) * 1000)
            if resp.status_code == 200:
                data = resp.json().get("data")
                count = len(data) if isinstance(data, dict) else 0
                logger.info(f"[RelayClient] POST OK {resp.status_code} ({elapsed}ms) returned={count} symbols size={len(resp.content)}B")
                return data
            else:
                logger.warning(f"[RelayClient] POST 返回 {resp.status_code} ({elapsed}ms): {resp.text[:200]}")
                return None
        except Exception as e:
            elapsed = round((_time.time() - _t0) * 1000)
            logger.error(f"[RelayClient] POST 失败 ({elapsed}ms): {url[:100]} -> {type(e).__name__}: {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def _encode_params(params: Dict) -> str:
        """URL编码参数（仅用于日志显示）"""
        if not params:
            return ""
        from urllib.parse import urlencode
        return urlencode(params)

    async def _relay_get(self, path: str, params: Dict = None) -> Optional[Dict]:
        """向Relay发送GET请求（异步包装）"""
        url = f"{self.relay_url}{path}"
        logger.debug(f"[RelayClient] 异步GET调度: {path} params={params}")
        loop = asyncio.get_event_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(self._http_get, url, params)
            return await loop.run_in_executor(None, lambda: future.result())

    async def _relay_post(self, path: str, json_body: Dict) -> Optional[Dict]:
        """向Relay发送POST请求（异步包装）"""
        url = f"{self.relay_url}{path}"
        logger.debug(f"[RelayClient] 异步POST调度: {path} symbols={json_body.get('symbols', []) if json_body else []}")
        loop = asyncio.get_event_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(self._http_post, url, json_body)
            return await loop.run_in_executor(None, lambda: future.result())

    # ==================== 直连模式：本地AKShare库 ====================

    def _get_ak(self):
        if self._ak is None:
            import akshare as ak
            self._ak = ak
        return self._ak

    async def _run_sync(self, func, *args, **kwargs):
        """在线程池中执行同步AKShare调用"""
        loop = asyncio.get_event_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            future = pool.submit(func, *args, **kwargs)
            return await loop.run_in_executor(None, lambda: future.result())

    def _extract_quote_from_df(self, df, symbol: str) -> Optional[Dict]:
        """从DataFrame中提取单只股票行情（两种模式共用格式）"""
        if df is None or df.empty:
            return None
        stock_data = df[df['代码'] == symbol]
        if stock_data.empty:
            return None
        row = stock_data.iloc[0]
        return {
            'symbol': symbol,
            'name': row.get('名称', ''),
            'price': float(row.get('最新价', 0)),
            'change_pct': float(row.get('涨跌幅', 0)),
            'change_amount': float(row.get('涨跌额', 0)),
            'volume': float(row.get('成交量', 0)),
            'turnover': float(row.get('成交额', 0)),
            'high': float(row.get('最高', 0)),
            'low': float(row.get('最低', 0)),
            'open': float(row.get('今开', 0)),
            'prev_close': float(row.get('昨收', 0)),
            'amplitude': float(row.get('振幅', 0)),
            'turnover_rate': float(row.get('换手率', 0)),
            'pe_ratio': float(row.get('市盈率-动态', 0)) if row.get('市盈率-动态') else None,
            'market_cap': float(row.get('总市值', 0)) if row.get('总市值') else None,
            'circulating_cap': float(row.get('流通市值', 0)) if row.get('流通市值') else None,
            'rise_speed': float(row.get('涨速', 0)) if row.get('涨速') else None,
            'volume_ratio': float(row.get('量比', 0)) if row.get('量比') else None,
            'update_time': datetime.now().isoformat(),
            'source': 'akshare'
        }

    # ==================== 公共接口（自动路由到对应模式）====================

    async def get_realtime_quote(self, symbol: str) -> Optional[Dict]:
        """
        获取单股实时行情

        代理模式: GET /api/stock/quote?symbol=xxx
        直连模式: ak.stock_zh_a_spot_em() + 过滤
        """
        logger.info(f"[AKShareProvider] get_realtime_quote(symbol={symbol}) mode={self.mode}")
        if self.mode == "proxy":
            data = await self._relay_get("/api/stock/quote", {"symbol": symbol})
            if data:
                data["source"] = "akshare-relay"
                logger.info(f"[AKShareProvider] quote OK {symbol} name={data.get('name','')} price={data.get('price')}")
            else:
                logger.warning(f"[AKShareProvider] quote 返回空 {symbol}")
            return data

        # 直连模式
        try:
            ak = self._get_ak()
            df = await self._run_sync(lambda: ak.stock_zh_a_spot_em())
            result = self._extract_quote_from_df(df, symbol)
            if not result:
                logger.warning(f"AKShare未找到{symbol}的实时行情")
            return result
        except Exception as e:
            logger.error(f"AKShare获取{symbol}实时行情失败: {e}")
            raise

    async def get_history_kline(self, symbol: str, period: str = "daily",
                                 days: int = 30, adjust: str = "qfq"):
        """
        获取历史K线

        代理模式: GET /api/stock/kline?symbol=xxx&days=30
        直连模式: ak.stock_zh_a_hist()
        """
        import pandas as pd
        logger.info(f"[AKShareProvider] get_history_kline(symbol={symbol} days={days} adjust={adjust}) mode={self.mode}")

        if self.mode == "proxy":
            data = await self._relay_get("/api/stock/kline", {
                "symbol": symbol, "days": days, "adjust": adjust
            })
            if data and data.get("records"):
                df = pd.DataFrame(data["records"])
                if not df.empty and '日期' in df.columns:
                    df['日期'] = pd.to_datetime(df['日期'])
                    df = df.sort_values('日期', ascending=False)
                logger.info(f"[AKShareProvider] kline OK {symbol} records={len(data['records'])}")
                return df
            logger.warning(f"[AKShareProvider] kline 返回空 {symbol}")
            return None

        # 直连模式
        try:
            ak = self._get_ak()
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - __import__('datetime').timedelta(days=days)).strftime("%Y%m%d")

            df = await self._run_sync(
                lambda: ak.stock_zh_a_hist(symbol=symbol, period=period,
                                           start_date=start_date, end_date=end_date, adjust=adjust)
            )
            if df is not None and not df.empty:
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.sort_values('日期', ascending=False)
                return df

            logger.warning(f"AKShare未找到{symbol}的历史K线")
            return None
        except Exception as e:
            logger.error(f"AKShare获取{symbol}历史K线失败: {e}")
            raise

    async def get_stock_list(self, top: int = 50) -> List[Dict]:
        """
        获取A股市值排名列表

        代理模式: GET /api/stock/list?top=50
        直连模式: ak.stock_zh_a_spot_em() + 排序
        """
        logger.info(f"[AKShareProvider] get_stock_list(top={top}) mode={self.mode}")
        if self.mode == "proxy":
            data = await self._relay_get("/api/stock/list", {"top": top})
            result = data if isinstance(data, list) else []
            logger.info(f"[AKShareProvider] stock_list OK count={len(result)}")
            return result

        # 直连模式
        try:
            ak = self._get_ak()
            df = await self._run_sync(lambda: ak.stock_zh_a_spot_em())
            if df is None or df.empty:
                return []

            stocks = []
            for _, row in df.head(100).iterrows():
                stocks.append({
                    'symbol': row.get('代码', ''),
                    'name': row.get('名称', ''),
                    'price': float(row.get('最新价', 0)),
                    'change_pct': float(row.get('涨跌幅', 0)),
                    'market_cap': float(row.get('总市值', 0)) if row.get("总市值") else 0
                })

            stocks.sort(key=lambda x: x['market_cap'], reverse=True)
            return stocks[:top]
        except Exception as e:
            logger.error(f"AKShare获取股票列表失败: {e}")
            raise

    async def get_market_index(self) -> List[Dict]:
        """大盘指数"""
        indices = [
            {'name': '上证指数', 'code': '000001', 'price': 3100.5, 'change_pct': -0.25},
            {'name': '深证成指', 'code': '399001', 'price': 9800.2, 'change_pct': 0.15},
            {'name': '创业板指', 'code': '399006', 'price': 1920.8, 'change_pct': 0.42}
        ]
        return indices

    async def batch_quotes(self, symbols: List[str]) -> Dict[str, Optional[Dict]]:
        """
        批量查询多只股票行情

        代理模式: 单次POST请求（高效）
        直连模式: 获取全量再过滤
        """
        logger.info(f"[AKShareProvider] batch_quotes(symbols={symbols}) mode={self.mode}")
        if self.mode == "proxy":
            data = await self._relay_post("/api/stock/batch", {"symbols": symbols})
            result = data if isinstance(data, dict) else {}
            ok_count = sum(1 for v in result.values() if v is not None)
            logger.info(f"[AKShareProvider] batch_quotes OK total={len(symbols)} got={ok_count}")
            return result

        # 直连模式：走全量拉取+过滤
        try:
            results = {}
            ak = self._get_ak()
            df = await self._run_sync(lambda: ak.stock_zh_a_spot_em())
            for symbol in symbols:
                quote = self._extract_quote_from_df(df, symbol)
                results[symbol] = quote
            return results
        except Exception as e:
            logger.error(f"批量查询失败: {e}")
            return {s: None for s in symbols}

    async def health_check(self) -> Dict:
        """检查数据源连通性"""
        if self.mode == "proxy":
            import time as _time
            _t0 = _time.time()
            try:
                import requests
                s = requests.Session()
                s.trust_env = False
                s.headers.update(self._relay_headers)
                r = s.get(f"{self.relay_url}/health", timeout=10)
                elapsed = round((_time.time() - _t0) * 1000)
                s.close()
                if r.status_code == 200:
                    body = r.json()
                    logger.info(f"[AKShareProvider] health_check OK ({elapsed}ms) relay={body.get('service')} ds={body.get('data_source')}")
                    return {"mode": "proxy", "status": "ok", "url": self.relay_url, "relay_info": body}
                logger.warning(f"[AKShareProvider] health_check FAIL HTTP {r.status_code} ({elapsed}ms)")
                return {"mode": "proxy", "status": "error", "http_status": r.status_code}
            except Exception as e:
                elapsed = round((_time.time() - _t0) * 1000)
                logger.error(f"[AKShareProvider] health_check ERROR ({elapsed}ms): {type(e).__name__}: {e}")
                return {"mode": "proxy", "status": "error", "detail": str(e)[:100]}

        # 直连模式
        try:
            ak = self._get_ak()
            await self._run_sync(lambda: ak.stock_zh_a_spot_em())
            return {"mode": "direct", "status": "ok"}
        except Exception as e:
            return {"mode": "direct", "status": "error", "detail": str(e)[:100]}

    async def close(self):
        """清理资源"""
        if self._session and not self._session.closed:
            await self._session.close()
