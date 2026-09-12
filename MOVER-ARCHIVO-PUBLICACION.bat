@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Mover el archivo de publicacion a su carpeta
echo.
echo ==========================================================
echo   ACOMODAR EL ARCHIVO DE PUBLICACION
echo ==========================================================
echo.
echo   Esto solo mueve un archivo de sitio. No instala nada,
echo   no necesita internet y tarda un segundo.
echo.

if not exist "deploy-workflow.yml" (
  if exist ".github\workflows\deploy.yml" (
    echo   [OK] Ya estaba acomodado. No hay nada que hacer.
    echo.
    goto fin
  )
  echo   [!] No encuentro "deploy-workflow.yml" en esta carpeta
  echo       y tampoco ".github\workflows\deploy.yml".
  echo.
  echo       Avisame y te lo vuelvo a mandar.
  echo.
  goto fin
)

if not exist ".github\workflows" mkdir ".github\workflows"
move /y "deploy-workflow.yml" ".github\workflows\deploy.yml" >nul

if exist ".github\workflows\deploy.yml" (
  echo   [OK] Listo. El archivo quedo en:
  echo        .github\workflows\deploy.yml
  echo.
  echo   ----------------------------------------------------
  echo   AHORA, EN GITHUB DESKTOP:
  echo.
  echo     1. Abre GitHub Desktop.
  echo     2. Arriba a la izquierda dale a "Fetch origin" y
  echo        espera a que termine.
  echo     3. Abajo a la izquierda escribe un mensaje, por
  echo        ejemplo:  activar publicacion
  echo     4. Boton azul "Commit to main".
  echo     5. Arriba dale a "Push origin".
  echo.
  echo   Dos minutos despues la pagina queda en vivo.
  echo   ----------------------------------------------------
) else (
  echo   [!] No pude moverlo. Copiame lo que salga aqui arriba.
)

:fin
echo.
pause
