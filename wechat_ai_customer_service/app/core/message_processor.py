"""
消息处理器 - 核心业务逻辑
"""
import asyncio
import time
from typing import Dict, Optional
from app.core.config import settings
from app.core.redis_client import redis_client
from app.core.wechat_handler import WeChatHandler
from app.services.ai_service import AIService
from app.services.order_service import OrderService
from app.services.human_service import HumanService
from app.utils.logger import logger

class MessageProcessor:
    """消息处理器"""
    
    def __init__(self):
        self.wechat_handler = WeChatHandler()
        self.ai_service = AIService()
        self.order_service = OrderService()
        self.human_service = HumanService()
        
    async def process_message(self, message: Dict):
        """处理用户消息"""
        start_time = time.time()
        
        try:
            openid = message.get("FromUserName")
            content = message.get("Content", "").strip()
            msg_type = message.get("MsgType")
            
            if not openid or not content or msg_type != "text":
                return
            
            logger.info(f"处理用户消息: {openid} - {content}")
            
            # 检查是否需要人工转接
            if await self._check_human_transfer(content):
                await self.human_service.transfer_to_human(openid, content)
                return
            
            # 检查是否是订单查询
            order_info = await self._extract_order_query(content)
            if order_info:
                response = await self.order_service.query_order(order_info, openid)
                await self._send_response(openid, response, start_time)
                return
            
            # 智能问答处理
            response = await self._handle_intelligent_qa(openid, content)
            await self._send_response(openid, response, start_time)
            
        except Exception as e:
            logger.error(f"处理消息时发生错误: {e}")
            await self._send_response(
                openid, 
                "抱歉，系统暂时繁忙，请稍后再试或输入'人工'转接客服。", 
                start_time
            )
    
    async def _check_human_transfer(self, content: str) -> bool:
        """检查是否需要转接人工"""
        content_lower = content.lower()
        for keyword in settings.HUMAN_SERVICE_KEYWORDS:
            if keyword in content_lower:
                return True
        return False
    
    async def _extract_order_query(self, content: str) -> Optional[Dict]:
        """提取订单查询信息"""
        # 使用正则表达式或AI识别订单号
        import re
        
        # 简单的订单号识别（可根据实际业务调整）
        order_patterns = [
            r'订单号[：:]\s*([A-Z0-9]{10,20})',
            r'订单[：:]\s*([A-Z0-9]{10,20})',
            r'([A-Z0-9]{10,20})',
        ]
        
        for pattern in order_patterns:
            match = re.search(pattern, content)
            if match:
                return {
                    "order_number": match.group(1),
                    "query_type": "order_status"
                }
        
        # 检查是否包含订单相关关键词
        order_keywords = ["订单", "快递", "物流", "发货", "配送", "查询"]
        if any(keyword in content for keyword in order_keywords):
            return {
                "query_type": "order_help",
                "content": content
            }
        
        return None
    
    async def _handle_intelligent_qa(self, openid: str, content: str) -> str:
        """处理智能问答"""
        try:
            # 检查缓存
            cache_key = f"qa_cache:{hash(content)}"
            cached_response = await redis_client.get(cache_key)
            if cached_response:
                logger.info("使用缓存回复")
                return cached_response
            
            # 获取用户上下文
            context = await self._get_user_context(openid)
            
            # AI生成回复
            response = await self.ai_service.generate_response(content, context)
            
            # 缓存回复
            await redis_client.set(cache_key, response, settings.CACHE_EXPIRE_TIME)
            
            # 更新用户上下文
            await self._update_user_context(openid, content, response)
            
            return response
            
        except Exception as e:
            logger.error(f"智能问答处理失败: {e}")
            return "抱歉，我暂时无法理解您的问题，请您详细描述一下，或输入'人工'转接客服。"
    
    async def _get_user_context(self, openid: str) -> Dict:
        """获取用户对话上下文"""
        context_key = f"user_context:{openid}"
        context = await redis_client.get(context_key)
        return context if context else {"messages": []}
    
    async def _update_user_context(self, openid: str, user_msg: str, ai_response: str):
        """更新用户对话上下文"""
        context_key = f"user_context:{openid}"
        context = await self._get_user_context(openid)
        
        # 保持最近10轮对话
        messages = context.get("messages", [])
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": ai_response})
        
        if len(messages) > 20:  # 保持10轮对话
            messages = messages[-20:]
        
        context["messages"] = messages
        context["last_update"] = int(time.time())
        
        # 缓存1小时
        await redis_client.set(context_key, context, 3600)
    
    async def _send_response(self, openid: str, content: str, start_time: float):
        """发送响应给用户"""
        try:
            # 检查响应时间
            response_time = time.time() - start_time
            if response_time > settings.MAX_RESPONSE_TIME:
                logger.warning(f"响应时间超时: {response_time:.2f}s")
            
            # 限制消息长度
            if len(content) > settings.MAX_MESSAGE_LENGTH:
                content = content[:settings.MAX_MESSAGE_LENGTH-50] + "...\n\n内容较长，如需了解更多请输入'人工'转接客服。"
            
            success = await self.wechat_handler.send_text_message(openid, content)
            if success:
                logger.info(f"消息发送成功: {openid}, 响应时间: {response_time:.2f}s")
            else:
                logger.error(f"消息发送失败: {openid}")
                
        except Exception as e:
            logger.error(f"发送响应时发生错误: {e}")