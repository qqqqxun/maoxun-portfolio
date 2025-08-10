@echo off
echo 🚀 部署微信AI客服系统

REM 检查Docker是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker未安装，请先安装Docker Desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose未安装，请先安装Docker Compose
    pause
    exit /b 1
)

REM 检查配置文件
if not exist .env (
    echo 📋 创建配置文件...
    copy .env.example .env
    echo ⚠️  请编辑 .env 文件配置您的服务信息
    echo 📝 必填配置项：
    echo    - WECHAT_TOKEN: 微信公众号Token
    echo    - WECHAT_APP_ID: 微信公众号AppID
    echo    - WECHAT_APP_SECRET: 微信公众号AppSecret
    echo    - OPENAI_API_KEY: AI服务API密钥
    echo.
    pause
)

REM 创建必要目录
echo 📁 创建目录...
if not exist data mkdir data
if not exist logs mkdir logs
if not exist ssl mkdir ssl

REM 构建并启动服务
echo 🔨 构建Docker镜像...
docker-compose build

echo 🚀 启动服务...
docker-compose up -d

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo 📊 检查服务状态...
docker-compose ps

REM 健康检查
echo 🏥 执行健康检查...
curl -f http://localhost:8000/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 服务启动成功！
    echo.
    echo 🔗 访问地址：
    echo    - API文档: http://localhost:8000/docs
    echo    - 健康检查: http://localhost:8000/
    echo    - 管理后台: http://localhost:8000/admin/
    echo.
    echo 📝 微信公众号配置：
    echo    - 服务器URL: https://your-domain.com/wechat
    echo    - Token: 使用.env文件中的WECHAT_TOKEN
    echo.
) else (
    echo ❌ 服务启动失败，请检查日志：
    echo    docker-compose logs app
)

echo 🎉 部署完成！
pause