@echo off
REM run-harvest-env.bat
REM Usage: run-harvest-env.bat dev|test|prod

if "%~1"=="" goto usage
set "ENV=%~1"

if /I "%ENV%"=="dev" goto dev
if /I "%ENV%"=="test" goto test
if /I "%ENV%"=="prod" goto prod
goto usage

:dev
set "BASE_URL=https://dev-aapi.example.com:8443/automation-api"
set "API_KEY=<YOUR_DEV_API_KEY>"
set "INCLUDE=deploy,config,auth"
set "OUTPUT=dev_ctm_inventory"
goto run

:test
set "BASE_URL=https://test-aapi.example.com:8444/automation-api"
set "API_KEY=<YOUR_TEST_API_KEY>"
set "INCLUDE=deploy,config,auth"
set "OUTPUT=test_ctm_inventory"
goto run

:prod
set "BASE_URL=https://prod-aapi.example.com:8444/automation-api"
set "API_KEY=<YOUR_PROD_API_KEY>"
set "INCLUDE=deploy,config,auth"
set "OUTPUT=prod_ctm_inventory"
goto run

:run
python "%~dp0\harvest.py" --base-url "%BASE_URL%" --api-key "%API_KEY%" --include "%INCLUDE%" --output "%OUTPUT%" --debug True
echo.
echo Finished harvesting for %ENV% environment.
goto :eof

:usage
echo Usage: %~nx0 dev ^| test ^| prod
echo.
echo Example: %~nx0 prod
exit /b 1
