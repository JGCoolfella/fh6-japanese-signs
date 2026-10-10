@echo off
rem Opens the FH6 sign catalogue; choices and uploaded images are saved to _modwork\catalogue\choices
cd /d "%~dp0"
python tools\catalogue_server.py
pause
