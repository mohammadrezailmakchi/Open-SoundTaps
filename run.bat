@echo off
setlocal

:: Set your virtual environment folder name
set VENV_NAME=venv

echo ---------------------------------------
echo Creating virtual environment...
python -m venv %VENV_NAME%
if errorlevel 1 goto error

echo Activating virtual environment...
call %VENV_NAME%\Scripts\activate.bat
if errorlevel 1 goto error

echo Installing dependencies...
%VENV_NAME%\Scripts\python.exe -m pip install --upgrade pip
%VENV_NAME%\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 goto error

echo ---------------------------------------
echo Running your app...
echo.
%VENV_NAME%\Scripts\python.exe main.py
if errorlevel 1 goto error

echo.
echo ✅ App finished successfully.
pause
goto end

:error
echo.
echo ❌ An error occurred during setup or app execution!
pause

:end
endlocal
