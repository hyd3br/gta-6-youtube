@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Execute TESTE_LONGO.cmd para preparar o ambiente.
  pause
  exit /b 1
)
.venv\Scripts\python.exe make_long.py --tts bundled
if errorlevel 1 (
  echo Ocorreu um erro. Consulte README.md.
  pause
  exit /b 1
)
echo Episodio completo em output\aguardando_revisao\gta6_analise_longa.mp4
pause
