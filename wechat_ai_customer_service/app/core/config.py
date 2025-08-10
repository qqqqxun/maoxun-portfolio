"""
系统配置文件
"""
import os
from typing import Optional

class Settings:
    # 微信公众号配置
    WECHAT_TOKEN: str = os.getenv("WECHAT_TOKEN", "your_wechat_token")
    WECHAT_APP_ID: str = os.getenv("WECHAT_APP_ID", "your_app_id")
    WECHAT_APP_SECRET: str = os.getenv("WECHAT_APP_SECRET", "your_app_secret")
    
    # AI配置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "your_openai_api_key")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-3.5-turbo")
    
    # Redis配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ai_customer_service.db")
    
    # 系统配置
    MAX_RESPONSE_TIME: int = int(os.getenv("MAX_RESPONSE_TIME", "1"))  # 最大响应时间（秒）
    CACHE_EXPIRE_TIME: int = int(os.getenv("CACHE_EXPIRE_TIME", "3600"))  # 缓存过期时间（秒）
    MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "2000"))
    
    # 人工转接配置
    HUMAN_SERVICE_WEBHOOK: str = os.getenv("HUMAN_SERVICE_WEBHOOK", "")
    HUMAN_SERVICE_KEYWORDS: list = ["人工", "客服", "转人工", "真人", "工作人员"]
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/ai_customer_service.log")

settings = Settings()