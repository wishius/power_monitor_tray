@echo off
echo ======================================================
echo    BUILDING ONEFILE EXE: monitor_tray.exe
echo ======================================================

REM ---------------------------------------------
REM 1) ПЕРЕВІРКА НАЯВНОСТІ PLAYWRIGHT БРАУЗЕРІВ
REM ---------------------------------------------
set "PW_DIR=%USERPROFILE%\AppData\Local\ms-playwright"

if not exist "%PW_DIR%" (
    echo.
    echo ❌ НЕ ЗНАЙДЕНО PLAYWRIGHT БРАУЗЕРІВ!
    echo.
    echo 🔧 Запустіть команду:
    echo     playwright install chromium
    echo.
    pause
    exit /b
)

echo 📁 Playwright знайдено за шляхом:
echo     %PW_DIR%
echo.


REM ---------------------------------------------
REM 2) КОПІЮЄМО БРАУЗЕРИ У ЧАСОВУ ПАПКУ ДЛЯ ONEFILE
REM ---------------------------------------------
echo 🔄 Копіюємо браузери у temp_playwright...
rmdir /s /q temp_playwright >nul 2>&1
xcopy "%PW_DIR%" "temp_playwright" /E /I /Q >nul
echo ✔ temp_playwright створено.
echo.


REM ---------------------------------------------
REM 3) ЗБІРКА EXE З PYINSTALLER
REM ---------------------------------------------
echo 🚀 Запускаємо PyInstaller...

pyinstaller ^
  --onefile ^
  --noconsole ^
  --icon=icon.ico ^
  --add-data "icon.png;." ^
  --add-data "temp_playwright;playwright" ^
  --name monitor_tray ^
  monitor_tray.py

echo.
echo ======================================================
echo    ✔ ГОТОВО!
echo    EXE файл знаходиться тут:
echo        dist\monitor_tray.exe
echo ======================================================
pause
