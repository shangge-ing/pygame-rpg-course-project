@echo off
setlocal

set "ROOT=%~dp0"
cd /d "%ROOT%"
if errorlevel 1 (
    echo [ERROR] Failed to enter project directory:
    echo %ROOT%
    echo.
    pause
    exit /b 1
)

set "PYTHON_EXE=%ROOT%.venv\Scripts\python.exe"
set "MAIN_FILE=%ROOT%main.py"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python virtual environment was not found:
    echo %PYTHON_EXE%
    echo.
    echo Please create .venv and install requirements first.
    echo.
    pause
    exit /b 1
)

if not exist "%MAIN_FILE%" (
    echo [ERROR] main.py was not found:
    echo %MAIN_FILE%
    echo.
    echo Please put this script in the project root directory.
    echo.
    pause
    exit /b 1
)

if "%~1"=="--check" (
    echo Project directory: %ROOT%
    echo Python: %PYTHON_EXE%
    echo Entry: %MAIN_FILE%
    echo Check passed.
    exit /b 0
)

echo Starting Journey to the West...
echo.
"%PYTHON_EXE%" "%MAIN_FILE%"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ERROR] The game exited with code %EXIT_CODE%.
    echo Please check the error message above.
    echo.
    pause
)

exit /b %EXIT_CODE%
