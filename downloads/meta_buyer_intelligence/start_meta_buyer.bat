@echo off
setlocal
cd /d "%~dp0"
title Meta Buyer Intelligence - startup diagnostics
set "MBI_TASK_SCRIPT=%~dp0meta_buyer_intelligence.py.txt"
echo Meta Buyer Intelligence launcher
echo.
if not exist "%MBI_TASK_SCRIPT%" goto missing_file
findstr /c:"def receive_chat(" "%MBI_TASK_SCRIPT%" >nul 2>&1
if errorlevel 1 goto wrong_file
echo Starting: "%MBI_TASK_SCRIPT%"
echo.
where py >nul 2>&1
if errorlevel 1 goto try_python
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)" >nul 2>&1
if errorlevel 1 goto try_python
py -3 -u "%MBI_TASK_SCRIPT%"
goto app_ended
:try_python
where python >nul 2>&1
if errorlevel 1 goto missing_python
python -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)" >nul 2>&1
if errorlevel 1 goto missing_python
python -u "%MBI_TASK_SCRIPT%"
goto app_ended
:app_ended
set "MBI_TASK_EXIT=%errorlevel%"
echo.
echo Application stopped. Exit code: %MBI_TASK_EXIT%
echo If it failed, copy the error text shown ABOVE this line.
echo Keep config.env, .env, mbi.db and .mbi_secret in this folder.
pause
exit /b %MBI_TASK_EXIT%
:missing_file
echo ERROR: meta_buyer_intelligence.py.txt was not found beside this launcher.
echo Put BOTH downloaded files into the SAME folder.
echo In Explorer, enable View - Show - File name extensions.
echo The app must be named exactly: meta_buyer_intelligence.py.txt
echo Do not run the old 9 KB Python file.
pause
exit /b 2
:wrong_file
echo ERROR: this app file is an old or incomplete version.
echo Download the latest meta_buyer_intelligence.py.txt, about 129 KB.
echo Keep the original .py.txt extension.
pause
exit /b 3
:missing_python
echo ERROR: Python 3.9 or newer could not be found.
echo Install a current Python from https://www.python.org/downloads/windows/
echo Then reopen this launcher.
pause
exit /b 4
