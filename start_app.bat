@echo off
start "" "http://localhost:8501"
start /B py -m streamlit run app.py
timeout /t 5 > nul  # Ждём 5 секунд для запуска Streamlit
ngrok http 8501