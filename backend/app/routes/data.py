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
    """
    获取股票实时行情
    
    支持A股代码（如600519）和美股代码（如AAPL）
    自动识别市场并选择合适的数据源
    """
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
    """调试端点：测试Render到Relay的连通性"""
    import os
    result = {
        "env": {
            "AKSHARE_RELAY_URL": os.environ.get("AKSHARE_RELAY_URL", "(not set)"),
            "AKSHARE_RELAY_KEY": os.environ.get("AKSHARE_RELAY_KEY", "(not set)")[:10] + "...",
            "HTTP_PROXY": os.environ.get("HTTP_PROXY", "(not set)"),
            "HTTPS_PROXY": os.environ.get("HTTPS_PROXY", "(not set)"),
        },
        "provider_mode": akshare_provider.mode,
        "provider_url": getattr(akshare_provider, 'relay_url', 'N/A'),
        "relay_health": None,
        "relay_quote_test": None,
        "error": None,
    }
    # 测试1: 直接requests调Relay health
    try:
        import requests
        url = akshare_provider.relay_url + "/health"
        r = requests.get(url, headers={"X-Relay-Key": akshare_provider.relay_key},
                        timeout=20, trust_env=False)
        result["relay_health"] = {"status": r.status_code, "body": r.text[:200]}
    except Exception as e:
        result["error"] = f"health check: {e}"

    # 测试2: 调quote接口
    try:
        import requests
        url = akshare_provider.relay_url + "/api/stock/quote"
        r = requests.get(url, params={"symbol": "600519"},
                        headers={"X-Relay-Key": akshare_provider.relay_key},
                        timeout=20, trust_env=False)
        result["relay_quote_test"] = {"status": r.status_code, "body": r.text[:300]}
    except Exception as e:
        if not result["error"]:
            result["error"] = f"quote test: {e}"
        else:
            result["error"] += f" | quote: {e}"

    return result

@router.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    await alpha_vantage_provider.close()
