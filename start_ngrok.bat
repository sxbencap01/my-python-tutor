@echo off
chcp 65001 > nul
echo ================================================
echo  Python 学习导师 - 公网部署助手
echo ================================================
echo.

:: 检查 ngrok 是否存在
where ngrok >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 未检测到 ngrok，正在尝试用 winget 安装...
    winget install --id Ngrok.Ngrok -e --silent
    if %errorlevel% neq 0 (
        echo.
        echo [错误] 自动安装失败，请手动安装 ngrok：
        echo   1. 访问 https://ngrok.com/download
        echo   2. 下载 Windows 版本，解压到任意目录
        echo   3. 把 ngrok.exe 放到本脚本同目录，或添加到 PATH
        echo.
        pause
        exit /b 1
    )
    echo [OK] ngrok 安装完成
)

:: 进入项目目录
cd /d "%~dp0"
echo [1/3] 项目目录: %cd%
echo.

:: 安装依赖
echo [2/3] 检查并安装依赖...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [警告] 依赖安装可能有问题，尝试继续...
)
echo [OK] 依赖检查完成
echo.

:: 启动 Flask（后台）
echo [3/3] 启动 Flask 服务（端口 5000）...
start "Flask-Server" /min python app_flask.py

:: 等待 Flask 启动
timeout /t 3 /nobreak > nul

:: 启动 ngrok 并输出公网地址
echo.
echo ================================================
echo  正在建立公网隧道，请稍候...
echo  启动后会显示公网地址，Ctrl+C 停止服务
echo ================================================
echo.
ngrok http 5000 --log=stdout

echo.
echo [已停止] 服务已关闭
pause
