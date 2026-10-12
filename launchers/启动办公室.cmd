@echo off
rem ===== Start the pixel office + background workers (hidden) =====
cd /d D:\徐\MunderDifflin\custom-cast
start "" "C:\Users\徐\AppData\Local\Programs\Python\Python312\pythonw.exe" "D:\徐\MunderDifflin\custom-cast\supervisor.py"
timeout /t 2 /nobreak >nul
start "" "D:\徐\MunderDifflin\Munder-Difflin-0.5.5-fixed\Munder Difflin.exe"
echo.
echo   Office starting (app + background driver/watchdog).
echo   To check whether anyone is working:
echo     python D:\徐\MunderDifflin\custom-cast\who_works.py
echo.
