@echo off
cd /d %~dp0\..\app\backend\api_server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
