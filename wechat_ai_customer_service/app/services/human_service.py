"""
人工客服转接服务
"""
import httpx
import asyncio
from datetime import datetime
from typing import Dict, List
from app.core.config import settings
from app.core.redis_client import redis_client
from app.core.wechat_handler import WeChatHandler
from app.utils.logger import logger

class HumanService:
    """人工客服转接服务"""
    
    def __init__(self):
        self.wechat_handler = WeChatHandler()
        self.pending_transfers = {}  # 待转接队列
        
    async def transfer_to_human(self, user_openid: str, user_message: str) -> bool:
        """转接人工客服"""
        try:
            # 检查用户是否已在转接队列中
            if await self._is_user_in_queue(user_openid):
                await self._send_queue_status(user_openid)
                return True
            
            # 添加到转接队列
            await self._add_to_transfer_queue(user_openid, user_message)
            
            # 发送转接确认消息
            await self._send_transfer_confirmation(user_openid)
            
            # 通知人工客服系统
            await self._notify_human_service(user_openid, user_message)
            
            # 记录转接日志
            await self._log_transfer_request(user_openid, user_message)
            
            return True
            
        except Exception as e:
            logger.error(f"人工转接失败: {e}")
            await self.wechat_handler.send_text_message(
                user_openid,
                "抱歉，人工客服转接暂时不可用，请稍后再试。"
            )
            return False
    
    async def _is_user_in_queue(self, user_openid: str) -> bool:
        """检查用户是否已在转接队列中"""
        queue_key = f"transfer_queue:{user_openid}"
        return await redis_client.exists(queue_key)
    
    async def _add_to_transfer_queue(self, user_openid: str, user_message: str):
        """添加用户到转接队列"""
        queue_key = f"transfer_queue:{user_openid}"
        transfer_info = {
            "openid": user_openid,
            "message": user_message,
            "timestamp": datetime.now().isoformat(),
            "status": "waiting",
            "priority": "normal"
        }
        
        # 缓存2小时
        await redis_client.set(queue_key, transfer_info, 7200)
        
        # 添加到全局队列计数
        await redis_client.increment("transfer_queue_count")
    
    async def _send_transfer_confirmation(self, user_openid: str):
        """发送转接确认消息"""
        queue_position = await self._get_queue_position(user_openid)
        
        message = f"""🙋‍♀️ 正在为您转接人工客服...

当前排队人数：{queue_position}人
预计等待时间：{queue_position * 2}分钟

请稍等片刻，客服人员会尽快为您服务。
在等待期间，您可以继续发送消息描述问题。

如需取消转接，请回复"取消"。"""
        
        await self.wechat_handler.send_text_message(user_openid, message)
    
    async def _send_queue_status(self, user_openid: str):
        """发送排队状态"""
        queue_position = await self._get_queue_position(user_openid)
        
        message = f"""⏳ 您已在人工客服队列中

当前排队位置：第{queue_position}位
预计等待时间：{queue_position * 2}分钟

请耐心等待，我们会尽快为您安排客服。
如需取消转接，请回复"取消"。"""
        
        await self.wechat_handler.send_text_message(user_openid, message)
    
    async def _get_queue_position(self, user_openid: str) -> int:
        """获取用户在队列中的位置"""
        # 简化实现，实际应该维护一个有序队列
        queue_count = await redis_client.get("transfer_queue_count") or 0
        return max(1, int(queue_count))
    
    async def _notify_human_service(self, user_openid: str, user_message: str):
        """通知人工客服系统"""
        try:
            if not settings.HUMAN_SERVICE_WEBHOOK:
                logger.warning("未配置人工客服Webhook")
                return
            
            # 获取用户信息
            user_info = await self._get_user_info(user_openid)
            
            notification_data = {
                "type": "transfer_request",
                "user_openid": user_openid,
                "user_info": user_info,
                "message": user_message,
                "timestamp": datetime.now().isoformat(),
                "priority": "normal"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.HUMAN_SERVICE_WEBHOOK,
                    json=notification_data,
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    logger.info(f"人工客服通知成功: {user_openid}")
                else:
                    logger.warning(f"人工客服通知失败: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"通知人工客服系统失败: {e}")
    
    async def _get_user_info(self, user_openid: str) -> Dict:
        """获取用户信息"""
        try:
            # 从微信API获取用户信息
            access_token = await self.wechat_handler.get_access_token()
            if not access_token:
                return {"openid": user_openid}
            
            url = f"https://api.weixin.qq.com/cgi-bin/user/info"
            params = {
                "access_token": access_token,
                "openid": user_openid,
                "lang": "zh_CN"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                user_data = response.json()
                
                if user_data.get("errcode") == 0 or "nickname" in user_data:
                    return {
                        "openid": user_openid,
                        "nickname": user_data.get("nickname", "未知用户"),
                        "headimgurl": user_data.get("headimgurl", ""),
                        "city": user_data.get("city", ""),
                        "province": user_data.get("province", "")
                    }
                else:
                    logger.warning(f"获取用户信息失败: {user_data}")
                    return {"openid": user_openid}
                    
        except Exception as e:
            logger.error(f"获取用户信息异常: {e}")
            return {"openid": user_openid}
    
    async def _log_transfer_request(self, user_openid: str, user_message: str):
        """记录转接请求日志"""
        try:
            log_key = "transfer_logs"
            log_entry = {
                "openid": user_openid,
                "message": user_message,
                "timestamp": datetime.now().isoformat(),
                "action": "transfer_request"
            }
            
            # 获取现有日志
            logs = await redis_client.get(log_key) or []
            logs.append(log_entry)
            
            # 只保留最近1000条日志
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            # 缓存24小时
            await redis_client.set(log_key, logs, 86400)
            
        except Exception as e:
            logger.error(f"记录转接日志失败: {e}")
    
    async def cancel_transfer(self, user_openid: str) -> bool:
        """取消人工转接"""
        try:
            queue_key = f"transfer_queue:{user_openid}"
            
            # 检查是否在队列中
            if not await redis_client.exists(queue_key):
                await self.wechat_handler.send_text_message(
                    user_openid,
                    "您当前没有转接请求。"
                )
                return True
            
            # 从队列中移除
            await redis_client.delete(queue_key)
            await redis_client.increment("transfer_queue_count", -1)
            
            # 发送取消确认
            await self.wechat_handler.send_text_message(
                user_openid,
                "✅ 已取消人工客服转接。\n\n如有其他问题，请继续咨询或重新输入'人工'转接。"
            )
            
            logger.info(f"用户取消转接: {user_openid}")
            return True
            
        except Exception as e:
            logger.error(f"取消转接失败: {e}")
            return False
    
    async def handle_human_service_message(self, user_openid: str, message: str):
        """处理转接期间的用户消息"""
        try:
            # 检查是否要取消转接
            if message.strip().lower() in ["取消", "cancel"]:
                await self.cancel_transfer(user_openid)
                return
            
            # 检查是否在转接队列中
            queue_key = f"transfer_queue:{user_openid}"
            transfer_info = await redis_client.get(queue_key)
            
            if transfer_info:
                # 更新转接信息，添加用户补充消息
                if "additional_messages" not in transfer_info:
                    transfer_info["additional_messages"] = []
                
                transfer_info["additional_messages"].append({
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                })
                
                await redis_client.set(queue_key, transfer_info, 7200)
                
                # 发送确认消息
                await self.wechat_handler.send_text_message(
                    user_openid,
                    "📝 已记录您的补充信息，客服会看到所有消息内容。"
                )
            
        except Exception as e:
            logger.error(f"处理转接期间消息失败: {e}")