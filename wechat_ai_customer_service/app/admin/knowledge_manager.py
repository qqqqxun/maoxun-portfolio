"""
知识库管理系统
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
from datetime import datetime

from app.core.redis_client import redis_client
from app.utils.logger import logger

router = APIRouter(prefix="/admin/knowledge", tags=["知识库管理"])

class KnowledgeItem(BaseModel):
    """知识库条目"""
    id: Optional[str] = None
    question: str
    answer: str
    keywords: List[str]
    category: str = "general"
    enabled: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class KnowledgeResponse(BaseModel):
    """知识库响应"""
    success: bool
    message: str
    data: Optional[Dict] = None

class KnowledgeManager:
    """知识库管理器"""
    
    def __init__(self):
        self.knowledge_key = "knowledge_base"
        self.categories_key = "knowledge_categories"
    
    async def add_knowledge(self, item: KnowledgeItem) -> KnowledgeResponse:
        """添加知识条目"""
        try:
            # 生成ID和时间戳
            item.id = str(uuid.uuid4())
            item.created_at = datetime.now().isoformat()
            item.updated_at = item.created_at
            
            # 获取现有知识库
            knowledge_base = await redis_client.get(self.knowledge_key) or []
            
            # 添加新条目
            knowledge_base.append(item.dict())
            
            # 保存到Redis
            await redis_client.set(self.knowledge_key, knowledge_base)
            
            # 更新分类
            await self._update_categories(item.category)
            
            logger.info(f"添加知识条目: {item.question}")
            
            return KnowledgeResponse(
                success=True,
                message="知识条目添加成功",
                data=item.dict()
            )
            
        except Exception as e:
            logger.error(f"添加知识条目失败: {e}")
            return KnowledgeResponse(
                success=False,
                message=f"添加失败: {str(e)}"
            )
    
    async def get_knowledge_list(self, category: str = None, enabled: bool = None) -> List[Dict]:
        """获取知识库列表"""
        try:
            knowledge_base = await redis_client.get(self.knowledge_key) or []
            
            # 过滤条件
            filtered_items = []
            for item in knowledge_base:
                if category and item.get("category") != category:
                    continue
                if enabled is not None and item.get("enabled") != enabled:
                    continue
                filtered_items.append(item)
            
            return filtered_items
            
        except Exception as e:
            logger.error(f"获取知识库列表失败: {e}")
            return []
    
    async def update_knowledge(self, item_id: str, updates: Dict) -> KnowledgeResponse:
        """更新知识条目"""
        try:
            knowledge_base = await redis_client.get(self.knowledge_key) or []
            
            # 查找并更新条目
            updated = False
            for item in knowledge_base:
                if item.get("id") == item_id:
                    item.update(updates)
                    item["updated_at"] = datetime.now().isoformat()
                    updated = True
                    break
            
            if not updated:
                return KnowledgeResponse(
                    success=False,
                    message="未找到指定的知识条目"
                )
            
            # 保存更新
            await redis_client.set(self.knowledge_key, knowledge_base)
            
            logger.info(f"更新知识条目: {item_id}")
            
            return KnowledgeResponse(
                success=True,
                message="知识条目更新成功"
            )
            
        except Exception as e:
            logger.error(f"更新知识条目失败: {e}")
            return KnowledgeResponse(
                success=False,
                message=f"更新失败: {str(e)}"
            )
    
    async def delete_knowledge(self, item_id: str) -> KnowledgeResponse:
        """删除知识条目"""
        try:
            knowledge_base = await redis_client.get(self.knowledge_key) or []
            
            # 查找并删除条目
            original_length = len(knowledge_base)
            knowledge_base = [item for item in knowledge_base if item.get("id") != item_id]
            
            if len(knowledge_base) == original_length:
                return KnowledgeResponse(
                    success=False,
                    message="未找到指定的知识条目"
                )
            
            # 保存更新
            await redis_client.set(self.knowledge_key, knowledge_base)
            
            logger.info(f"删除知识条目: {item_id}")
            
            return KnowledgeResponse(
                success=True,
                message="知识条目删除成功"
            )
            
        except Exception as e:
            logger.error(f"删除知识条目失败: {e}")
            return KnowledgeResponse(
                success=False,
                message=f"删除失败: {str(e)}"
            )
    
    async def search_knowledge(self, query: str) -> List[Dict]:
        """搜索知识库"""
        try:
            knowledge_base = await redis_client.get(self.knowledge_key) or []
            query_lower = query.lower()
            
            results = []
            for item in knowledge_base:
                if not item.get("enabled", True):
                    continue
                
                # 搜索问题、答案和关键词
                question = item.get("question", "").lower()
                answer = item.get("answer", "").lower()
                keywords = [kw.lower() for kw in item.get("keywords", [])]
                
                if (query_lower in question or 
                    query_lower in answer or 
                    any(query_lower in kw for kw in keywords)):
                    results.append(item)
            
            return results
            
        except Exception as e:
            logger.error(f"搜索知识库失败: {e}")
            return []
    
    async def get_categories(self) -> List[str]:
        """获取知识库分类"""
        try:
            categories = await redis_client.get(self.categories_key) or ["general"]
            return categories
        except Exception as e:
            logger.error(f"获取知识库分类失败: {e}")
            return ["general"]
    
    async def _update_categories(self, category: str):
        """更新分类列表"""
        try:
            categories = await self.get_categories()
            if category not in categories:
                categories.append(category)
                await redis_client.set(self.categories_key, categories)
        except Exception as e:
            logger.error(f"更新分类失败: {e}")
    
    async def import_knowledge_bulk(self, items: List[Dict]) -> KnowledgeResponse:
        """批量导入知识"""
        try:
            success_count = 0
            errors = []
            
            for item_data in items:
                try:
                    item = KnowledgeItem(**item_data)
                    result = await self.add_knowledge(item)
                    if result.success:
                        success_count += 1
                    else:
                        errors.append(f"导入失败: {item.question} - {result.message}")
                except Exception as e:
                    errors.append(f"数据格式错误: {str(e)}")
            
            message = f"成功导入 {success_count} 条记录"
            if errors:
                message += f"，{len(errors)} 条失败"
            
            return KnowledgeResponse(
                success=True,
                message=message,
                data={"success_count": success_count, "errors": errors}
            )
            
        except Exception as e:
            logger.error(f"批量导入知识失败: {e}")
            return KnowledgeResponse(
                success=False,
                message=f"批量导入失败: {str(e)}"
            )

# 全局知识库管理器实例
knowledge_manager = KnowledgeManager()

# API路由
@router.post("/add", response_model=KnowledgeResponse)
async def add_knowledge_item(item: KnowledgeItem):
    """添加知识条目"""
    return await knowledge_manager.add_knowledge(item)

@router.get("/list")
async def get_knowledge_list(category: str = None, enabled: bool = None):
    """获取知识库列表"""
    items = await knowledge_manager.get_knowledge_list(category, enabled)
    return {"success": True, "data": items}

@router.put("/{item_id}", response_model=KnowledgeResponse)
async def update_knowledge_item(item_id: str, updates: Dict):
    """更新知识条目"""
    return await knowledge_manager.update_knowledge(item_id, updates)

@router.delete("/{item_id}", response_model=KnowledgeResponse)
async def delete_knowledge_item(item_id: str):
    """删除知识条目"""
    return await knowledge_manager.delete_knowledge(item_id)

@router.get("/search")
async def search_knowledge(q: str):
    """搜索知识库"""
    results = await knowledge_manager.search_knowledge(q)
    return {"success": True, "data": results}

@router.get("/categories")
async def get_categories():
    """获取分类列表"""
    categories = await knowledge_manager.get_categories()
    return {"success": True, "data": categories}

@router.post("/import", response_model=KnowledgeResponse)
async def import_knowledge_bulk(items: List[Dict]):
    """批量导入知识"""
    return await knowledge_manager.import_knowledge_bulk(items)