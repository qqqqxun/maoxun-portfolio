"""
限流中间件 - 防止滥用和提升性能
"""
import time
from typing import Dict, Optional
from fastapi import Request, HTTPException
from app.core.redis_client import redis_client
from app.utils.logger import logger

class RateLimiter:
    """限流器"""
    
    def __init__(self):
        self.default_limit = 60  # 每分钟60次请求
        self.default_window = 60  # 60秒窗口
        
    async def check_rate_limit(
        self, 
        key: str, 
        limit: int = None, 
        window: int = None
    ) -> Dict[str, any]:
        """检查限流状态"""
        limit = limit or self.default_limit
        window = window or self.default_window
        
        try:
            current_time = int(time.time())
            window_start = current_time - window
            
            # 使用Redis的有序集合实现滑动窗口限流
            pipe = redis_client.redis.pipeline()
            
            # 清理过期记录
            pipe.zremrangebyscore(f"rate_limit:{key}", 0, window_start)
            
            # 添加当前请求
            pipe.zadd(f"rate_limit:{key}", {str(current_time): current_time})
            
            # 获取当前窗口内的请求数
            pipe.zcard(f"rate_limit:{key}")
            
            # 设置过期时间
            pipe.expire(f"rate_limit:{key}", window)
            
            results = await pipe.execute()
            current_requests = results[2]
            
            if current_requests > limit:
                return {
                    "allowed": False,
                    "current": current_requests,
                    "limit": limit,
                    "window": window,
                    "reset_time": current_time + window
                }
            
            return {
                "allowed": True,
                "current": current_requests,
                "limit": limit,
                "window": window,
                "remaining": limit - current_requests
            }
            
        except Exception as e:
            logger.error(f"限流检查失败: {e}")
            # 限流失败时允许请求通过
            return {"allowed": True, "error": str(e)}
    
    async def user_rate_limit(self, openid: str) -> bool:
        """用户限流检查"""
        result = await self.check_rate_limit(
            f"user:{openid}",
            limit=30,  # 每分钟30次
            window=60
        )
        return result.get("allowed", True)
    
    async def ip_rate_limit(self, ip: str) -> bool:
        """IP限流检查"""
        result = await self.check_rate_limit(
            f"ip:{ip}",
            limit=100,  # 每分钟100次
            window=60
        )
        return result.get("allowed", True)
    
    async def api_rate_limit(self, api_path: str) -> bool:
        """API限流检查"""
        result = await self.check_rate_limit(
            f"api:{api_path}",
            limit=1000,  # 每分钟1000次
            window=60
        )
        return result.get("allowed", True)

class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.default_expire = 3600  # 1小时
    
    async def get_or_set(
        self, 
        key: str, 
        generator_func, 
        expire: int = None
    ):
        """获取缓存或设置新值"""
        try:
            # 尝试从缓存获取
            cached_value = await redis_client.get(key)
            if cached_value is not None:
                return cached_value
            
            # 生成新值
            new_value = await generator_func() if callable(generator_func) else generator_func
            
            # 设置缓存
            expire_time = expire or self.default_expire
            await redis_client.set(key, new_value, expire_time)
            
            return new_value
            
        except Exception as e:
            logger.error(f"缓存操作失败: {e}")
            # 缓存失败时直接返回生成的值
            return await generator_func() if callable(generator_func) else generator_func
    
    async def invalidate_pattern(self, pattern: str):
        """批量删除缓存"""
        try:
            if not redis_client.redis:
                return
            
            keys = await redis_client.redis.keys(pattern)
            if keys:
                await redis_client.redis.delete(*keys)
                logger.info(f"清除缓存: {len(keys)} 个key")
                
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
    
    async def warm_up_cache(self):
        """预热缓存"""
        try:
            # 预热知识库缓存
            from app.services.ai_service import AIService
            ai_service = AIService()
            await ai_service._load_knowledge_base()
            
            logger.info("缓存预热完成")
            
        except Exception as e:
            logger.error(f"缓存预热失败: {e}")

class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.cache_manager = CacheManager()
    
    async def optimize_message_processing(self, openid: str, content: str):
        """优化消息处理性能"""
        try:
            # 检查用户限流
            if not await self.rate_limiter.user_rate_limit(openid):
                logger.warning(f"用户限流触发: {openid}")
                return None, "请求过于频繁，请稍后再试"
            
            # 检查重复消息
            duplicate_key = f"duplicate_check:{openid}:{hash(content)}"
            if await redis_client.exists(duplicate_key):
                logger.info(f"检测到重复消息: {openid}")
                return None, "请不要重复发送相同消息"
            
            # 设置重复消息检查（5秒内）
            await redis_client.set(duplicate_key, "1", 5)
            
            return True, None
            
        except Exception as e:
            logger.error(f"性能优化处理失败: {e}")
            return True, None  # 失败时允许继续处理
    
    async def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        try:
            stats = {}
            
            # AI使用统计
            ai_stats = await redis_client.get("ai_usage_stats") or {}
            stats["ai_usage"] = ai_stats
            
            # 转接统计
            transfer_count = await redis_client.get("transfer_queue_count") or 0
            stats["transfer_queue"] = transfer_count
            
            # Redis连接状态
            if redis_client.redis:
                redis_info = await redis_client.redis.info()
                stats["redis"] = {
                    "connected_clients": redis_info.get("connected_clients", 0),
                    "used_memory_human": redis_info.get("used_memory_human", "0B"),
                    "keyspace_hits": redis_info.get("keyspace_hits", 0),
                    "keyspace_misses": redis_info.get("keyspace_misses", 0)
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取性能统计失败: {e}")
            return {}

# 全局实例
rate_limiter = RateLimiter()
cache_manager = CacheManager()
performance_optimizer = PerformanceOptimizer()