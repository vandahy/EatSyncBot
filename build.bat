@echo off
chcp 65001 >nul
title Build Bot Đặt Cơm v1.0

echo ╔═══════════════════════════════════════════════════════════════╗
echo ║         BUILD SCRIPT - BOT ĐẶT CƠM TỰ ĐỘNG v1.0              ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

REM Kiểm tra Python có được cài đặt không
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ PYTHON CHƯA ĐƯỢC CÀI ĐẶT!
    echo    Vui lòng cài Python 3.9+ từ: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✓ Đã phát hiện Python
echo.

REM Kiểm tra PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo ⚠️  PyInstaller chưa được cài đặt
    echo    Đang cài đặt PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo ❌ Cài đặt PyInstaller thất bại!
        pause
        exit /b 1
    )
)

echo ✓ PyInstaller đã sẵn sàng
echo.

REM Xóa build cũ
echo 🗑️  Dọn dẹp build cũ...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"
echo ✓ Đã dọn dẹp
echo.

REM Build với PyInstaller
echo 🔨 Đang build file EXE...
echo    (Quá trình này có thể mất 2-5 phút)
echo.

pyinstaller --noconfirm ^
    --onefile ^
    --name "BotDatCom_v1.0" ^
    --hidden-import "pydantic" ^
    --hidden-import "pydantic.main" ^
    --hidden-import "pydantic.fields" ^
    --hidden-import "PIL" ^
    --hidden-import "PIL._imaging" ^
    --hidden-import "telethon" ^
    --hidden-import "telethon.sync" ^
    --hidden-import "telethon.events" ^
    --hidden-import "google.generativeai" ^
    --hidden-import "google.ai.generativelanguage" ^
    --hidden-import "genkit.core.schema" ^
    --collect-all "google.generativeai" ^
    --collect-all "telethon" ^
    bot.pyw

if errorlevel 1 (
    echo.
    echo ❌ BUILD THẤT BẠI!
    echo    Kiểm tra lỗi ở trên và thử lại
    pause
    exit /b 1
)

echo.
echo ═══════════════════════════════════════════════════════════════
echo ✅ BUILD THÀNH CÔNG!
echo ═══════════════════════════════════════════════════════════════
echo.
echo 📦 File EXE đã được tạo tại:
echo    %CD%\dist\BotDatCom_v1.0.exe
echo.
echo 📋 Kích thước file: 
for %%F in ("dist\BotDatCom_v1.0.exe") do echo    %%~zF bytes (≈ %%~zF KB)
echo.
echo ⚠️  LƯU Ý TRƯỚC KHI PHÂN PHỐI:
echo    1. KHÔNG đóng gói file .env hoặc .session
echo    2. KHÔNG đóng gói file config.json có dữ liệu thật
echo    3. Chỉ phân phối file .exe + Huong_dan_su_dung.txt
echo.
echo 📝 Các file cần phân phối:
echo    ✓ dist\BotDatCom_v1.0.exe
echo    ✓ Huong_dan_su_dung.txt
echo.

REM Mở thư mục dist
explorer "dist"

echo Nhấn phím bất kỳ để đóng...
pause >nul
