REM https://pyinstaller.org/en/stable/
pyinstaller harvest.spec --clean --noconfirm
REM pyinstaller harvest.spec --clean --noconfirm --log-level=DEBUG
cd dist
tar -czf harvest.zip harvest.exe