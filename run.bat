@echo off
echo Instalando ferramentas... Isso so acontece na primeira vez.
python -m pip install streamlit pandas openpyxl plotly
echo.
echo Abrindo o Sistema da Tesouraria do Gremio...
python -m streamlit run app.py
pause