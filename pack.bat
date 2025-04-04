
@echo off
setlocal enabledelayedexpansion

REM ---------- 启用 ANSI 颜色支持 ----------
reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1
chcp 65001 >nul

REM ---------- 定义 ANSI 颜色变量 ----------
for /f %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "COLOR_GREEN=%ESC%[32m"
set "COLOR_RED=%ESC%[31m"
set "COLOR_YELLOW=%ESC%[33m"
set "COLOR_RESET=%ESC%[0m"

REM ---------- 配置变量 ----------
set "PROJECT_ROOT=%~dp0"
set "PYTHON_EMBED_URL=https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip"
set "PYTHON_DIR=%PROJECT_ROOT%python"
set "GET_PIP_URL=https://bootstrap.pypa.io/get-pip.py"

REM ---------- 步骤1: 下载并解压嵌入式Python ----------
echo %COLOR_YELLOW%[STEP 1] 正在下载并解压嵌入式Python...%COLOR_RESET%
if not exist "%PYTHON_DIR%" mkdir "%PYTHON_DIR%"
curl -Lo "%PROJECT_ROOT%python-embed.zip" "%PYTHON_EMBED_URL%"
if errorlevel 1 (
  echo %COLOR_RED%错误: 下载嵌入式Python失败!%COLOR_RESET%
  pause
  exit /b 1
)
tar -xf "%PROJECT_ROOT%python-embed.zip" -C "%PYTHON_DIR%"
if errorlevel 1 (
  echo %COLOR_RED%错误: 解压失败!%COLOR_RESET%
  pause
  exit /b 1
)
del "%PROJECT_ROOT%python-embed.zip"

REM ---------- 步骤2: 修改.pth文件 ----------
set "PYTHON_PTH=%PYTHON_DIR%\python310._pth"  REM 注意文件名可能为 python310._pth，根据实际调整
echo %COLOR_YELLOW% [STEP 2] 修改 '%PYTHON_PTH%' 文件... %COLOR_RESET%

if exist "%PYTHON_PTH%" (
  powershell -Command "(Get-Content '%PYTHON_PTH%') -replace '#import site','import site' | Set-Content '%PYTHON_PTH%'"
  echo %COLOR_GREEN%成功启用 import site!%COLOR_RESET%
) else (
  echo %COLOR_RED%错误: 未找到 %PYTHON_PTH%!%COLOR_RESET%
  pause
  exit /b 1
)

REM ---------- 步骤3: 安装pip ----------
echo %COLOR_YELLOW%[STEP 3] 安装pip...%COLOR_RESET%
if not exist "%PROJECT_ROOT%get-pip.py" (
  curl -Lo "%PROJECT_ROOT%get-pip.py" "%GET_PIP_URL%"
)
if not exist "%PROJECT_ROOT%get-pip.py" (
  echo %COLOR_RED%错误: 下载 get-pip.py 失败!%COLOR_RESET%
  pause
  exit /b 1
)
"%PYTHON_DIR%\python.exe" "%PROJECT_ROOT%get-pip.py"
if errorlevel 1 (
  echo %COLOR_RED%错误: 安装 pip 失败!%COLOR_RESET%
  pause
  exit /b 1
)

REM ---------- 步骤4: 安装依赖 ----------
echo %COLOR_YELLOW%[STEP 4] 安装项目依赖...%COLOR_RESET%
if exist "%PROJECT_ROOT%requirements.txt" (
  "%PYTHON_DIR%\Scripts\pip.exe" install -r "%PROJECT_ROOT%requirements.txt"
) else (
  echo %COLOR_RED%错误: 未找到 requirements.txt!%COLOR_RESET%
  pause
  exit /b 1
)

REM ---------- 步骤5: 清理.env和get-pip.py文件 ----------
echo %COLOR_YELLOW%[STEP 5] 清理.env文件...%COLOR_RESET%
if exist "%PROJECT_ROOT%.env" (
  del "%PROJECT_ROOT%.env"
  echo %COLOR_GREEN%已删除 .env 文件%COLOR_RESET%
)
if exist "%PROJECT_ROOT%get-pip.py" (
  del "%PROJECT_ROOT%get-pip.py"
  echo %COLOR_GREEN%已删除 get-pip.py 文件%COLOR_RESET%
)

echo %COLOR_GREEN%[完成] 所有步骤已成功完成!%COLOR_RESET%
pause