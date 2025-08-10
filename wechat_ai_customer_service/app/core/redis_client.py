"""
Redis客户端封装
"""
import aioredis
import json
from typing import Any, Optional
from app.core.config import settings
from app.utils.logger import logger

class RedisClient:
    """Redis客户端"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
    
    async def initialize(self):
        """初始化Redis连接"""
        try:
            self.redis = aioredis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            # 测试连接
            await self.redis.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            self.redis = None
    
    async def close(self):
        """关闭Redis连接"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis连接已关闭")
    
    async def set(self, key: str, value: Any, expire: int = None) -> bool:
        """设置缓存"""
        try:
            if not self.redis:
                return False
            
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            if expire:
                await self.redis.setex(key, expire, value)
            else:
                await self.redis.set(key, value)
            
            return True
        except Exception as e:
            logger.error(f"Redis设置失败: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            if not self.redis:
                return None
            
            value = await self.redis.get(key)
            if not value:
                return None
            
            # 尝试解析JSON
            try:
                return json.loads(value)
            except:
                return value
                
        except Exception as e:
            logger.error(f"Redis获取失败: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            if not self.redis:
                return False
            
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis删除失败: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查key是否存在"""
        try:
            if not self.redis:
                return False
            
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.error(f"Redis检查存在性失败: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """递增计数器"""
        try:
            if not self.redis:
                return None
            
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis递增失败: {e}")
            return None
    
    async def set_hash(self, key: str, field: str, value: Any) -> bool:
        """设置哈希字段"""
        try:
            if not self.redis:
                return False
            
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            await self.redis.hset(key, field, value)
            return True
        except Exception as e:
            logger.error(f"Redis哈希设置失败: {e}")
            return False
    
    async def get_hash(self, key: str, field: str) -> Optional[Any]:
        """获取哈希字段"""
        try:
            if not self.redis:
                return None
            
            value = await self.redis.hget(key, field)
            if not value:
                return None
            
            # 尝试解析JSON
            try:
                return json.loads(value)
            except:
                return value
                
        except Exception as e:
            logger.error(f"Redis哈希获取失败: {e}")
            return None

# 全局Redis客户端实例
redis_client = RedisClient()