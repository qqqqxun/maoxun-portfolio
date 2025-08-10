#!/bin/bash

echo "🚀 部署微信AI客服系统"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 检查配置文件
if [ ! -f .env ]; then
    echo "📋 创建配置文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件配置您的服务信息"
    echo "📝 必填配置项："
    echo "   - WECHAT_TOKEN: 微信公众号Token"
    echo "   - WECHAT_APP_ID: 微信公众号AppID"
    echo "   - WECHAT_APP_SECRET: 微信公众号AppSecret"
    echo "   - OPENAI_API_KEY: AI服务API密钥"
    
    read -p "配置完成后按Enter继续..." -r
fi

# 创建必要目录
echo "📁 创建目录..."
mkdir -p data logs ssl

# 构建并启动服务
echo "🔨 构建Docker镜像..."
docker-compose build

echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 健康检查
echo "🏥 执行健康检查..."
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ 服务启动成功！"
    echo ""
    echo "🔗 访问地址："
    echo "   - API文档: http://localhost:8000/docs"
    echo "   - 健康检查: http://localhost:8000/"
    echo "   - 管理后台: http://localhost:8000/admin/"
    echo ""
    echo "📝 微信公众号配置："
    echo "   - 服务器URL: https://your-domain.com/wechat"
    echo "   - Token: 使用.env文件中的WECHAT_TOKEN"
    echo ""
else
    echo "❌ 服务启动失败，请检查日志："
    echo "   docker-compose logs app"
fi

echo "🎉 部署完成！"