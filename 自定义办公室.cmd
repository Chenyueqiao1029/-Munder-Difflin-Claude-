@echo off
rem ===== Custom office: drag a top-down scene image onto this file =====
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo   StarHive Office - Custom Office
echo   (drag a top-down office image onto this .cmd, or just double-click and pick one)
echo.
python "tools\customize.py" office %*
echo.
if "%~1"=="" pause
