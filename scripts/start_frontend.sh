#!/bin/bash
cd app
source venv/bin/activate
cd frontend/server
python flask_server.py
