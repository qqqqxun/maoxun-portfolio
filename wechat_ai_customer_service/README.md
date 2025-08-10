# 微信公众号AI客服系统

一个基于Python + FastAPI的智能客服系统，支持微信公众号接入，具备智能问答、订单查询、人工转接等功能。

## 功能特性

### 🤖 核心功能
- **智能问答**: 基于GPT/通义千问的AI对话
- **订单查询**: 支持订单号查询和物流追踪  
- **人工转接**: 智能识别转接需求，排队管理
- **知识库**: 可视化知识库管理，支持批量导入

### ⚡ 性能优化
- **响应速度**: < 1秒响应时间保证
- **缓存机制**: Redis多层缓存优化
- **限流保护**: 防刷机制和频率控制
- **异步处理**: 高并发消息处理

### 🔧 技术特性
- **微信接入**: 完整的微信公众号消息处理
- **Docker化**: 容器化部署，易于扩展
- **监控告警**: Prometheus + Grafana监控
- **日志管理**: 结构化日志记录

## 快速开始

### 环境要求
- Python 3.8+
- Redis 6.0+
- Docker (推荐)

### 方式一：一键部署（推荐）
```bash
# Linux/Mac
./deploy.sh

# Windows
deploy.bat
```

### 方式二：手动部署

#### 1. 克隆项目
```bash
git clone <your-repo-url>
cd wechat_ai_customer_service
```

#### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，填入必要的配置信息
```

#### 3. Docker部署（推荐）
```bash
# 开发环境
docker-compose up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d
```

#### 4. 本地开发部署
```bash
# 安装依赖
pip install -r requirements.txt

# 启动Redis
redis-server

# 启动应用
# Linux/Mac
./start.sh
# Windows  
start.bat
```

## 配置说明

### 微信公众号配置
1. 在微信公众平台设置服务器配置
2. URL: `https://your-domain.com/wechat`  
3. Token: 设置在环境变量`WECHAT_TOKEN`中
4. 消息加解密方式: 明文模式

### AI服务配置
支持多种AI服务：

**OpenAI GPT**
```env
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-3.5-turbo
```

**阿里云通义千问**
```env
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_MODEL=qwen-turbo
```

## API文档

### 主要接口

#### 微信消息接口
- `GET /wechat` - 微信验证
- `POST /wechat` - 接收微信消息

#### 知识库管理
- `POST /admin/knowledge/add` - 添加知识条目
- `GET /admin/knowledge/list` - 获取知识列表
- `PUT /admin/knowledge/{id}` - 更新知识条目
- `DELETE /admin/knowledge/{id}` - 删除知识条目
- `GET /admin/knowledge/search` - 搜索知识库
- `GET /admin/knowledge/categories` - 获取分类列表
- `POST /admin/knowledge/import` - 批量导入知识

#### 系统监控
- `GET /` - 健康检查
- `GET /admin/health` - 详细健康检查
- `GET /admin/stats` - 系统统计信息
- `POST /admin/cache/clear` - 清除缓存
- `POST /admin/cache/warmup` - 预热缓存

### 完整API文档
启动后访问: `http://localhost:8000/docs`

## 项目结构

```
wechat_ai_customer_service/
│
├── app/
│   ├── main.py                 # 应用入口
│   ├── core/                   # 核心模块
│   │   ├── config.py          # 配置管理
│   │   ├── wechat_handler.py  # 微信消息处理
│   │   ├── message_processor.py # 消息路由处理
│   │   └── redis_client.py    # Redis客户端
│   │
│   ├── services/              # 业务服务
│   │   ├── ai_service.py      # AI问答服务
│   │   ├── order_service.py   # 订单查询服务
│   │   └── human_service.py   # 人工转接服务
│   │
│   ├── admin/                 # 管理功能
│   │   └── knowledge_manager.py # 知识库管理
│   │
│   ├── middleware/            # 中间件
│   │   └── rate_limiter.py    # 限流和缓存
│   │
│   └── utils/                 # 工具模块
│       └── logger.py          # 日志配置
│
├── docker-compose.yml         # Docker编排
├── Dockerfile                 # Docker镜像
├── requirements.txt           # Python依赖
├── .env.example              # 环境变量示例
└── README.md                 # 项目文档
```

## 部署建议

### 生产环境部署

1. **使用Docker Compose**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

2. **配置HTTPS**
- 使用Nginx反向代理
- 配置SSL证书
- 开启HTTP/2

3. **数据库迁移**
- 生产环境建议使用PostgreSQL
- 配置数据备份策略

4. **监控告警**
- 配置Prometheus监控
- 设置Grafana仪表板
- 配置告警规则

### 性能调优

1. **Redis优化**
```bash
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
```

2. **应用优化**
- 调整worker进程数
- 配置连接池大小
- 启用请求压缩

## 常见问题

### Q: 如何提高响应速度？
A: 
1. 使用Redis缓存常见问答
2. 优化AI接口调用参数
3. 启用异步消息处理
4. 配置CDN加速

### Q: 如何处理高并发？
A:
1. 使用Docker水平扩展
2. 配置负载均衡
3. 启用限流机制
4. 优化数据库查询

### Q: 如何自定义AI回复？
A:
1. 修改`ai_service.py`中的系统提示词
2. 通过知识库管理添加专业回复
3. 调整AI模型参数

## 开发计划

- [ ] 支持语音消息识别
- [ ] 增加情感分析功能  
- [ ] 支持多媒体消息处理
- [ ] 增加客服工作台
- [ ] 支持微信群聊机器人

## 技术支持

如有问题请提交Issue或联系开发团队。

## 许可证

MIT License

---

**预算说明**: 本系统在15万预算内可实现完整功能，包括:
- 服务器部署: 2万/年
- AI接口费用: 8万/年 
- 开发维护: 5万
- 总计: 15万以内