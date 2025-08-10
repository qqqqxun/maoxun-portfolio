"""
AI服务 - 智能问答核心
"""
import openai
from typing import Dict, List
from app.core.config import settings
from app.core.redis_client import redis_client
from app.utils.logger import logger

class AIService:
    """AI智能问答服务"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        self.model = settings.AI_MODEL
        
        # 系统提示词
        self.system_prompt = """你是一个专业的客服助手，请遵循以下规则：

1. 保持友好、专业的语调
2. 回答要简洁明了，不超过200字
3. 如果不确定答案，建议用户转接人工客服
4. 对于订单、物流等具体业务问题，引导用户提供订单号或转接人工
5. 始终保持礼貌和耐心
6. 避免提供可能不准确的具体信息（如价格、库存等）

常见问题处理：
- 产品咨询：提供基本信息，详细问题建议转人工
- 售后问题：了解具体情况，复杂问题转人工
- 投诉建议：表示理解，记录问题，转接相关部门
- 技术支持：提供基础帮助，复杂问题转人工

记住：你的目标是快速、准确地帮助用户，提升客户体验。"""
    
    async def generate_response(self, user_message: str, context: Dict = None) -> str:
        """生成AI回复"""
        try:
            # 构建对话历史
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # 添加历史对话
            if context and "messages" in context:
                # 只保留最近6轮对话避免token过多
                recent_messages = context["messages"][-12:]
                messages.extend(recent_messages)
            
            # 添加当前用户消息
            messages.append({"role": "user", "content": user_message})
            
            # 调用AI接口
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=300,
                temperature=0.7,
                timeout=3.0  # 3秒超时确保响应速度
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # 记录AI使用情况
            await self._log_ai_usage(user_message, ai_response)
            
            return ai_response
            
        except openai.APITimeoutError:
            logger.error("AI接口超时")
            return "抱歉，系统响应较慢，请稍后再试或输入'人工'转接客服。"
        except openai.APIError as e:
            logger.error(f"AI接口错误: {e}")
            return "抱歉，系统暂时无法处理您的问题，请输入'人工'转接客服。"
        except Exception as e:
            logger.error(f"AI服务异常: {e}")
            return "抱歉，系统出现异常，请输入'人工'转接客服。"
    
    async def _log_ai_usage(self, user_message: str, ai_response: str):
        """记录AI使用情况用于优化"""
        try:
            usage_key = "ai_usage_stats"
            stats = await redis_client.get(usage_key) or {
                "total_requests": 0,
                "success_requests": 0,
                "avg_response_length": 0
            }
            
            stats["total_requests"] += 1
            stats["success_requests"] += 1
            
            # 计算平均回复长度
            current_avg = stats.get("avg_response_length", 0)
            new_avg = (current_avg * (stats["success_requests"] - 1) + len(ai_response)) / stats["success_requests"]
            stats["avg_response_length"] = round(new_avg, 2)
            
            await redis_client.set(usage_key, stats, 86400)  # 缓存24小时
            
        except Exception as e:
            logger.error(f"记录AI使用情况失败: {e}")
    
    async def get_knowledge_base_answer(self, question: str) -> str:
        """从知识库获取答案"""
        try:
            # 这里可以集成向量数据库进行语义搜索
            # 当前实现简单的关键词匹配
            
            knowledge_base = await self._load_knowledge_base()
            
            # 简单关键词匹配
            question_lower = question.lower()
            for item in knowledge_base:
                keywords = item.get("keywords", [])
                if any(keyword in question_lower for keyword in keywords):
                    return item.get("answer", "")
            
            return ""
            
        except Exception as e:
            logger.error(f"知识库查询失败: {e}")
            return ""
    
    async def _load_knowledge_base(self) -> List[Dict]:
        """加载知识库"""
        # 从Redis缓存或数据库加载知识库
        cache_key = "knowledge_base"
        knowledge_base = await redis_client.get(cache_key)
        
        if not knowledge_base:
            # 这里应该从数据库加载，当前使用示例数据
            knowledge_base = [
                {
                    "keywords": ["退货", "退款", "不满意"],
                    "answer": "关于退货退款：\n1. 商品7天内可无理由退货\n2. 请确保商品包装完整\n3. 退款会在3-5个工作日内到账\n如需处理请提供订单号或转接人工客服。"
                },
                {
                    "keywords": ["发货", "物流", "快递", "配送"],
                    "answer": "关于物流配送：\n1. 订单将在24小时内发货\n2. 可通过订单号查询物流信息\n3. 一般3-5天可送达\n如需查询具体物流请提供订单号。"
                },
                {
                    "keywords": ["价格", "优惠", "折扣", "活动"],
                    "answer": "关于价格优惠：\n1. 价格以商品页面显示为准\n2. 关注公众号获取最新优惠信息\n3. 定期有促销活动\n具体优惠信息请咨询人工客服。"
                }
            ]
            
            # 缓存2小时
            await redis_client.set(cache_key, knowledge_base, 7200)
        
        return knowledge_base