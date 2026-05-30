"""
数据API路由 - 提供真实金融数据接口
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
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
    try:
        data = None
        source = "unknown"
        
        if _is_cn_stock(symbol):
            data = await akshare_provider.get_realtime_quote(symbol)
            source = "akshare"
        else:
            data = await alpha_vantage_provider.get_us_stock_quote(symbol)
            source = "alpha_vantage"
        
        if data:
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
            raise HTTPException(status_code=404, detail=f"未找到{symbol}的行情数据")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取{symbol}实时行情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取行情数据失败: {str(e)}")

@router.get("/history/{symbol}")
async def get_history_kline(
    symbol: str,
    period: str = Query("daily", description="K线周期"),
    days: int = Query(30, ge=1, le=365),
    adjust: str = Query("qfq", description="复权方式")
):
    try:
        if not _is_cn_stock(symbol):
            raise HTTPException(status_code=400, detail="历史K线目前仅支持A股")
        
        df = await akshare_provider.get_history_kline(symbol=symbol, period=period, days=days, adjust=adjust)
        
        if df is not None and not df.empty:
            records = df.to_dict('records')
            
            return {
                "success": True,
                "data": records,
                "summary": {"total_records": len(records), "symbol": symbol, "source": "akshare"},
                "metadata": {"source": "akshare", "update_time": datetime.now().isoformat()}
            }
        else:
            raise HTTPException(status_code=404, detail=f"未找到{symbol}的历史数据")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取{symbol}历史K线失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stocks")
async def get_stock_list(limit: int = Query(50, ge=1, le=200)):
    try:
        stocks = await akshare_provider.get_stock_list()
        
        if stocks:
            return {
                "success": True,
                "data": stocks[:limit],
                "total": len(stocks),
                "metadata": {"source": "akshare", "update_time": datetime.now().isoformat()}
            }
        else:
            return {"success": True, "data": [], "total": 0, "message": "暂时无法获取股票列表"}
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        return {"success": False, "error": str(e), "data": [], "fallback_available": True}

@router.get("/market-index")
async def get_market_index():
    try:
        indices = await akshare_provider.get_market_index()
        return {"success": True, "data": indices, "metadata": {"source": "akshare"}}
    except Exception as e:
        logger.error(f"获取市场指数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/company/{symbol}")
async def get_company_overview(symbol: str):
    try:
        data = None
        source = "unknown"
        
        if _is_us_stock(symbol):
            data = await alpha_vantage_provider.get_company_overview(symbol)
            source = "alpha_vantage"
        else:
            quote_data = await akshare_provider.get_realtime_quote(symbol)
            if quote_data:
                data = {'symbol': symbol, 'name': quote_data.get('name', ''), 'price': quote_data.get('price'), 'market_cap': quote_data.get('market_cap'), 'pe_ratio': quote_data.get('pe_ratio'), 'source': 'akshare'}
                source = "akshare"
        
        if data:
            return {"success": True, "data": data, "metadata": {"source": source}}
        else:
            raise HTTPException(status_code=404, detail=f"未找到{symbol}的公司信息")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取{symbol}公司信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _is_cn_stock(symbol: str) -> bool:
    symbol = str(symbol).upper()
    return (symbol.isdigit() and len(symbol) == 6) or (symbol.startswith(('SH', 'SZ'))) or (len(symbol) == 6 and symbol[0] in ('0', '3', '6'))

def _is_us_stock(symbol: str) -> bool:
    symbol = str(symbol).upper()
    us_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM']
    return symbol in us_stocks or (symbol.isalpha() and len(symbol) <= 5)

@router.on_event("shutdown")
async def shutdown_event():
    await alpha_vantage_provider.close()

