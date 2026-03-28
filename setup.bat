@echo off
echo ========================================
echo   Nova Voice Assistant - Setup
echo ========================================
echo.

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found! Install Python 3.10+ from python.org
    pause
    exit /b 1
)

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Failed to install dependencies.
    echo If PyAudio fails, download the .whl from:
    echo   https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
    echo Then: pip install path\to\PyAudio.whl
    pause
    exit /b 1
)

:: Check for API key
if "%GEMINI_API_KEY%"=="" (
    echo.
    echo ----------------------------------------
    echo  GEMINI_API_KEY is not set!
    echo  Get a free key: https://aistudio.google.com/apikey
    echo.
    set /p GEMINI_API_KEY="  Paste your API key here: "
    setx GEMINI_API_KEY "%GEMINI_API_KEY%"
    echo  Saved! Key will persist across restarts.
    echo ----------------------------------------
)

echo.
echo Building Nova.exe...
python build.py

echo.
echo ========================================
echo   Setup complete!
echo   Run dist\Nova.exe to start Nova.
echo ========================================
pause
