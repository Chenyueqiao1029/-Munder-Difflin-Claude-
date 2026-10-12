@echo off
rem ===== Custom character: drag an image onto this file, or double-click =====
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo   StarHive Office - Custom Character
echo   (drag an image file onto this .cmd, or just double-click and pick one)
echo.
python "tools\customize.py" char %*
echo.
if "%~1"=="" pause
