#!/bin/bash
cd app
source venv/bin/activate
cd backend/api_server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload