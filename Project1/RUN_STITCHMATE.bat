@echo off
title StitchMate Atelier Server
color 0E

echo ========================================================
echo        StitchMate Atelier Management System
echo ========================================================
echo.

:: 1. Check & Start XAMPP MySQL
tasklist /FI "IMAGENAME eq mysqld.exe" 2>NUL | find /I /N "mysqld.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] MySQL is already running.
) else (
    echo [..] Starting MySQL service...
    start /B "" "C:\xampp\mysql\bin\mysqld.exe" --defaults-file=C:\xampp\mysql\bin\my.ini --standalone
    timeout /t 2 /nobreak >nul
)

:: 2. Check & Start XAMPP Apache (for phpMyAdmin)
tasklist /FI "IMAGENAME eq httpd.exe" 2>NUL | find /I /N "httpd.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] Apache / phpMyAdmin is already running.
) else (
    echo [..] Starting Apache for phpMyAdmin...
    start /B "" "C:\xampp\apache\bin\httpd.exe"
    timeout /t 1 /nobreak >nul
)

echo.
echo [OK] Opening StitchMate in your default browser...
start http://127.0.0.1:5000

echo.
echo ========================================================
echo   Web App:    http://127.0.0.1:5000
echo   phpMyAdmin: http://localhost/phpmyadmin
echo ========================================================
echo.
echo Press CTRL+C to stop the server when finished.
echo.

cd /d "%~dp0"
python app.py
pause
