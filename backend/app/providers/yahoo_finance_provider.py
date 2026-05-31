#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yahoo Finance数据提供者 - Alpha Vantage的免费无限制备用方案

特点：
- 完全免费，无API Key要求
- 无请求频率限制
- 数据来源可靠（Yahoo Finance）
- 作为Alpha Vantage的主要备用数据源

适用场景：
- Alpha Vantage API配额耗尽时
- 需要高频次访问时
- 作为主要数据源（推荐）
"""

import httpx
from typing import Optional, Dict, List
from datetime import datetime
import logging
import json
import re

logger = logging.getLogger(__name__)

class YahooFinanceProvider:
    """
    Yahoo Finance 数据提供者
    
    使用Yahoo Finance的公开API获取股票数据
    """
    
    BASE_URL = "https://query1.finance.yahoo.com"
    V8_FINANCE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    
    def __init__(self):
        self.name = "yahoo_finance"
        self.description = "Yahoo Finance (免费无限制)"
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # 模拟浏览器User-Agent避免被拦截
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://finance.yahoo.com/'
        }
        
        logger.info("📈 Yahoo Finance Provider 初始化完成")
    
    async def get_us_stock_quote(self, symbol: str) -> Optional[Dict]:
        """
        获取美股实时行情
        
        Args:
            symbol: 股票代码 (如 BABA, MSFT, AAPL)
            
        Returns:
            行情字典或None
        """
        try:
            from ..utils.smart_cache import get_cache
            
            cache = get_cache()
            cache_key = f"yahoo_quote_{symbol}"
            
            # 检查缓存
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                logger.info(f"✨ [Yahoo] 使用缓存 ({symbol}): ${cached_data.get('price')}")
                return cached_data
            
            # 调用Yahoo Finance V8 API
            url = self.V8_FINANCE_URL.format(symbol=symbol)
            params = {
                'interval': '1d',
                'range': '1d'
            }
            
            response = await self.client.get(
                url,
                params=params,
                headers=self.headers,
                follow_redirects=True
            )
            
            if response.status_code != 200:
                logger.warning(f"[Yahoo] HTTP错误 {symbol}: {response.status_code}")
                return None
            
            data = response.json()
            
            # 解析V8 Finance API响应
            result = data.get('chart', {}).get('result', [])
            if not result:
                logger.warning(f"[Yahoo] 未找到 {symbol} 的数据")
                return None
            
            meta = result[0].get('meta', {})
            if not meta or 'regularMarketPrice' not in meta:
                logger.warning(f"[Yahoo] {symbol} 数据格式异常")
                return None
            
            # 构建标准化的行情数据
            quote = {
                'symbol': symbol,
                'open': float(meta.get('regularMarketOpen', 0)),
                'high': float(meta.get('dayHigh', 0)),
                'low': float(meta.get('dayLow', 0)),
                'price': float(meta.get('regularMarketPrice', 0)),
                'volume': int(meta.get('regularMarketVolume', 0)),
                'latest_trading_day': datetime.fromtimestamp(
                    meta.get('regularMarketTime', 0)
                ).strftime('%Y-%m-%d') if meta.get('regularMarketTime') else None,
                'prev_close': float(meta.get('previousClose', 0)),
                'change': float(meta.get('regularMarketPrice', 0)) - float(meta.get('previousClose', 0)),
                'source': 'yahoo_finance',
                'update_time': datetime.now().isoformat()
            }
            
            # 计算涨跌幅
            if quote['prev_close'] > 0:
                quote['change_percent'] = round(
                    (quote['price'] - quote['prev_close']) / quote['prev_close'] * 100, 2
                )
            else:
                quote['change_percent'] = 0.0
            
            # 存入缓存（15分钟）
            cache.set(cache_key, quote, ttl=15 * 60)
            
            logger.info(f"✅ [Yahoo] 成功获取 {symbol} 行情: ${quote['price']} ({quote['change_percent']}%)")
            
            return quote
            
        except Exception as e:
            logger.error(f"[Yahoo] 获取{symbol}行情失败: {e}", exc_info=True)
            return None
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


# 测试代码
if __name__ == '__main__':
    import asyncio
    
    async def test_yahoo_finance():
        print("\n" + "="*80)
        print("测试 Yahoo Finance Provider")
        print("="*80)
        
        provider = YahooFinanceProvider()
        
        try:
            # 测试BABA
            print(f"\n📊 测试 BABA (阿里巴巴):")
            baba = await provider.get_us_stock_quote('BABA')
            if baba:
                print(f"✅ 成功!")
                print(f"   价格: ${baba['price']}")
                print(f"   涨跌: {baba['change_percent']}%")
                print(f"   成交量: {baba['volume']:,}")
            else:
                print(f"❌ 失败")
            
            # 测试MSFT
            print(f"\n📊 测试 MSFT (微软):")
            msft = await provider.get_us_stock_quote('MSFT')
            if msft:
                print(f"✅ 成功!")
                print(f"   价格: ${msft['price']}")
                print(f"   涨跌: {msft['change_percent']}%")
            else:
                print(f"❌ 失败")
                
        finally:
            await provider.close()
    
    asyncio.run(test_yahoo_finance())
