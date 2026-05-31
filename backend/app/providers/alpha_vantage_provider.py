"""
Alpha Vantage数据提供者

适用场景：
- 美股实时行情
- 全球市场数据
- 外汇汇率
- 公司基本面数据

免费版限制：25次/天
"""

import os
import json
import httpx
from typing import Optional, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AlphaVantageProvider:
    BASE_URL = "https://www.alphavantage.co/query"
    FREE_TIER_DAILY_LIMIT = 25
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY', '')
        self.name = "alpha_vantage"
        self.description = "美股及全球数据补充源（免费25次/天）"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.daily_call_count = 0
        self.last_reset_date = datetime.now().date()
    
    async def _check_rate_limit(self):
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_call_count = 0
            self.last_reset_date = today
        
        if self.daily_call_count >= self.FREE_TIER_DAILY_LIMIT:
            raise Exception(f"Alpha Vantage每日调用限制已用完（{self.FREE_TIER_DAILY_LIMIT}次/天）")
    
    async def _make_request(self, params: dict) -> dict:
        await self._check_rate_limit()
        
        params['apikey'] = self.api_key
        
        try:
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data:
                raise Exception(data['Error Message'])
            
            if 'Note' in data and 'API call frequency' in data['Note']:
                raise Exception(data['Note'])
            
            self.daily_call_count += 1
            
            return data
            
        except httpx.HTTPError as e:
            logger.error(f"Alpha Vantage HTTP请求失败: {e}")
            raise
    
    async def get_us_stock_quote(self, symbol: str) -> Optional[Dict]:
        try:
            data = await self._make_request({
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol
            })
            
            logger.info(f"📦 Alpha Vantage原始响应 ({symbol}): {json.dumps(data, ensure_ascii=False)[:500]}")
            
            quote = data.get('Global Quote', {})
            logger.info(f"🔍 Global Quote字段: {quote}")
            
            if quote and '01. symbol' in quote:
                logger.info(f"✅ 成功解析{symbol}行情数据: price={quote.get('05. price')}")
                return {
                    'symbol': quote.get('01. symbol'),
                    'open': float(quote.get('02. open', 0)),
                    'high': float(quote.get('03. high', 0)),
                    'low': float(quote.get('04. low', 0)),
                    'price': float(quote.get('05. price', 0)),
                    'volume': int(quote.get('06. volume', 0)),
                    'latest_trading_day': quote.get('07. latest trading day'),
                    'prev_close': float(quote.get('08. previous close', 0)),
                    'change': float(quote.get('09. change', 0)),
                    'change_percent': float(quote.get('10. change percent', '0%').replace('%', '')),
                    'source': 'alpha_vantage',
                    'update_time': datetime.now().isoformat()
                }
                
            logger.warning(f"Alpha Vantage未找到{symbol}的行情数据")
            logger.warning(f"   原始数据keys: {list(data.keys()) if data else 'None'}")
            logger.warning(f"   Global Quote内容: {quote if quote else 'Empty/None'}")
            if 'Note' in data:
                logger.warning(f"   ⚠️ API限制: {data['Note']}")
            return None
            
        except Exception as e:
            logger.error(f"Alpha Vantage获取{symbol}行情失败: {e}")
    
    async def get_company_overview(self, symbol: str) -> Optional[Dict]:
        try:
            data = await self._make_request({
                'function': 'OVERVIEW',
                'symbol': symbol
            })
            
            if not data or 'Symbol' not in data:
                return None
            
            return {
                'symbol': data.get('Symbol'),
                'name': data.get('Name'),
                'description': data.get('Description', '')[:500],
                'exchange': data.get('Exchange'),
                'currency': data.get('Currency'),
                'country': data.get('Country'),
                'sector': data.get('Sector'),
                'industry': data.get('Industry'),
                'market_cap': float(data.get('MarketCapitalization', 0)) if data.get('MarketCapitalization') else None,
                'pe_ratio': float(data.get('PERatio', 0)) if data.get('PERatio') else None,
                'peg_ratio': float(data.get('PEGRatio', 0)) if data.get('PEGRatio') else None,
                'book_value': float(data.get('BookValue', 0)) if data.get('BookValue') else None,
                'dividend_per_share': float(data.get('DividendPerShare', 0)) if data.get('DividendPerShare') else None,
                'dividend_yield': float(data.get('DividendYield', 0)) if data.get('DividendYield') else None,
                'eps': float(data.get('EPS', 0)) if data.get('EPS') else None,
                'revenue_per_share_ttm': float(data.get('RevenuePerShareTTM', 0)) if data.get('RevenuePerShareTTM') else None,
                'profit_margin': float(data.get('ProfitMargin', 0)) if data.get('ProfitMargin') else None,
                'operating_margin_ttm': float(data.get('OperatingMarginTTM', 0)) if data.get('OperatingMarginTTM') else None,
                'return_on_assets_ttm': float(data.get('ReturnOnAssetsTTM', 0)) if data.get('ReturnOnAssetsTTM') else None,
                'return_on_equity_ttm': float(data.get('ReturnOnEquityTTM', 0)) if data.get('ReturnOnEquityTTM') else None,
                'revenue_ttm': float(data.get('RevenueTTM', 0)) if data.get('RevenueTTM') else None,
                'gross_profit_ttm': float(data.get('GrossProfitTTM', 0)) if data.get('GrossProfitTTM') else None,
                'ebitda': float(data.get('EBITDA', 0)) if data.get('EBITDA') else None,
                'total_debt': float(data.get('TotalDebt', 0)) if data.get('TotalDebt') else None,
                'total_receivable': float(data.get('TotalReceivable', 0)) if data.get('TotalReceivable') else None,
                'current_ratio': float(data.get('CurrentRatio', 0)) if data.get('CurrentRatio') else None,
                'operating_cashflow_ttm': float(data.get('OperatingCashflowTTM', 0)) if data.get('OperatingCashflowTTM') else None,
                'free_cashflow_ttm': float(data.get('FreeCashflowTTM', 0)) if data.get('FreeCashflowTTM') else None,
                '52_week_high': float(data.get('52WeekHigh', 0)) if data.get('52WeekHigh') else None,
                '52_week_low': float(data.get('52WeekLow', 0)) if data.get('52WeekLow') else None,
                '50_day_moving_avg': float(data.get('50DayMovingAverage', 0)) if data.get('50DayMovingAverage') else None,
                '200_day_moving_avg': float(data.get('200DayMovingAverage', 0)) if data.get('200DayMovingAverage') else None,
                'shares_outstanding': float(data.get('SharesOutstanding', 0)) if data.get('SharesOutstanding') else None,
                'source': 'alpha_vantage',
                'update_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Alpha Vantage获取{symbol}公司概览失败: {e}")
    
    async def get_forex_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        try:
            data = await self._make_request({
                'function': 'CURRENCY_EXCHANGE_RATE',
                'from_currency': from_currency,
                'to_currency': to_currency
            })
            
            exchange_data = data.get('Realtime Currency Exchange Rate', {})
            if exchange_data and '5. Exchange Rate' in exchange_data:
                rate = float(exchange_data['5. Exchange Rate'])
                return rate
                
            return None
            
        except Exception as e:
            logger.error(f"Alpha Vantage获取汇率失败: {e}")
    
    async def close(self):
        await self.client.aclose()
