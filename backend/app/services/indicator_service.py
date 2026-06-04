"""
技术指标计算服务

支持指标：MA、MACD、RSI、KDJ、BOLL
所有公式遵循业界标准，与同花顺/东方财富/TradingView 计算逻辑一致。

输入：K线 DataFrame（需包含列：日期、开盘、收盘、最高、最低、成交量）
输出：各指标的 Series / DataFrame + 信号解读
"""

import math
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class IndicatorService:
    """技术指标计算引擎 — 纯 Python 实现，无第三方依赖"""

    # ──────────────────────────────────────────────
    # MA 移动平均线
    # ──────────────────────────────────────────────

    @staticmethod
    def ma(close_prices: List[float], period: int) -> Optional[List[Optional[float]]]:
        """
        简单移动平均线 SMA
        MA(N) = 最近N日收盘价的算术平均值

        Args:
            close_prices: 收盘价列表（从旧到新排列）
            period: 周期 (5/10/20/60)
        Returns:
            与输入等长的列表，前 period-1 个值为 None
        """
        if len(close_prices) < period:
            return [None] * len(close_prices)

        result = []
        for i in range(len(close_prices)):
            if i < period - 1:
                result.append(None)
            else:
                window = close_prices[i - period + 1:i + 1]
                result.append(round(sum(window) / period, 4))
        return result

    @staticmethod
    def detect_ma_signal(ma_short: List[Optional[float]],
                         ma_long: List[Optional[float]]) -> Dict[str, Any]:
        """
        检测均线金叉/死叉信号

        Returns:
            {
                "signal": "golden_cross" | "death_cross" | "none",
                "date": str | None,
                "description": str
            }
        """
        for i in range(1, len(ma_short)):
            s_prev, s_curr = ma_short[i - 1], ma_short[i]
            l_prev, l_curr = ma_long[i - 1], ma_long[i]

            if any(v is None for v in (s_prev, s_curr, l_prev, l_curr)):
                continue

            # 金叉：短期均线上穿长期均线
            if s_prev <= l_prev and s_curr > l_curr:
                return {
                    "signal": "golden_cross",
                    "index": i,
                    "description": f"MA金叉 — 短期均线上穿长期均线，短期看多信号"
                }
            # 死叉：短期均线下穿长期均线
            if s_prev >= l_prev and s_curr < l_curr:
                return {
                    "signal": "death_cross",
                    "index": i,
                    "description": f"MA死叉 — 短期均线下穿长期均线，短期看空信号"
                }

        return {"signal": "none", "index": None, "description": "无交叉信号"}

    # ──────────────────────────────────────────────
    # MACD 指数平滑异同移动平均线
    # ──────────────────────────────────────────────

    @staticmethod
    def macd(close_prices: List[float],
             short_period: int = 12,
             long_period: int = 26,
             signal_period: int = 9) -> Dict[str, List[Optional[float]]]:
        """
        MACD (12, 26, 9)

        EMA(n) = Close * (2/(n+1)) + 前一日EMA * ((n-1)/(n+1))
        DIF = EMA(12) - EMA(26)
        DEA = EMA(DIF, 9)  即 DIF 的信号线
        MACD柱 = (DIF - DEA) * 2

        Returns:
            {"dif": [...], "dea": [...], "histogram": [...]}
        """
        n = len(close_prices)
        ema12 = IndicatorService._ema(close_prices, short_period)
        ema26 = IndicatorService._ema(close_prices, long_period)

        dif = []
        for i in range(n):
            if ema12[i] is None or ema26[i] is None:
                dif.append(None)
            else:
                dif.append(round(ema12[i] - ema26[i], 4))

        dea = IndicatorService._ema([d if d is not None else 0 for d in dif], signal_period,
                                    start_val=None)

        histogram = []
        for i in range(n):
            if dif[i] is None or dea[i] is None:
                histogram.append(None)
            else:
                histogram.append(round((dif[i] - dea[i]) * 2, 4))

        return {"dif": dif, "dea": dea, "histogram": histogram}

    @staticmethod
    def detect_macd_signal(dif: List[Optional[float]],
                           dea: List[Optional[float]],
                           histogram: List[Optional[float]]) -> Dict[str, Any]:
        """
        检测 MACD 金叉/死叉/背离信号
        """
        signal = {"signal": "none", "index": None, "description": "无明显MACD信号"}

        # 金叉/死叉检测
        for i in range(1, len(dif)):
            d_prev, d_curr = dif[i - 1], dif[i]
            e_prev, e_curr = dea[i - 1], dea[i]
            if any(v is None for v in (d_prev, d_curr, e_prev, e_curr)):
                continue

            if d_prev <= e_prev and d_curr > e_curr:
                # 判断是否在零轴下方（低位金叉更可靠）
                zone = "零轴下方" if d_curr < 0 else "零轴上方"
                signal = {
                    "signal": "golden_cross",
                    "index": i,
                    "description": f"MACD金叉({zone}) — DIF上穿DEA，看多信号{'，强度较高' if d_curr < 0 else ''}"
                }
            elif d_prev >= e_prev and d_curr < e_curr:
                zone = "零轴上方" if d_curr > 0 else "零轴下方"
                signal = {
                    "signal": "death_cross",
                    "index": i,
                    "description": f"MACD死叉({zone}) — DIF下穿DEA，看空信号{'，强度较高' if d_curr > 0 else ''}"
                }

        # 柱状图趋势判断
        valid_hist = [h for h in histogram if h is not None]
        if len(valid_hist) >= 3:
            recent = valid_hist[-3:]
            if all(h > 0 for h in recent):
                signal["histogram_trend"] = "red_column_growing"  # 红柱增长
            elif all(h < 0 for h in recent):
                signal["histogram_trend"] = "green_column_growing"  # 绿柱增长

        return signal

    # ──────────────────────────────────────────────
    # RSI 相对强弱指标
    # ──────────────────────────────────────────────

    @staticmethod
    def rsi(close_prices: List[float], period: int = 14) -> List[Optional[float]]:
        """
        Wilder's RSI(14)

        RSI = 100 - 100 / (1 + RS)
        RS = 平均涨幅 / 平均跌幅

        使用 Wilder 平滑方式（非简单SMA）
        """
        n = len(close_prices)
        if n < period + 1:
            return [None] * n

        # 计算每日涨跌
        gains = []
        losses = []
        for i in range(1, n):
            change = close_prices[i] - close_prices[i - 1]
            gains.append(max(change, 0))
            losses.append(max(-change, 0))

        result = [None]  # 第一天没有RSI

        # 第一天用简单平均
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            result.append(round(100 - 100 / (1 + rs), 2))

        # 后续使用平滑平均
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

            if avg_loss == 0:
                result.append(100.0)
            else:
                rs = avg_gain / avg_loss
                result.append(round(100 - 100 / (1 + rs), 2))

        # 补齐前面的None
        while len(result) < n:
            result.insert(0, None)

        return result

    @staticmethod
    def detect_rsi_signal(rsi_values: List[Optional[float]]) -> Dict[str, Any]:
        """
        RSI 超买/超卖判断
        >70 超买 | <30 超卖 | >80 极端超买 | <20 极端超卖
        """
        valid = [v for v in rsi_values if v is not None]
        if not valid:
            return {"signal": "none", "value": None, "description": "数据不足"}

        latest = valid[-1]

        if latest > 80:
            return {
                "signal": "extreme_overbought",
                "value": latest,
                "description": f"RSI={latest:.1f}，极端超买区域，回调风险极高"
            }
        elif latest > 70:
            return {
                "signal": "overbought",
                "value": latest,
                "description": f"RSI={latest:.1f}，超买区域，注意回调风险"
            }
        elif latest < 20:
            return {
                "signal": "extreme_oversold",
                "value": latest,
                "description": f"RSI={latest:.1f}，极端超卖区域，反弹机会较大"
            }
        elif latest < 30:
            return {
                "signal": "oversold",
                "value": latest,
                "description": f"RSI={latest:.1f}，超卖区域，可能存在反弹机会"
            }
        else:
            return {
                "signal": "neutral",
                "value": latest,
                "description": f"RSI={latest:.1f}，中性区域(30-70)"
            }

    # ──────────────────────────────────────────────
    # KDJ 随机指标
    # ──────────────────────────────────────────────

    @staticmethod
    def kdj(high_prices: List[float], low_prices: List[float],
            close_prices: List[float], rsv_period: int = 9,
            k_smooth: int = 3, d_smooth: int = 3) -> Dict[str, List[Optional[float]]]:
        """
        KDJ (9, 3, 3)

        RSV = (Close - Ln) / (Hn - Ln) * 100   (n日内最高/最低价)
        K = 2/3 * 前K + 1/3 * RSV   (首日K=50)
        D = 2/3 * 前D + 1/3 * K      (首日D=50)
        J = 3K - 2D
        """
        n = len(close_prices)
        k_vals = []
        d_vals = []
        j_vals = []

        prev_k = 50.0
        prev_d = 50.0

        for i in range(n):
            if i < rsv_period - 1:
                k_vals.append(None)
                d_vals.append(None)
                j_vals.append(None)
                continue

            # 计算 RSV
            window_high = max(high_prices[i - rsv_period + 1:i + 1])
            window_low = min(low_prices[i - rsv_period + 1:i + 1])
            hl_range = window_high - window_low

            if hl_range == 0:
                rsv = 50.0
            else:
                rsv = (close_prices[i] - window_low) / hl_range * 100

            # K值
            k = (k_smooth - 1) / k_smooth * prev_k + 1 / k_smooth * rsv
            # D值
            d = (d_smooth - 1) / d_smooth * prev_d + 1 / d_smooth * k
            # J值
            j = 3 * k - 2 * d

            k_vals.append(round(k, 2))
            d_vals.append(round(d, 2))
            j_vals.append(round(j, 2))

            prev_k = k
            prev_d = d

        return {"k": k_vals, "d": d_vals, "j": j_vals}

    @staticmethod
    def detect_kdj_signal(k: List[Optional[float]], d: List[Optional[float]],
                          j: List[Optional[float]]) -> Dict[str, Any]:
        """
        KDJ 信号检测
        """
        # 取最近有效值
        def last_valid(arr):
            for v in reversed(arr):
                if v is not None:
                    return v
            return None

        k_latest = last_valid(k)
        d_latest = last_valid(d)
        j_latest = last_valid(j)

        if k_latest is None:
            return {"signal": "none", "description": "数据不足"}

        signals = []

        # K/D 金叉死叉
        for i in range(1, len(k)):
            kp, kc = k[i - 1], k[i]
            dp, dc = d[i - 1], d[i]
            if any(v is None for v in (kp, kc, dp, dc)):
                continue
            if kp <= dp and kc > dc:
                signals.append(("golden_cross", i, "KDJ金叉 — K线上穿D线"))
            elif kp >= dp and kc < dc:
                signals.append(("death_cross", i, "KDJ死叉 — K线下穿D线"))

        # J值超限
        if j_latest is not None:
            if j_latest > 100:
                signals.append(("j_overbought", len(j) - 1, f"J={j_latest:.1f}>100，超买"))
            elif j_latest < 0:
                signals.append(("j_oversold", len(j) - 1, f"J={j_latest:.1f}<0，超卖"))

        if signals:
            latest_sig = signals[-1]
            return {
                "signal": latest_sig[0],
                "index": latest_sig[1],
                "description": latest_sig[2],
                "values": {"K": k_latest, "D": d_latest, "J": j_latest}
            }

        return {
            "signal": "none",
            "values": {"K": k_latest, "D": d_latest, "J": j_latest},
            "description": "无明确KDJ信号"
        }

    # ──────────────────────────────────────────────
    # BOLL 布林带
    # ──────────────────────────────────────────────

    @staticmethod
    def boll(close_prices: List[float], period: int = 20,
             std_dev: float = 2.0) -> Dict[str, List[Optional[float]]]:
        """
        BOLL (20, 2)

        MID = MA(Close, 20)
        UPPER = MID + 2 * STD(Close, 20)
        LOWER = MID - 2 * STD(Close, 20)
        """
        mid = IndicatorService.ma(close_prices, period)

        upper = []
        lower = []
        bandwidth = []  # 带宽 = (UPPER-LOWER)/MID * 100

        for i in range(len(close_prices)):
            if mid[i] is None or i < period - 1:
                upper.append(None)
                lower.append(None)
                bandwidth.append(None)
            else:
                window = close_prices[i - period + 1:i + 1]
                mean = sum(window) / period
                variance = sum((x - mean) ** 2 for x in window) / period
                std = math.sqrt(variance)

                u = round(mean + std_dev * std, 4)
                l = round(mean - std_dev * std, 4)
                upper.append(u)
                lower.append(l)

                bw = round((u - l) / mean * 100, 2) if mean != 0 else None
                bandwidth.append(bw)

        return {"mid": mid, "upper": upper, "lower": lower, "bandwidth": bandwidth}

    @staticmethod
    def detect_boll_signal(close_prices: List[float],
                           upper: List[Optional[float]],
                           lower: List[Optional[float]],
                           bandwidth: List[Optional[float]]) -> Dict[str, Any]:
        """
        BOLL 信号检测：
        - 价格触及上轨 → 压力位
        - 价格触及下轨 → 支撑位
        - 带宽收窄 → 变盘预警
        """
        latest_close = close_prices[-1] if close_prices else None
        latest_upper = None
        latest_lower = None
        latest_bw = None

        for v in reversed(upper):
            if v is not None:
                latest_upper = v
                break
        for v in reversed(lower):
            if v is not None:
                latest_lower = v
                break
        for v in reversed(bandwidth):
            if v is not None:
                latest_bw = v
                break

        if any(v is None for v in (latest_close, latest_upper, latest_lower)):
            return {"signal": "none", "description": "数据不足"}

        signals = []

        # 触及上轨
        if latest_close >= latest_upper * 0.995:
            signals.append(f"价格接近上轨({latest_upper:.2f})，面临压力")
        # 触及下轨
        elif latest_close <= latest_lower * 1.005:
            signals.append(f"价格接近下轨({latest_lower:.2f})，存在支撑")

        # 带宽收窄（变盘信号）
        if latest_bw is not None:
            # 比较近5日带宽均值
            valid_bw = [b for b in bandwidth[-10:] if b is not None]
            if len(valid_bw) >= 5:
                recent_avg = sum(valid_bw[-5:]) / 5
                older_avg = sum(valid_bw[:-5]) / len(valid_bw[:-5]) if len(valid_bw) > 5 else recent_avg
                if older_avg > 0 and recent_avg / older_avg < 0.8:
                    signals.append("布林带宽度持续收窄，可能即将变盘")

        if signals:
            return {
                "signal": "touch_band" if "上轨" in signals[0] or "下轨" in signals[0] else "bandwidth_squeeze",
                "description": "; ".join(signals),
                "bandwidth": latest_bw
            }

        return {
            "signal": "normal",
            "description": f"价格在布林带中轨附近运行，带宽{latest_bw:.1f}%",
            "bandwidth": latest_bw
        }

    # ──────────────────────────────────────────────
    # 区间收益 & 风险指标
    # ──────────────────────────────────────────────

    @staticmethod
    def calculate_risk_metrics(close_prices: List[float],
                               dates: Optional[List[str]] = None,
                               risk_free_rate: float = 0.03) -> Dict[str, Any]:
        """
        计算区间收益和风险指标

        Args:
            close_prices: 收盘价列表（从旧到新）
            dates: 对应日期列表（可选）
            risk_free_rate: 无风险年化利率，默认3%
        """
        n = len(close_prices)
        if n < 5:
            return {"error": "数据不足，至少需要5个交易日"}

        # 日收益率
        daily_returns = []
        for i in range(1, n):
            ret = (close_prices[i] - close_prices[i - 1]) / close_prices[i - 1]
            daily_returns.append(ret)

        # 各区间收益率
        periods = {
            "1M": 21,     # 约1个月交易日
            "3M": 63,     # 约3个月
            "6M": 126,    # 约6个月
            "1Y": 252,    # 约1年
        }

        period_returns = {}
        for label, days in periods.items():
            if n > days:
                start_price = close_prices[n - 1 - days]
                end_price = close_prices[-1]
                pct_return = (end_price - start_price) / start_price * 100
                period_returns[label] = round(pct_return, 2)
            elif n > 1:
                start_price = close_prices[0]
                end_price = close_prices[-1]
                pct_return = (end_price - start_price) / start_price * 100
                period_returns[label] = round(pct_return, 2)
            else:
                period_returns[label] = 0.0

        # 最大回撤
        peak = close_prices[0]
        max_drawdown = 0
        max_dd_peak = close_prices[0]
        max_dd_trough = close_prices[0]

        for price in close_prices:
            if price > peak:
                peak = price
            drawdown = (peak - price) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_dd_peak = peak
                max_dd_trough = price

        # 年化波动率
        if daily_returns:
            mean_ret = sum(daily_returns) / len(daily_returns)
            variance = sum((r - mean_ret) ** 2 for r in daily_returns) / len(daily_returns)
            volatility = math.sqrt(variance) * math.sqrt(252)  # 年化
        else:
            volatility = 0

        # 年化收益率
        total_return = (close_prices[-1] - close_prices[0]) / close_prices[0]
        trading_days = n - 1
        if trading_days > 0:
            annualized_return = (1 + total_return) ** (252 / trading_days) - 1
        else:
            annualized_return = 0

        # 夏普比率
        if volatility > 0:
            sharpe = (annualized_return - risk_free_rate) / volatility
        else:
            sharpe = 0

        # 最大连续上涨/下跌天数
        max_up_streak = 0
        max_down_streak = 0
        current_up = 0
        current_down = 0

        for r in daily_returns:
            if r > 0:
                current_up += 1
                current_down = 0
                max_up_streak = max(max_up_streak, current_up)
            elif r < 0:
                current_down += 1
                current_up = 0
                max_down_streak = max(max_down_streak, current_down)
            else:
                current_up = 0
                current_down = 0

        return {
            "period_returns": period_returns,
            "total_return_pct": round(total_return * 100, 2),
            "max_drawdown_pct": round(max_drawdown * 100, 2),
            "annualized_volatility": round(volatility * 100, 2),
            "annualized_return_pct": round(annualized_return * 100, 2),
            "sharpe_ratio": round(sharpe, 3),
            "max_up_streak": max_up_streak,
            "max_down_streak": max_down_streak,
            "trading_days": trading_days,
            "risk_level": IndicatorService._assess_risk_level(max_drawdown, volatility),
        }

    @staticmethod
    def _assess_risk_level(max_drawdown: float, volatility: float) -> str:
        """综合评估风险等级"""
        dd_score = 0
        if max_drawdown > 0.5:
            dd_score = 3  # 高风险
        elif max_drawdown > 0.25:
            dd_score = 2  # 中高风险
        elif max_drawdown > 0.15:
            dd_score = 1  # 中风险
        else:
            dd_score = 0  # 低风险

        vol_score = 0
        if volatility > 0.5:
            vol_score = 3
        elif volatility > 0.35:
            vol_score = 2
        elif volatility > 0.2:
            vol_score = 1

        total = dd_score + vol_score
        if total >= 5:
            return "high"
        elif total >= 3:
            return "medium"
        else:
            return "low"

    # ──────────────────────────────────────────────
    # 综合入口：一次计算全部指标
    # ──────────────────────────────────────────────

    @staticmethod
    def calculate_all(records: List[Dict]) -> Dict[str, Any]:
        """
        综合计算全部技术指标

        Args:
            records: K线记录列表，每条包含：日期、开盘、收盘、最高、最低、成交量
                   注意：records 应按时间从旧到新排列
        Returns:
            完整的指标结果字典
        """
        if not records or len(records) < 30:
            return {"error": "数据不足，至少需要30条K线记录", "record_count": len(records)}

        # 提取数据序列（从旧到新）
        dates = [r.get('日期', '') for r in records]
        opens = [float(r.get('开盘', 0)) for r in records]
        closes = [float(r.get('收盘', 0)) for r in records]
        highs = [float(r.get('最高', 0)) for r in records]
        lows = [float(r.get('最低', 0)) for r in records]
        volumes = [float(r.get('成交量', 0)) for r in records]

        logger.info(f"[IndicatorService] 开始计算指标, 数据量={len(records)}, "
                     f"日期范围: {dates[0]} ~ {dates[-1]}")

        result = {
            "symbol": records[0].get('symbol', ''),
            "data_count": len(records),
            "date_range": {"start": dates[0], "end": dates[-1]},
            "latest_price": closes[-1],
            "indicators": {},
            "signals": {},
        }

        # === MA ===
        ma5 = IndicatorService.ma(closes, 5)
        ma10 = IndicatorService.ma(closes, 10)
        ma20 = IndicatorService.ma(closes, 20)
        ma60 = IndicatorService.ma(closes, 60)

        result["indicators"]["ma"] = {
            "ma5": ma5[-1],
            "ma10": ma10[-1],
            "ma20": ma20[-1],
            "ma60": ma60[-1],
            "series_5": [v if v is not None else 0 for v in ma5],
            "series_10": [v if v is not None else 0 for v in ma10],
            "series_20": [v if v is not None else 0 for v in ma20],
            "series_60": [v if v is not None else 0 for v in ma60],
        }

        # MA 信号
        ma_sig = IndicatorService.detect_ma_signal(ma5, ma20)
        result["signals"]["ma"] = ma_sig
        ma_sig_long = IndicatorService.detect_ma_signal(ma10, ma60)
        result["signals"]["ma_long_term"] = ma_sig_long

        # === MACD ===
        macd_data = IndicatorService.macd(closes)
        result["indicators"]["macd"] = {
            "dif": macd_data["dif"][-1],
            "dea": macd_data["dea"][-1],
            "histogram": macd_data["histogram"][-1],
            "series_dif": [v if v is not None else 0 for v in macd_data["dif"]],
            "series_dea": [v if v is not None else 0 for v in macd_data["dea"]],
            "series_hist": [v if v is not None else 0 for v in macd_data["histogram"]],
        }
        result["signals"]["macd"] = IndicatorService.detect_macd_signal(
            macd_data["dif"], macd_data["dea"], macd_data["histogram"]
        )

        # === RSI ===
        rsi_vals = IndicatorService.rsi(closes)
        result["indicators"]["rsi"] = {
            "value": rsi_vals[-1],
            "series": [v if v is not None else 50 for v in rsi_vals],
        }
        result["signals"]["rsi"] = IndicatorService.detect_rsi_signal(rsi_vals)

        # === KDJ ===
        kdj_data = IndicatorService.kdj(highs, lows, closes)
        result["indicators"]["kdj"] = {
            "k": kdj_data["k"][-1],
            "d": kdj_data["d"][-1],
            "j": kdj_data["j"][-1],
            "series_k": [v if v is not None else 50 for v in kdj_data["k"]],
            "series_d": [v if v is not None else 50 for v in kdj_data["d"]],
            "series_j": [v if v is not None else 50 for v in kdj_data["j"]],
        }
        result["signals"]["kdj"] = IndicatorService.detect_kdj_signal(
            kdj_data["k"], kdj_data["d"], kdj_data["j"]
        )

        # === BOLL ===
        boll_data = IndicatorService.boll(closes)
        result["indicators"]["boll"] = {
            "upper": boll_data["upper"][-1],
            "mid": boll_data["mid"][-1],
            "lower": boll_data["lower"][-1],
            "bandwidth": boll_data["bandwidth"][-1],
            "series_upper": [v if v is not None else 0 for v in boll_data["upper"]],
            "series_mid": [v if v is not None else 0 for v in boll_data["mid"]],
            "series_lower": [v if v is not None else 0 for v in boll_data["lower"]],
        }
        result["signals"]["boll"] = IndicatorService.detect_boll_signal(
            closes, boll_data["upper"], boll_data["lower"], boll_data["bandwidth"]
        )

        # === 风险指标 ===
        result["risk"] = IndicatorService.calculate_risk_metrics(closes, dates)

        logger.info(f"[IndicatorService] 指标计算完成, "
                     f"MA5={ma5[-1]} MACD_DIF={macd_data['dif'][-1]} "
                     f"RSI={rsi_vals[-1]} BOLL_UB={boll_data['upper'][-1]}")

        return result

    # ──────────────────────────────────────────────
    # 内部工具方法
    # ──────────────────────────────────────────────

    @staticmethod
    def _ema(data: List[float], period: int,
             start_val: Optional[float] = None) -> List[Optional[float]]:
        """
        指数移动平均线 EMA

        EMA(t) = price * multiplier + EMA(t-1) * (1 - multiplier)
        multiplier = 2 / (period + 1)
        """
        n = len(data)
        if n == 0:
            return []

        multiplier = 2 / (period + 1)
        result = []

        # 第一个EMA值用SMA初始化
        if n >= period:
            sma_start = sum(data[:period]) / period
            ema_val = start_val if start_val is not None else sma_start
        else:
            ema_val = data[0] if data else 0

        for i in range(n):
            if i < period - 1:
                result.append(None)
            elif i == period - 1:
                sma_init = sum(data[:period]) / period
                result.append(round(sma_init, 4))
                ema_val = sma_init
            else:
                ema_val = data[i] * multiplier + ema_val * (1 - multiplier)
                result.append(round(ema_val, 4))

        return result


# 单例实例
indicator_service = IndicatorService()
