@echo off
rem ===== Stop the pixel office + all background workers =====
taskkill /IM "Munder Difflin.exe" /F >nul 2>&1
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq pythonw.exe" /fo list ^| findstr /i "PID:"') do taskkill /PID %%i /F >nul 2>&1
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo list ^| findstr /i "PID:"') do taskkill /PID %%i /F >nul 2>&1
echo.
echo   All stopped (office + background). Nothing will restart by itself.
echo.
