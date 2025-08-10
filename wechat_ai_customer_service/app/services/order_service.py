"""
订单服务 - 订单查询功能
"""
import httpx
from typing import Dict, Optional
from app.core.config import settings
from app.core.redis_client import redis_client
from app.utils.logger import logger

class OrderService:
    """订单查询服务"""
    
    def __init__(self):
        # 模拟订单数据（实际应该连接真实的订单系统）
        self.mock_orders = {
            "ORD2024080501": {
                "order_number": "ORD2024080501",
                "status": "已发货",
                "items": ["iPhone 15 Pro", "手机壳"],
                "total_amount": 8999.00,
                "tracking_number": "SF1234567890",
                "estimated_delivery": "2024-08-07"
            },
            "ORD2024080502": {
                "order_number": "ORD2024080502", 
                "status": "已完成",
                "items": ["MacBook Air M3"],
                "total_amount": 12999.00,
                "tracking_number": None,
                "estimated_delivery": "已送达"
            }
        }
    
    async def query_order(self, order_info: Dict, user_openid: str) -> str:
        """查询订单信息"""
        try:
            if order_info.get("query_type") == "order_status":
                return await self._query_order_by_number(order_info["order_number"], user_openid)
            elif order_info.get("query_type") == "order_help":
                return await self._handle_order_help(order_info["content"])
            else:
                return "请提供订单号进行查询，格式如：ORD2024080501"
                
        except Exception as e:
            logger.error(f"订单查询失败: {e}")
            return "抱歉，订单查询服务暂时不可用，请稍后再试或转接人工客服。"
    
    async def _query_order_by_number(self, order_number: str, user_openid: str) -> str:
        """根据订单号查询订单"""
        try:
            # 检查缓存
            cache_key = f"order_info:{order_number}"
            cached_order = await redis_client.get(cache_key)
            
            if not cached_order:
                # 从订单系统获取数据（这里使用模拟数据）
                order_data = await self._fetch_order_from_system(order_number)
                if order_data:
                    # 缓存10分钟
                    await redis_client.set(cache_key, order_data, 600)
                    cached_order = order_data
            
            if not cached_order:
                return f"未找到订单号为 {order_number} 的订单信息。\n\n请检查订单号是否正确，或转接人工客服查询。"
            
            # 格式化订单信息
            return self._format_order_info(cached_order)
            
        except Exception as e:
            logger.error(f"订单号查询失败: {e}")
            return "抱歉，订单查询失败，请稍后再试或转接人工客服。"
    
    async def _fetch_order_from_system(self, order_number: str) -> Optional[Dict]:
        """从订单系统获取订单数据"""
        try:
            # 实际项目中应该调用真实的订单API
            # 这里使用模拟数据
            return self.mock_orders.get(order_number)
            
            # 真实API调用示例：
            # async with httpx.AsyncClient() as client:
            #     response = await client.get(
            #         f"{ORDER_API_URL}/orders/{order_number}",
            #         headers={"Authorization": f"Bearer {API_TOKEN}"},
            #         timeout=3.0
            #     )
            #     if response.status_code == 200:
            #         return response.json()
            #     return None
            
        except Exception as e:
            logger.error(f"获取订单数据失败: {e}")
            return None
    
    def _format_order_info(self, order_data: Dict) -> str:
        """格式化订单信息"""
        try:
            order_number = order_data.get("order_number")
            status = order_data.get("status")
            items = order_data.get("items", [])
            total_amount = order_data.get("total_amount")
            tracking_number = order_data.get("tracking_number")
            estimated_delivery = order_data.get("estimated_delivery")
            
            info_parts = [
                f"📦 订单信息",
                f"订单号：{order_number}",
                f"状态：{status}",
                f"商品：{', '.join(items)}",
                f"金额：¥{total_amount:.2f}"
            ]
            
            if tracking_number:
                info_parts.append(f"快递单号：{tracking_number}")
            
            if estimated_delivery:
                if status == "已发货":
                    info_parts.append(f"预计送达：{estimated_delivery}")
                elif status == "已完成":
                    info_parts.append(f"送达时间：{estimated_delivery}")
            
            info_parts.append("\n如需更多帮助请转接人工客服。")
            
            return "\n".join(info_parts)
            
        except Exception as e:
            logger.error(f"格式化订单信息失败: {e}")
            return "订单信息格式化失败，请转接人工客服查询。"
    
    async def _handle_order_help(self, content: str) -> str:
        """处理订单相关咨询"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["快递", "物流", "发货"]):
            return """📮 物流配送说明：

1. 订单确认后24小时内发货
2. 支持顺丰、圆通、申通等快递
3. 一般3-5个工作日送达
4. 可通过快递单号查询物流进度

请提供订单号查询具体物流信息，或转接人工客服。"""
        
        elif any(word in content_lower for word in ["退货", "退款", "换货"]):
            return """🔄 退换货说明：

1. 商品7天内支持无理由退货
2. 商品需保持原包装完整
3. 退款3-5个工作日内到账
4. 换货需重新下单

如需办理退换货请提供订单号，或转接人工客服处理。"""
        
        elif any(word in content_lower for word in ["发票", "开票"]):
            return """🧾 发票相关：

1. 支持电子发票和纸质发票
2. 下单时请选择发票类型
3. 电子发票将发送到邮箱
4. 纸质发票随货发送

如需补开发票请提供订单号，或转接人工客服。"""
        
        else:
            return """📋 订单相关服务：

• 订单查询：请提供订单号
• 物流查询：请提供快递单号  
• 退换货：请说明具体问题
• 发票问题：请提供订单信息

您也可以直接转接人工客服获得更详细的帮助。"""