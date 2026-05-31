#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能缓存管理器 - 解决Alpha Vantage API频率限制问题

功能：
1. 内存缓存（进程内）
2. 自动过期机制
3. 命中率统计
4. 线程安全
"""

import time
import threading
import logging
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SmartCache:
    """
    智能缓存管理器
    
    使用示例：
        cache = SmartCache(default_ttl=1800)  # 30分钟
        
        # 存储数据
        cache.set('BABA_quote', {'price': 124.22}, ttl=600)  # 10分钟
        
        # 获取数据
        data = cache.get('BABA_quote')
        if data:
            print(f"命中缓存: {data}")
        else:
            print("缓存未命中，需要重新获取")
    """
    
    def __init__(self, default_ttl: int = 1800):
        """
        初始化缓存
        
        Args:
            default_ttl: 默认过期时间（秒），默认30分钟
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl
        self._lock = threading.Lock()
        
        # 统计信息
        self._hits = 0
        self._misses = 0
        
        logger.info(f"📦 智能缓存系统初始化 (默认TTL: {default_ttl}秒)")
    
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """
        存储数据到缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None则使用默认值
        """
        with self._lock:
            expire_time = time.time() + (ttl or self._default_ttl)
            
            self._cache[key] = {
                'value': value,
                'expire_time': expire_time,
                'created_at': datetime.now().isoformat()
            }
            
            logger.debug(f"💾 缓存已存储: {key} (TTL: {ttl or self._default_ttl}秒)")
    
    def get(self, key: str) -> Optional[Any]:
        """
        从缓存获取数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的值，如果不存在或已过期返回None
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            item = self._cache[key]
            
            # 检查是否过期
            if time.time() > item['expire_time']:
                del self._cache[key]
                self._misses += 1
                logger.debug(f"⏰ 缓存已过期: {key}")
                return None
            
            # 缓存命中
            self._hits += 1
            logger.debug(f"✅ 缓存命中: {key}")
            return item['value']
    
    def delete(self, key: str) -> bool:
        """
        删除指定缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功删除
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"🗑️ 缓存已删除: {key}")
                return True
            return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"🧹 已清空 {count} 条缓存")
    
    def has(self, key: str) -> bool:
        """检查键是否存在且未过期"""
        return self.get(key) is not None
    
    def cleanup(self) -> int:
        """清理过期的缓存条目"""
        with self._lock:
            now = time.time()
            expired_keys = [
                key for key, item in self._cache.items()
                if now > item['expire_time']
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"🧹 清理了 {len(expired_keys)} 条过期缓存")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        
        return {
            'total_requests': total,
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': f"{hit_rate:.2f}%",
            'cached_items': len(self._cache),
            'default_ttl': self._default_ttl
        }
    
    def print_stats(self) -> None:
        """打印缓存统计信息"""
        stats = self.get_stats()
        
        print(f"\n{'='*60}")
        print(f"📊 缓存统计信息")
        print(f"{'='*60}")
        print(f"总请求数: {stats['total_requests']}")
        print(f"命中次数: {stats['hits']}")
        print(f"未命中: {stats['misses']}")
        print(f"命中率: {stats['hit_rate']}")
        print(f"当前缓存条目: {stats['cached_items']}")
        print(f"默认TTL: {stats['default_ttl']}秒")
        print(f"{'='*60}\n")


# 全局单例实例（供整个应用使用）
_global_cache: Optional[SmartCache] = None

def get_cache() -> SmartCache:
    """
    获取全局缓存实例
    
    Returns:
        SmartCache 全局单例
    """
    global _global_cache
    
    if _global_cache is None:
        _global_cache = SmartCache(
            default_ttl=30 * 60  # 30分钟默认缓存
        )
    
    return _global_cache


def cached(ttl: int = None):
    """
    缓存装饰器（用于函数级别缓存）
    
    使用方法：
        @cached(ttl=600)  # 缓存10分钟
        async def fetch_data(symbol):
            # 昂贵的API调用
            return await api.call(symbol)
    
    Args:
        ttl: 过期时间（秒）
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # 尝试从缓存获取
            cache = get_cache()
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                logger.info(f"✨ 函数缓存命中: {func.__name__}")
                return cached_result
            
            # 执行原函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            if result is not None:
                cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


if __name__ == '__main__':
    # 测试缓存系统
    print("测试智能缓存系统...")
    
    cache = SmartCache(default_ttl=10)  # 10秒用于测试
    
    # 测试基本操作
    cache.set('test_key', {'price': 124.22, 'symbol': 'BABA'})
    
    value = cache.get('test_key')
    assert value == {'price': 124.22, 'symbol': 'BABA'}
    print("✅ 基本存储和读取测试通过")
    
    # 测试未命中
    assert cache.get('nonexistent') is None
    print("✅ 未命中测试通过")
    
    # 测试删除
    cache.delete('test_key')
    assert cache.get('test_key') is None
    print("✅ 删除测试通过")
    
    # 测试统计
    stats = cache.get_stats()
    print(f"✅ 统计信息: {stats}")
    
    print("\n✅ 所有测试通过！")
