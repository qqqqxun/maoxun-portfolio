#!/bin/bash

echo "正在启动微信AI客服系统..."

# 检查是否存在.env文件
if [ ! -f .env ]; then
    echo "复制配置文件..."
    cp .env.example .env
    echo "请编辑 .env 文件设置您的配置信息"
    read -p "按任意键继续..."
fi

# 创建必要目录
mkdir -p data logs

# 检查Redis是否运行
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Redis未运行，正在启动Redis..."
    redis-server --daemonize yes
else
    echo "Redis已在运行"
fi

# 安装依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 启动应用
echo "启动AI客服系统..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload