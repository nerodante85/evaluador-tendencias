@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Arreglar el archivo de publicacion
echo.
echo ==========================================================
echo   ARREGLAR EL ARCHIVO DE PUBLICACION
echo ==========================================================
echo.
echo   El archivo llego a su carpeta pero con el contenido
echo   equivocado. Esto le pone el contenido bueno.
echo.

if not exist "deploy-workflow.yml" (
  echo   [!] No encuentro "deploy-workflow.yml" en esta carpeta.
  echo       Avisame y te lo vuelvo a mandar.
  echo.
  pause
  exit /b 1
)

if not exist ".github\workflows" mkdir ".github\workflows"
copy /y "deploy-workflow.yml" ".github\workflows\deploy.yml" >nul
del /q "deploy-workflow.yml"

echo   Revisando que haya quedado bien...
echo.
for %%A in (".github\workflows\deploy.yml") do set TAM=%%~zA
echo   Tamano del archivo: %TAM% bytes   ^(tiene que decir 1105^)
echo.
findstr /b /c:"name: Publicar panel" ".github\workflows\deploy.yml" >nul
if errorlevel 1 (
  echo   [!] Algo salio mal, el contenido no es el esperado.
  echo       Copiame lo que salga aqui arriba.
  echo.
  pause
  exit /b 1
)

echo   [OK] Quedo bien.
echo.
echo   ----------------------------------------------------
echo   AHORA, EN GITHUB DESKTOP:
echo.
echo     1. Abre GitHub Desktop.
echo     2. Vas a ver los cambios listados a la izquierda.
echo     3. Abajo escribe un mensaje, por ejemplo:
echo            arreglar archivo de publicacion
echo     4. Boton azul "Commit to main".
echo     5. Arriba, "Push origin".
echo.
echo   Dos minutos despues la pagina queda en vivo en:
echo   https://nerodante85.github.io/evaluador-tendencias/
echo   ----------------------------------------------------
echo.
pause
