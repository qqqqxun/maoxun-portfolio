@echo off
echo 正在启动微信AI客服系统...

REM 检查是否存在.env文件
if not exist .env (
    echo 复制配置文件...
    copy .env.example .env
    echo 请编辑 .env 文件设置您的配置信息
    pause
)

REM 创建必要目录
if not exist data mkdir data
if not exist logs mkdir logs

REM 启动Redis (如果本地安装了Redis)
echo 检查Redis服务...
tasklist /FI "IMAGENAME eq redis-server.exe" 2>NUL | find /I /N "redis-server.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Redis已在运行
) else (
    echo 请确保Redis已启动，或使用Docker启动
)

REM 安装依赖
echo 安装Python依赖...
pip install -r requirements.txt

REM 启动应用
echo 启动AI客服系统...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause