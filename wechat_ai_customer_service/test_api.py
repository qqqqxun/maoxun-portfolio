#!/usr/bin/env python3
"""
API测试脚本
测试微信AI客服系统的主要功能
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_check(self):
        """测试健康检查"""
        print("🏥 测试健康检查...")
        try:
            async with self.session.get(f"{self.base_url}/") as resp:
                data = await resp.json()
                assert resp.status == 200
                assert data["status"] == "ok"
                print("✅ 健康检查通过")
                return True
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
            return False
    
    async def test_detailed_health(self):
        """测试详细健康检查"""
        print("🔍 测试详细健康检查...")
        try:
            async with self.session.get(f"{self.base_url}/admin/health") as resp:
                data = await resp.json()
                assert resp.status == 200
                print(f"   状态: {data.get('status')}")
                print(f"   服务: {data.get('services')}")
                print("✅ 详细健康检查通过")
                return True
        except Exception as e:
            print(f"❌ 详细健康检查失败: {e}")
            return False
    
    async def test_knowledge_management(self):
        """测试知识库管理"""
        print("📚 测试知识库管理...")
        
        # 测试数据
        test_knowledge = {
            "question": "测试问题",
            "answer": "这是一个测试答案",
            "keywords": ["测试", "问答"],
            "category": "test"
        }
        
        try:
            # 添加知识条目
            async with self.session.post(
                f"{self.base_url}/admin/knowledge/add",
                json=test_knowledge
            ) as resp:
                data = await resp.json()
                assert resp.status == 200
                assert data["success"] == True
                knowledge_id = data["data"]["id"]
                print(f"   ✅ 添加知识条目成功: {knowledge_id}")
            
            # 获取知识列表
            async with self.session.get(f"{self.base_url}/admin/knowledge/list") as resp:
                data = await resp.json()
                assert resp.status == 200
                assert data["success"] == True
                print(f"   ✅ 获取知识列表成功: {len(data['data'])} 条记录")
            
            # 搜索知识
            async with self.session.get(
                f"{self.base_url}/admin/knowledge/search?q=测试"
            ) as resp:
                data = await resp.json()
                assert resp.status == 200
                assert data["success"] == True
                print(f"   ✅ 搜索知识成功: {len(data['data'])} 条记录")
            
            # 删除知识条目
            async with self.session.delete(
                f"{self.base_url}/admin/knowledge/{knowledge_id}"
            ) as resp:
                data = await resp.json()
                assert resp.status == 200
                assert data["success"] == True
                print(f"   ✅ 删除知识条目成功")
            
            print("✅ 知识库管理测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 知识库管理测试失败: {e}")
            return False
    
    async def test_system_stats(self):
        """测试系统统计"""
        print("📊 测试系统统计...")
        try:
            async with self.session.get(f"{self.base_url}/admin/stats") as resp:
                data = await resp.json()
                assert resp.status == 200
                assert data["success"] == True
                print(f"   AI使用统计: {data['data'].get('ai_usage', {})}")
                print(f"   转接队列: {data['data'].get('transfer_queue', 0)}")
                print("✅ 系统统计测试通过")
                return True
        except Exception as e:
            print(f"❌ 系统统计测试失败: {e}")
            return False
    
    async def test_cache_operations(self):
        """测试缓存操作"""
        print("💾 测试缓存操作...")
        try:
            # 预热缓存
            async with self.session.post(f"{self.base_url}/admin/cache/warmup") as resp:
                data = await resp.json()
                assert resp.status == 200
                assert data["success"] == True
                print("   ✅ 缓存预热成功")
            
            # 清除缓存
            async with self.session.post(
                f"{self.base_url}/admin/cache/clear?pattern=test_*"
            ) as resp:
                data = await resp.json()
                assert resp.status == 200
                assert data["success"] == True
                print("   ✅ 缓存清除成功")
            
            print("✅ 缓存操作测试通过")
            return True
        except Exception as e:
            print(f"❌ 缓存操作测试失败: {e}")
            return False
    
    async def test_wechat_verification(self):
        """测试微信验证接口"""
        print("📱 测试微信验证接口...")
        try:
            # 模拟微信验证请求（这会失败，但能测试接口是否存在）
            params = {
                "signature": "test_signature",
                "timestamp": str(int(time.time())),
                "nonce": "test_nonce",
                "echostr": "test_echo"
            }
            async with self.session.get(f"{self.base_url}/wechat", params=params) as resp:
                # 期望返回403（验证失败）
                assert resp.status == 403
                print("   ✅ 微信验证接口响应正常（验证失败是预期的）")
            
            return True
        except Exception as e:
            print(f"❌ 微信验证接口测试失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始API测试...")
        print("=" * 50)
        
        tests = [
            ("基础健康检查", self.test_health_check),
            ("详细健康检查", self.test_detailed_health),
            ("知识库管理", self.test_knowledge_management),
            ("系统统计", self.test_system_stats),
            ("缓存操作", self.test_cache_operations),
            ("微信验证接口", self.test_wechat_verification),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print()
            result = await test_func()
            if result:
                passed += 1
        
        print()
        print("=" * 50)
        print(f"🎯 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有测试通过！系统运行正常")
        else:
            print("⚠️  部分测试失败，请检查系统状态")

async def main():
    """主函数"""
    async with APITester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())