import asyncio
from typing import Optional, List, Dict
from datetime import datetime
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class AKShareProvider:
    def __init__(self):
        self.name = "akshare"
        self.description = "A股数据主力源（免费无限）"
        self._ak = None
    
    def _get_ak(self):
        if self._ak is None:
            import akshare as ak
            self._ak = ak
        return self._ak
    
    async def get_realtime_quote(self, symbol: str) -> Optional[Dict]:
        try:
            ak = self._get_ak()
            loop = asyncio.get_event_loop()
            
            df = await loop.run_in_executor(None, lambda: ak.stock_zh_a_spot_em())
            
            if df is not None and not df.empty:
                stock_data = df[df['代码'] == symbol]
                
                if not stock_data.empty:
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
            
            logger.warning(f"AKShare未找到{symbol}的实时行情")
            return None
            
        except Exception as e:
            logger.error(f"AKShare获取{symbol}实时行情失败: {e}")
            raise
    
    async def get_history_kline(self, symbol: str, period: str = "daily", days: int = 30, adjust: str = "qfq") -> Optional[pd.DataFrame]:
        try:
            ak = self._get_ak()
            loop = asyncio.get_event_loop()
            
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - __import__('datetime').timedelta(days=days)).strftime("%Y%m%d")
            
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_zh_a_hist(symbol=symbol, period=period, start_date=start_date, end_date=end_date, adjust=adjust)
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
    
    async def get_stock_list(self) -> List[Dict]:
        try:
            ak = self._get_ak()
            loop = asyncio.get_event_loop()
            
            df = await loop.run_in_executor(None, lambda: ak.stock_zh_a_spot_em())
            
            if df is not None and not df.empty:
                stocks = []
                for _, row in df.head(100).iterrows():
                    stocks.append({
                        'symbol': row.get('代码', ''),
                        'name': row.get('名称', ''),
                        'price': float(row.get('最新价', 0)),
                        'change_pct': float(row.get('涨跌幅', 0)),
                        'market_cap': float(row.get('总市值', 0)) if row.get('总市值') else 0
                    })
                
                sorted_stocks = sorted(stocks, key=lambda x: x['market_cap'], reverse=True)
                return sorted_stocks[:50]
            
            return []
            
        except Exception as e:
            logger.error(f"AKShare获取股票列表失败: {e}")
            raise
    
    async def get_market_index(self) -> List[Dict]:
        indices = [
            {'name': '上证指数', 'code': '000001', 'price': 3100.5, 'change_pct': -0.25},
            {'name': '深证成指', 'code': '399001', 'price': 9800.2, 'change_pct': 0.15},
            {'name': '创业板指', 'code': '399006', 'price': 1920.8, 'change_pct': 0.42}
        ]
        return indices
    
    async def close(self):
        pass
