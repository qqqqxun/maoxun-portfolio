"""
微信公众号AI客服系统主入口
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime
import asyncio
from typing import Optional

from app.core.config import settings
from app.core.wechat_handler import WeChatHandler
from app.core.message_processor import MessageProcessor
from app.core.redis_client import redis_client
from app.utils.logger import logger
from app.admin.knowledge_manager import router as knowledge_router
from app.middleware.rate_limiter import performance_optimizer

app = FastAPI(title="微信公众号AI客服系统", version="1.0.0")

# 添加管理后台路由
app.include_router(knowledge_router)

# 初始化处理器
wechat_handler = WeChatHandler()
message_processor = MessageProcessor()

@app.on_event("startup")
async def startup_event():
    """应用启动初始化"""
    logger.info("AI客服系统启动中...")
    await redis_client.initialize()
    logger.info("AI客服系统启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭清理"""
    logger.info("AI客服系统关闭中...")
    await redis_client.close()
    logger.info("AI客服系统已关闭")

@app.get("/")
async def root():
    """健康检查"""
    return {"status": "ok", "message": "微信公众号AI客服系统运行中"}

@app.get("/admin/stats")
async def get_system_stats():
    """获取系统统计信息"""
    try:
        stats = await performance_optimizer.get_performance_stats()
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取系统统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")

@app.get("/admin/health")
async def health_check():
    """详细健康检查"""
    try:
        health_status = {
            "status": "healthy",
            "services": {
                "redis": "unknown",
                "ai_service": "unknown"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # 检查Redis连接
        try:
            if redis_client.redis:
                await redis_client.redis.ping()
                health_status["services"]["redis"] = "healthy"
            else:
                health_status["services"]["redis"] = "disconnected"
        except:
            health_status["services"]["redis"] = "error"
        
        # 检查AI服务
        try:
            from app.services.ai_service import AIService
            ai_service = AIService()
            # 这里可以添加AI服务健康检查
            health_status["services"]["ai_service"] = "healthy"
        except:
            health_status["services"]["ai_service"] = "error"
        
        # 判断整体状态
        if any(status == "error" for status in health_status["services"].values()):
            health_status["status"] = "unhealthy"
        elif any(status == "unknown" for status in health_status["services"].values()):
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail="健康检查失败")

@app.post("/admin/cache/clear")
async def clear_cache(pattern: str = "*"):
    """清除缓存"""
    try:
        from app.middleware.rate_limiter import cache_manager
        await cache_manager.invalidate_pattern(pattern)
        return {"success": True, "message": f"缓存清除成功: {pattern}"}
    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        raise HTTPException(status_code=500, detail="清除缓存失败")

@app.post("/admin/cache/warmup")
async def warmup_cache():
    """预热缓存"""
    try:
        from app.middleware.rate_limiter import cache_manager
        await cache_manager.warm_up_cache()
        return {"success": True, "message": "缓存预热完成"}
    except Exception as e:
        logger.error(f"缓存预热失败: {e}")
        raise HTTPException(status_code=500, detail="缓存预热失败")

@app.get("/wechat")
async def wechat_verify(
    signature: str,
    timestamp: str,
    nonce: str,
    echostr: str
):
    """微信公众号接入验证"""
    if wechat_handler.verify_signature(signature, timestamp, nonce):
        logger.info("微信公众号验证成功")
        return PlainTextResponse(echostr)
    else:
        logger.warning("微信公众号验证失败")
        raise HTTPException(status_code=403, detail="验证失败")

@app.post("/wechat")
async def wechat_message(request: Request):
    """处理微信公众号消息"""
    try:
        # 获取原始数据
        body = await request.body()
        xml_data = body.decode('utf-8')
        
        # 解析XML消息
        message = wechat_handler.parse_message(xml_data)
        if not message:
            return PlainTextResponse("")
        
        logger.info(f"收到消息: {message}")
        
        # 异步处理消息
        asyncio.create_task(message_processor.process_message(message))
        
        # 立即返回空响应（微信要求5秒内响应）
        return PlainTextResponse("")
        
    except Exception as e:
        logger.error(f"处理微信消息时发生错误: {e}")
        return PlainTextResponse("")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )