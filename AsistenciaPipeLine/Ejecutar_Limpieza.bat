@echo off
cd /d "%~dp0"
REM Activa el venv si tienes uno, o asume Python en PATH
REM call .venv\Scripts\activate

python procesar_asistencia.py
echo.
echo === Proceso terminado. Presiona una tecla para cerrar. ===
pause >nul
