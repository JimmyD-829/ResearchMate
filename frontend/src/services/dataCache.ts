import { emotionApi, monitorApi } from './api';

interface CacheItem<T> {
  data: T;
  timestamp: number;
  source: 'live' | 'cached' | 'fallback';
  expiresAt: number;
}

class DataCacheManager {
  private cache = new Map<string, CacheItem<any>>();
  private readonly DEFAULT_TTL = 30 * 60 * 1000; // 30分钟
  private readonly FALLBACK_TTL = 60 * 60 * 1000; // 1小时（fallback数据）
  private retryCount = 0;
  private maxRetries = 3;

  async fetchWithCache<T>(
    key: string,
    fetchFn: () => Promise<T>,
    fallbackFn?: () => T,
    ttl: number = this.DEFAULT_TTL
  ): Promise<{ data: T; source: 'live' | 'cached' | 'fallback'; isFresh: boolean }> {
    const now = Date.now();
    
    // 1. 检查缓存是否有效
    const cached = this.cache.get(key);
    if (cached && cached.expiresAt > now) {
      console.log(`[Cache] Hit: ${key}, age: ${Math.round((now - cached.timestamp) / 1000)}s`);
      return {
        data: cached.data,
        source: cached.source,
        isFresh: (now - cached.timestamp) < (ttl / 2) // 一半时间算新鲜
      };
    }

    // 2. 尝试获取实时数据
    try {
      this.retryCount = 0;
      const data = await this.withRetry(fetchFn);
      
      // 存储到缓存
      this.set(key, data, 'live', ttl);
      
      return {
        data,
        source: 'live',
        isFresh: true
      };
    } catch (error) {
      console.error(`[Cache] Fetch failed for ${key}:`, error);
      
      // 3. 使用过期但可用的缓存
      if (cached) {
        console.warn(`[Cache] Using stale cache for ${key}`);
        return {
          data: cached.data,
          source: 'cached',
          isFresh: false
        };
      }
      
      // 4. 使用fallback数据
      if (fallbackFn) {
        console.warn(`[Cache] Using fallback for ${key}`);
        const fallbackData = fallbackFn();
        this.set(key, fallbackData, 'fallback', this.FALLBACK_TTL);
        
        return {
          data: fallbackData,
          source: 'fallback',
          isFresh: false
        };
      }
      
      throw error;
    }
  }

  private async withRetry<T>(fn: () => Promise<T>): Promise<T> {
    for (let i = 0; i <= this.maxRetries; i++) {
      try {
        return await fn();
      } catch (error) {
        if (i === this.maxRetries) throw error;
        console.log(`[Retry] Attempt ${i + 1}/${this.maxRetries} failed, retrying in ${(i + 1) * 1000}ms...`);
        await new Promise(resolve => setTimeout(resolve, (i + 1) * 1000));
      }
    }
    throw new Error('Max retries exceeded');
  }

  private set<T>(key: string, data: T, source: 'live' | 'cached' | 'fallback', ttl: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      source,
      expiresAt: Date.now() + ttl
    });
  }

  getCacheInfo(key: string): { exists: boolean; age: number | null; source: string | null } {
    const cached = this.cache.get(key);
    if (!cached) return { exists: false, age: null, source: null };
    
    return {
      exists: true,
      age: Math.round((Date.now() - cached.timestamp) / 1000),
      source: cached.source
    };
  }

  clear(): void {
    this.cache.clear();
  }

  getAgeInSeconds(key: string): number | null {
    const cached = this.cache.get(key);
    return cached ? Math.round((Date.now() - cached.timestamp) / 1000) : null;
  }
}

export const dataCache = new DataCacheManager();

// 数据新鲜度工具函数
export function getDataFreshnessLabel(ageSeconds: number | null): { label: string; color: string; icon: string } {
  if (ageSeconds === null) return { label: '未知', color: 'gray', icon: '❓' };
  
  if (ageSeconds < 60) return { label: '刚刚更新', color: 'green', icon: '✅' };
  if (ageSeconds < 300) return { label: `${Math.floor(ageSeconds / 60)}分钟前`, color: 'green', icon: '🟢' };
  if (ageSeconds < 1800) return { label: `${Math.floor(ageSeconds / 60)}分钟前`, color: 'yellow', icon: '🟡' };
  if (ageSeconds < 3600) return { label: `${Math.floor(ageSeconds / 60)}分钟前`, color: 'orange', icon: '🟠' };
  return { label: `${Math.floor(ageSeconds / 3600)}小时前`, color: 'red', icon: '🔴' };
}

export function getSourceBadge(source: string): { text: string; className: string } {
  switch (source) {
    case 'live':
      return { text: '实时', className: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' };
    case 'cached':
      return { text: '缓存', className: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' };
    case 'fallback':
      return { text: '示例', className: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' };
    default:
      return { text: '未知', className: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-400' };
  }
}
