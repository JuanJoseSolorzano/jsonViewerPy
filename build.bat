@echo off
setlocal
cd /d "%~dp0"

echo === Installing dependencies ===
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo === Building executable ===
python -m PyInstaller --clean --noconfirm JsonFormViewer.spec
if errorlevel 1 goto :error

echo.
echo === Build complete ===
echo Executable: %CD%\dist\JsonFormViewer.exe
goto :eof

:error
echo.
echo Build FAILED. See output above for details.
exit /b 1
