"""
微信公众号消息处理
"""
import hashlib
import xml.etree.ElementTree as ET
from typing import Dict, Optional
import time
import httpx
from app.core.config import settings
from app.utils.logger import logger

class WeChatHandler:
    """微信公众号消息处理器"""
    
    def __init__(self):
        self.token = settings.WECHAT_TOKEN
        self.app_id = settings.WECHAT_APP_ID
        self.app_secret = settings.WECHAT_APP_SECRET
        self.access_token = None
        self.access_token_expires = 0
    
    def verify_signature(self, signature: str, timestamp: str, nonce: str) -> bool:
        """验证微信服务器签名"""
        try:
            # 将token、timestamp、nonce三个参数进行字典序排序
            tmp_arr = [self.token, timestamp, nonce]
            tmp_arr.sort()
            tmp_str = ''.join(tmp_arr)
            
            # sha1加密
            sha1 = hashlib.sha1()
            sha1.update(tmp_str.encode('utf-8'))
            hashcode = sha1.hexdigest()
            
            return hashcode == signature
        except Exception as e:
            logger.error(f"验证微信签名失败: {e}")
            return False
    
    def parse_message(self, xml_data: str) -> Optional[Dict]:
        """解析微信XML消息"""
        try:
            root = ET.fromstring(xml_data)
            message = {}
            
            for child in root:
                message[child.tag] = child.text
            
            return message
        except Exception as e:
            logger.error(f"解析微信消息失败: {e}")
            return None
    
    async def get_access_token(self) -> Optional[str]:
        """获取微信access_token"""
        try:
            # 检查token是否过期
            current_time = int(time.time())
            if self.access_token and current_time < self.access_token_expires:
                return self.access_token
            
            # 获取新的access_token
            url = f"https://api.weixin.qq.com/cgi-bin/token"
            params = {
                "grant_type": "client_credential",
                "appid": self.app_id,
                "secret": self.app_secret
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                data = response.json()
                
                if "access_token" in data:
                    self.access_token = data["access_token"]
                    # 提前5分钟过期
                    self.access_token_expires = current_time + data.get("expires_in", 7200) - 300
                    logger.info("获取微信access_token成功")
                    return self.access_token
                else:
                    logger.error(f"获取微信access_token失败: {data}")
                    return None
                    
        except Exception as e:
            logger.error(f"获取微信access_token异常: {e}")
            return None
    
    async def send_text_message(self, openid: str, content: str) -> bool:
        """发送文本消息给用户"""
        try:
            access_token = await self.get_access_token()
            if not access_token:
                return False
            
            url = f"https://api.weixin.qq.com/cgi-bin/message/custom/send"
            params = {"access_token": access_token}
            
            data = {
                "touser": openid,
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, params=params, json=data)
                result = response.json()
                
                if result.get("errcode") == 0:
                    logger.info(f"发送消息成功: {openid}")
                    return True
                else:
                    logger.error(f"发送消息失败: {result}")
                    return False
                    
        except Exception as e:
            logger.error(f"发送微信消息异常: {e}")
            return False
    
    def create_xml_response(self, to_user: str, from_user: str, content: str) -> str:
        """创建XML响应消息"""
        template = """
        <xml>
        <ToUserName><![CDATA[{to_user}]]></ToUserName>
        <FromUserName><![CDATA[{from_user}]]></FromUserName>
        <CreateTime>{timestamp}</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[{content}]]></Content>
        </xml>
        """
        
        return template.format(
            to_user=to_user,
            from_user=from_user,
            timestamp=int(time.time()),
            content=content
        ).strip()