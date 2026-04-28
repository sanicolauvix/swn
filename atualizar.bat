@echo off
chcp 65001 > nul
echo.
echo  SWN Imoveis — Atualizando site...
echo  ────────────────────────────────
echo.

cd /d "%~dp0"

python build.py
if errorlevel 1 (
    echo.
    echo  ERRO no build. Site nao atualizado.
    pause
    exit /b 1
)

echo.
git add -A
git diff --cached --quiet
if errorlevel 1 (
    for /f "tokens=*" %%d in ('powershell -command "Get-Date -Format \"yyyy-MM-dd HH:mm\""') do set DT=%%d
    git commit -m "update: midia e status [%DT%]"
    git push
    echo.
    echo  Site publicado com sucesso!
) else (
    echo  Nenhuma alteracao detectada. Site ja esta atualizado.
)

echo.
pause
