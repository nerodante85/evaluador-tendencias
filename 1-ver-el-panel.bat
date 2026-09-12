@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Evaluador de Tendencias - ver el panel
echo.
echo ==========================================================
echo   EVALUADOR DE TENDENCIAS - abrir el panel en el navegador
echo ==========================================================
echo.

where node >nul 2>nul
if errorlevel 1 (
  echo [!] No encuentro Node.js instalado en este computador.
  echo.
  echo     El panel lo necesita para funcionar. Instalalo desde:
  echo        https://nodejs.org       ^(descarga el boton "LTS"^)
  echo.
  echo     Instalalo, cierra esta ventana y vuelve a dar doble clic aqui.
  echo.
  pause
  exit /b 1
)

echo [1/3] Acomodando el archivo de publicacion...
if exist "deploy-workflow.yml" (
  if not exist ".github\workflows" mkdir ".github\workflows"
  move /y "deploy-workflow.yml" ".github\workflows\deploy.yml" >nul
  echo       Listo: .github\workflows\deploy.yml
) else (
  echo       Ya estaba acomodado, sigo.
)

echo.
echo [2/3] Instalando lo que el panel necesita...
echo       ^(la primera vez tarda uno o dos minutos^)
echo.
call npm install
if errorlevel 1 (
  echo.
  echo [!] Fallo la instalacion. Copia el mensaje de arriba y mandamelo.
  echo.
  pause
  exit /b 1
)

echo.
echo [3/3] Abriendo el panel...
echo.
echo     Se va a abrir en tu navegador: http://localhost:5173
echo.
echo     DEJA ESTA VENTANA ABIERTA mientras lo miras.
echo     Para cerrar el panel: vuelve aqui y presiona Ctrl+C.
echo.
timeout /t 4 >nul
start "" http://localhost:5173
call npm run dev

pause
