@echo off
REM https://pyinstaller.org/en/stable/

FOR /F "usebackq tokens=* delims=" %%A IN (`time /t`) DO (
    SET "startTime=%%A")

python -m compileall . -q
echo The compileall errorlevels is %ERRORLEVEL%
if %ERRORLEVEL% NEQ 0 (
    echo "Error compiling python files"
    exit /b %ERRORLEVEL%
)

echo Removing previous build directories
rmdir /s /q dist
rmdir /s /q build

echo Starting PyInstaller build
pyinstaller harvest.spec --clean
REM pyinstaller harvest.spec --clean --log-level=DEBUG
echo Finished PyInstaller build
echo Creating zip archive
cd dist
tar -czf harvest.zip harvest.exe
cd ..

FOR /F "usebackq tokens=* delims=" %%A IN (`time /t`) DO (
    SET "endTime=%%A")


echo Start time: %startTime%
echo End time: %endTime%
