@echo off
setlocal

echo === Installing build dependencies ===
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo === Running unit tests ===
python -m pip install -r requirements-dev.txt
python -m pytest tests/ -v
if errorlevel 1 (
    echo Tests failed. Aborting build.
    pause
    exit /b 1
)

echo.
echo === Building executable ===
python -m PyInstaller --noconfirm --onefile --windowed --name Claude3pSetup claude_3p_gui.py
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo === Build complete: dist\Claude3pSetup.exe ===
pause
