@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found.
    echo Please run first: python -m venv .venv
    echo Then: .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo ========================================
echo   Idea Court
echo   Open: http://127.0.0.1:8000
echo   Stop: Ctrl + C
echo ========================================
echo.

.venv\Scripts\python.exe -m uvicorn main:app --reload

pause
