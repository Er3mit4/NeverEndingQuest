@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"

REM ============================================================
REM  NeverEndingQuest - atualizador automatico do fork
REM
REM  O que ele faz:
REM   1. Busca e aplica as atualizacoes do upstream (origin/main)
REM   2. Preserva seu provider OpenCode Go (pasta fork_ext)
REM   3. Instala dependencias Python se o requirements.txt mudou
REM   4. Recompila o frontend se algo em web/frontend mudou
REM   5. Confere o provider e roda as verificacoes do OpenCode Go
REM
REM  Uso normal: clique duas vezes em atualizar.bat
REM  So verificar (sem atualizar): atualizar.bat --teste
REM ============================================================

set "LOG=%TEMP%\neverendingquest_update.log"
break > "%LOG%"

set "TEST_MODE="
if /i "%~1"=="--teste" set "TEST_MODE=1"
if /i "%~1"=="/teste" set "TEST_MODE=1"

echo ============================================================
echo   NeverEndingQuest - atualizacao automatica
echo ============================================================
if defined TEST_MODE echo   MODO DE VERIFICACAO (nada sera atualizado)
echo.
echo Log completo: %LOG%
echo.

REM ---------- 0. Ferramentas basicas ----------
where git >nul 2>&1
if errorlevel 1 goto :no_git

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 goto :not_repo

if not defined TEST_MODE (
    if exist ".git\MERGE_HEAD" goto :merge_in_progress
)

REM ---------- 1. Garantir que estamos na main ----------
for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "BRANCH=%%b"
if /i not "!BRANCH!"=="main" (
    echo Voce esta no branch "!BRANCH!". Trocando para main...
    git switch main >> "%LOG%" 2>&1
    if errorlevel 1 goto :switch_failed
)

REM ---------- 2. Alteracoes locais ----------
git status --porcelain --untracked-files=no > "%TEMP%\neq_status.txt" 2>nul
set "CHANGES=0"
for /f %%c in ('type "%TEMP%\neq_status.txt" ^| find /c /v ""') do set "CHANGES=%%c"
if not "!CHANGES!"=="0" (
    echo AVISO: existem alteracoes locais em arquivos versionados:
    type "%TEMP%\neq_status.txt"
    echo.
    echo Elas serao preservadas se nao conflitarem com a atualizacao.
    if not defined TEST_MODE (
        choice /c SN /n /m "Continuar mesmo assim? [S/N] "
        if errorlevel 2 goto :cancelled
    )
)

REM ---------- 3. Buscar e aplicar atualizacoes ----------
if not defined TEST_MODE (
    echo.
    echo Buscando atualizacoes do upstream...
    git fetch origin >> "%LOG%" 2>&1
    if errorlevel 1 goto :fetch_failed

    for /f "delims=" %%h in ('git rev-parse HEAD') do set "BEFORE=%%h"

    echo Aplicando atualizacoes ^(pode levar alguns minutos^)...
    git pull --no-rebase origin main >> "%LOG%" 2>&1
    set "PULL_RC=!ERRORLEVEL!"

    git diff --name-only --diff-filter=U > "%TEMP%\neq_conflicts.txt" 2>nul
    set "CONFLICTS=0"
    for /f %%c in ('type "%TEMP%\neq_conflicts.txt" ^| find /c /v ""') do set "CONFLICTS=%%c"
    if not "!CONFLICTS!"=="0" goto :conflicts
    if not "!PULL_RC!"=="0" goto :pull_failed

    for /f "delims=" %%h in ('git rev-parse HEAD') do set "AFTER=%%h"
    if "!BEFORE!"=="!AFTER!" (
        echo Ja estava atualizado ^(nenhum commit novo^).
    ) else (
        echo Atualizado: !BEFORE! -^> !AFTER!
    )

    git diff --name-only !BEFORE! !AFTER! > "%TEMP%\neq_changed.txt" 2>nul
) else (
    for /f "delims=" %%h in ('git rev-parse HEAD') do set "BEFORE=%%h"
    set "AFTER=!BEFORE!"
    break > "%TEMP%\neq_changed.txt"
)

REM ---------- 4. O que mudou? ----------
set "REQ_CHANGED=0"
set "FRONT_CHANGED=0"
for /f "usebackq delims=" %%f in ("%TEMP%\neq_changed.txt") do (
    if /i "%%f"=="requirements.txt" set "REQ_CHANGED=1"
    echo %%f | findstr /b /i /c:"web/frontend/" >nul
    if not errorlevel 1 set "FRONT_CHANGED=1"
)

