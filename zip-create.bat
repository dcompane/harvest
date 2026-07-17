REM https://pyinstaller.org/en/stable/
python -m compileall . -q
echo the errorlevels is %ERRORLEVEL%
if %ERRORLEVEL% NEQ 0 (
    echo "Error compiling python files"
    exit /b %ERRORLEVEL%
)
rmdir /s /q dist
rmdir /s /q build

goto :next
setlocal enabledelayedexpansion

REM === Configuration ===
set "PY_FILE=Utility-copy.py"   REM Python file containing the version variable
set "VAR_NAME=harverst_version"    REM Name of the variable to update

REM === Read the current version from the Python file ===
for /f "tokens=2 delims==" %%A in ('findstr /i "^%VAR_NAME% *=" "%PY_FILE%"') do (
    set "ver=%%~A"
)

echo %ver%

REM Remove quotes and spaces
set "ver=%ver:"=%"
set "ver=%ver: =%"

REM "Split into major.minor.patch"
for /f "tokens=1-3 delims=." %%a in ("%ver%") do (
    set "major=%%a"
    set "minor=%%b"
    set "patch=%%c"
)

REM === Increment patch number ===
set /a patch=patch+1

REM === Build new version string ===
set "newver=%major%.%minor%.%patch%"

REM === Update the Python file ===
(for /f "usebackq delims=" %%L in ("%PY_FILE%") do (
    set "line=%%L"
    setlocal enabledelayedexpansion
    if "!line!"=="%VAR_NAME% = '%ver%'" (
        echo %VAR_NAME% = '%newver%'
    ) else if "!line!"=="%VAR_NAME% = \"%ver%\"" (
        echo %VAR_NAME% = "%newver%"
    ) else (
        echo !line!
    )
    endlocal
)) > "%PY_FILE%.tmp"

move /y "%PY_FILE%.tmp" "%PY_FILE%" >nul

echo Updated %VAR_NAME% from %ver% to %newver%
endlocal







:next

pyinstaller harvest.spec --clean --noconfirm
REM pyinstaller harvest.spec --clean --noconfirm --log-level=DEBUG
cd dist
tar -czf harvest.zip harvest.exe
cd ..