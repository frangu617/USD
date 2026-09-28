@echo off
cd /d "%~dp0"
python app.py
if errorlevel 1 (
  echo Install dependencies first: python -m pip install -r requirements.txt
  pause
)