REM ---------- 5. Python / venv ----------
set "PY=%~dp0venv\Scripts\python.exe"
if not exist "!PY!" (
    echo.
    echo Ambiente Python nao encontrado. Criando venv...
    where python >nul 2>&1
    if errorlevel 1 goto :no_python
    python -m venv venv >> "%LOG%" 2>&1
    if errorlevel 1 goto :venv_failed
    set "REQ_CHANGED=1"
)

if "!REQ_CHANGED!"=="1" (
    echo.
    echo Instalando dependencias Python ^(pode levar alguns minutos^)...
    "!PY!" -m pip install --upgrade pip >> "%LOG%" 2>&1
    "!PY!" -m pip install -r requirements.txt >> "%LOG%" 2>&1
    if errorlevel 1 goto :pip_failed
)

REM pytest e ferramenta de teste, nao vem no requirements.txt de producao.
"!PY!" -c "import pytest" >nul 2>&1
if errorlevel 1 (
    echo Instalando pytest...
    "!PY!" -m pip install pytest >> "%LOG%" 2>&1
)

REM ---------- 6. Frontend ----------
if "!FRONT_CHANGED!"=="1" (
    echo.
    echo Frontend mudou; recompilando...
    where npm >nul 2>&1
    if errorlevel 1 (
        echo AVISO: npm/Node.js nao encontrado.
        echo Instale o Node.js LTS e rode este atualizador de novo.
    ) else (
        pushd "web\frontend"
        call npm run build >> "%LOG%" 2>&1
        set "BUILD_RC=!ERRORLEVEL!"
        popd
        if not "!BUILD_RC!"=="0" goto :build_failed
        echo Frontend recompilado com sucesso.
    )
)

REM ---------- 7. Conferir o provider de IA ----------
echo.
echo Conferindo o provider de IA...
"!PY!" -c "import model_config; p=model_config.get_provider(); c=model_config.resolve_callsite_config('T013','opencodego') or {}; print('provider=' + str(p)); print('model=' + str(c.get('model')))" > "%TEMP%\neq_provider.txt" 2>> "%LOG%"
set "PROV_RC=!ERRORLEVEL!"
if not exist "fork_ext\registry.py" (
    echo AVISO: a pasta fork_ext nao foi encontrada.
    echo Sem ela o jogo usa o provider padrao ^(codex^), nao o OpenCode Go.
)
if not "!PROV_RC!"=="0" (
    echo ATENCAO: nao foi possivel carregar o model_config.
    echo Veja o log: %LOG%
    goto :finish_error
)
for /f "delims=" %%p in ('findstr /b /c:"provider=" "%TEMP%\neq_provider.txt"') do set "PROVIDER_LINE=%%p"
for /f "delims=" %%m in ('findstr /b /c:"model=" "%TEMP%\neq_provider.txt"') do set "MODEL_LINE=%%m"
echo   !PROVIDER_LINE!
echo   !MODEL_LINE!
findstr /c:"provider=opencodego" "%TEMP%\neq_provider.txt" >nul
if errorlevel 1 (
    echo   ^(o provider ativo nao e opencodego; se nao for intencional, abra
    echo    Settings -^> AI Provider e escolha OpenCode Go^)
)

REM ---------- 8. Verificacoes rapidas do bridge ----------
if exist "tests\test_opencodego_bridge.py" (
    echo.
    echo Rodando verificacoes do OpenCode Go...
    "!PY!" -m pytest tests\test_opencodego_bridge.py tests\test_opencodego_models.py -q >> "%LOG%" 2>&1
    if errorlevel 1 (
        echo ATENCAO: as verificacoes do OpenCode Go falharam.
        echo Nao abra o jogo ainda; envie o log para analise:
        echo   %LOG%
        goto :finish_error
    )
    echo Verificacoes do OpenCode Go: OK
)

REM ---------- 9. Suite completa (opcional) ----------
if not defined TEST_MODE (
    if exist "tests" (
        choice /c SN /n /m "Rodar a suite completa de testes agora? (~4 min) [S/N] "
        if not errorlevel 2 (
            echo.
            echo Rodando a suite completa...
            "!PY!" -m pytest tests web\frontend\e2e -q >> "%LOG%" 2>&1
            if errorlevel 1 (
                echo ATENCAO: a suite completa encontrou falhas.
                echo Nao abra o jogo ainda; envie o log para analise:
                echo   %LOG%
                goto :finish_error
            )
            echo Suite completa: OK
        )
    )
)

