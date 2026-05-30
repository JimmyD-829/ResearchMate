import os
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
            
            quote = data.get('Global Quote', {})
            if quote and '01. symbol' in quote:
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
