@echo off
title 자동 종료 타이머
echo 자동 종료 타이머를 시작합니다...
echo 자정(00:00)에 컴퓨터가 자동으로 종료됩니다.
echo.

:: 필요한 패키지 확인 및 설치
pip show pystray >nul 2>&1
if %errorlevel% neq 0 (
    echo pystray 설치 중...
    pip install pystray Pillow
)

pip show Pillow >nul 2>&1
if %errorlevel% neq 0 (
    echo Pillow 설치 중...
    pip install Pillow
)

echo.
echo 트레이 아이콘이 실행됩니다. 시스템 트레이를 확인하세요.
pythonw auto_shutdown.pyw
