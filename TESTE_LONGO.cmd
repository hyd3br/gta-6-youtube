@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  if errorlevel 1 goto erro
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 goto erro
)
.venv\Scripts\python.exe make_long.py --tts bundled --preview-scenes 2 --width 640 --height 360 --fps 24 --output output/aguardando_revisao/preview_longo_640.mp4
if errorlevel 1 goto erro
start "" "output\aguardando_revisao\preview_longo_640.mp4"
echo Teste concluido. Reveja o arquivo de video e checklist.
pause
exit /b 0
:erro
echo Erro. Confira Python/FFmpeg instalados e o README.md.
pause
exit /b 1