REM ---------- 10. Abrir o jogo ----------
if not defined TEST_MODE (
    choice /c SN /n /m "Abrir o jogo agora? [S/N] "
    if not errorlevel 2 (
        if exist "launch_game.bat" (
            start "" "%~dp0launch_game.bat"
        ) else (
            start "" "!PY!" run_web.py
        )
    )
)

echo.
echo ============================================================
echo   Atualizacao concluida com sucesso.
echo   !PROVIDER_LINE!  !MODEL_LINE!
echo   Log: %LOG%
echo ============================================================
if not defined TEST_MODE pause
exit /b 0

REM ============================================================
REM  Situacoes de erro / decisao
REM ============================================================

:no_git
echo ERRO: o Git nao foi encontrado no PATH.
echo Instale o Git para Windows (https://git-scm.com/download/win) e tente de novo.
goto :finish_error

:not_repo
echo ERRO: esta pasta nao parece ser o repositorio do jogo.
echo Coloque este arquivo atualizar.bat na pasta que contem o arquivo model_config.py.
goto :finish_error

:no_python
echo ERRO: o Python nao foi encontrado no PATH.
echo Instale o Python 3.9 ou mais novo (https://www.python.org/downloads/) e tente de novo.
goto :finish_error

:venv_failed
echo ERRO: nao foi possivel criar o ambiente Python (venv).
echo Veja o log: %LOG%
goto :finish_error

:pip_failed
echo ERRO: falha ao instalar as dependencias Python.
echo Veja o log: %LOG%
goto :finish_error

:switch_failed
echo ERRO: nao foi possivel trocar para o branch main.
echo Verifique se ha alteracoes pendentes com: git status
goto :finish_error

:fetch_failed
echo ERRO: nao foi possivel buscar as atualizacoes (sem internet?).
echo Tente de novo mais tarde. Nada foi alterado.
goto :finish_error

:pull_failed
echo.
echo ERRO: a atualizacao nao pode ser aplicada.
echo Causa comum: alteracoes locais em arquivos que o upstream tambem mudou.
echo Nada foi perdido; sua versao atual continua intacta.
echo Rode "git status" para ver os arquivos e tente de novo.
echo Log: %LOG%
goto :finish_error

:build_failed
echo.
echo ERRO: o frontend nao compilou.
echo O jogo continua com o build anterior. Veja o log: %LOG%
goto :finish_error

:merge_in_progress
echo.
echo Ha uma atualizacao/merge incompleta da vez anterior.
echo Se voce ainda nao terminou de resolver os conflitos, pode desfazer agora.
choice /c SN /n /m "Desfazer essa atualizacao incompleta e voltar ao estado anterior? [S/N] "
if errorlevel 2 (
    echo Nada foi alterado. Termine o merge manualmente ou rode este atualizador
    echo e escolha S para desfazer.
    goto :finish_error
)
git merge --abort >> "%LOG%" 2>&1
echo Atualizacao incompleta desfeita. Sua versao anterior continua funcionando.
goto :finish_error

:conflicts
echo.
echo CONFLITO durante a atualizacao nos arquivos:
type "%TEMP%\neq_conflicts.txt"
echo.
echo O atualizador NAO resolve conflitos sozinho, para nao perder codigo.
choice /c SN /n /m "Desfazer a atualizacao e manter a versao atual? [S/N] "
if errorlevel 2 (
    echo A atualizacao ficou pela metade.
    echo Resolva os conflitos e rode: git add . ^&^& git commit
    goto :finish_error
)
git merge --abort >> "%LOG%" 2>&1
echo Atualizacao desfeita. Sua versao anterior continua funcionando.
echo Envie o log para analise: %LOG%
goto :finish_error

:cancelled
echo.
echo Cancelado pelo usuario. Nada foi alterado.
if not defined TEST_MODE pause
exit /b 1

:finish_error
echo.
echo ============================================================
echo   A atualizacao NAO foi concluida.
echo   Log completo: %LOG%
echo ============================================================
choice /c SN /n /m "Abrir o log agora? [S/N] "
if not errorlevel 2 start "" notepad "%LOG%"
pause
exit /b 1
