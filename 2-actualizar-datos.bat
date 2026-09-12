@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Evaluador de Tendencias - actualizar datos
echo.
echo ==========================================================
echo   ACTUALIZAR LOS DATOS DEL RADAR
echo ==========================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [!] No encuentro Python instalado en este computador.
  echo.
  echo     Instalalo desde https://www.python.org/downloads/
  echo     IMPORTANTE: en la primera pantalla del instalador marca
  echo     la casilla "Add python.exe to PATH" antes de continuar.
  echo.
  pause
  exit /b 1
)

echo Que quieres actualizar?
echo.
echo   [1] Solo la tasa de cambio ^(TRM^)  - tarda 5 segundos
echo   [2] Las 30 senales de Google Trends - tarda unos 10 minutos
echo   [3] Las dos cosas
echo.
set /p opcion="Escribe 1, 2 o 3 y presiona Enter: "
echo.

echo Revisando que este todo instalado...
call python -m pip install -q -r requirements.txt
if errorlevel 1 (
  echo.
  echo [!] Fallo la instalacion de las librerias. Mandame el mensaje de arriba.
  echo.
  pause
  exit /b 1
)
echo.

if "%opcion%"=="1" goto macro
if "%opcion%"=="2" goto trends
if "%opcion%"=="3" goto ambos
echo No entendi la opcion. Cierra y vuelve a intentar.
pause
exit /b 1

:ambos
:macro
echo --- Consultando la TRM oficial ---
call python fetch_macro.py
if "%opcion%"=="1" goto fin
echo.

:trends
echo --- Consultando Google Trends: 30 senales ---
echo     Esto tarda unos 10 minutos. Puedes minimizar la ventana.
echo.
call python fetch_trends.py

:fin
echo.
echo ==========================================================
echo   LISTO
echo ==========================================================
echo.
echo   Los datos nuevos ya estan en el panel.
echo   Abre "1-ver-el-panel.bat" para mirarlos.
echo.
echo   Cuando quieras publicarlos en internet, abre GitHub Desktop
echo   y dale a "Commit" y luego "Push origin".
echo.
pause
