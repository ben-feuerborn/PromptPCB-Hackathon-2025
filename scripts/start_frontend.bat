@echo off
cd /d %~dp0\..\app\frontend\server
python flask_server.py
pause
