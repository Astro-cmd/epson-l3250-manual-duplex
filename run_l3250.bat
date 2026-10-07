@echo off
setlocal

REM Find Windows Python.
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py "%~dp0l3250_duplex.py"
    exit /b %ERRORLEVEL%
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python "%~dp0l3250_duplex.py"
    exit /b %ERRORLEVEL%
)

echo.
echo ERROR: Windows Python was not found.
echo Install Python for Windows, then install the requirements:
echo.
echo     py -m pip install -r requirements.txt
echo.
pause
exit /b 1
