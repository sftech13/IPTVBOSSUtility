@echo off
setlocal EnableExtensions EnableDelayedExpansion

:: Detect if running in non-interactive (argument) mode
set "arg_mode=false"
if not "%~1"=="" (
    set "arg_mode=true"
    set "choice=%~1"
)

title IPTVBoss Maintenance Utility
color 0A

:: ====== Configuration ======
set "IPTV_PATH=C:\Users\%USERNAME%\IPTVBoss"
set "LOG_PATH=%IPTV_PATH%\logs"
set "BACKUP_SRC=%IPTV_PATH%\backups"
set "BACKUP_DEST=%USERPROFILE%\Desktop\IPTVBoss_Backup"
set "DB_PATH=%IPTV_PATH%\db"
set "TEMP_PATH=%IPTV_PATH%\temp"
set "CACHE_PATH=%IPTV_PATH%\cache"

:MENU
if "%arg_mode%"=="true" goto DISPATCH
cls
echo ========================================
echo        IPTVBoss Maintenance Menu
echo ========================================
echo 1.  Kill IPTVBoss Process
echo 2.  Clean Lock, Temp, and Cache Files (Logs preserved)
echo 3.  Run NoGUI Fix (keep IPTVBoss.mv.db) ^& Run NoGUI Sync
echo 4.  Check Connectivity to IPTVBoss
echo 5.  View Last 50 Lines from Log File
echo 6.  DB Reset (wipe current DB)
echo 7.  Check Antivirus Status
echo 8.  Check Windows Defender Status
echo 9.  Toggle Defender Real-Time Protection
echo 10. Exit
echo.
set /p choice="Select an option [1-10]: "

:DISPATCH
if "%choice%"=="1" goto KILL_PROCESS
if "%choice%"=="2" goto CLEAN_FILES
if "%choice%"=="3" goto RUN_NOGUI_FIX
if "%choice%"=="4" goto DNS_CHECK
if "%choice%"=="5" goto TAIL_LOG
if "%choice%"=="6" goto MOVE_BACKUPS
if "%choice%"=="7" goto CHECK_AV
if "%choice%"=="8" goto CHECK_DEFENDER
if "%choice%"=="9" goto TOGGLE_DEFENDER
if "%choice%"=="10" exit /b 0
goto MENU

:KILL_PROCESS
echo.
tasklist | findstr /I "IPTVBoss.exe" >nul
if %errorlevel%==0 (
    echo Terminating IPTVBoss.exe...
    taskkill /F /IM IPTVBoss.exe >nul 2>&1
    echo IPTVBoss.exe terminated.
) else (
    echo IPTVBoss is not currently running.
)
if "%arg_mode%"=="true" exit /b 0
pause
goto MENU

:CLEAN_FILES
echo.
echo Cleaning lock, temp, and cache files (preserving logs)...
del /f /q "%IPTV_PATH%\*.lock" >nul 2>&1
del /f /q "%TEMP_PATH%\*.*"    >nul 2>&1
del /f /q "%CACHE_PATH%\*.*"   >nul 2>&1
echo Cleanup complete.
if "%arg_mode%"=="true" exit /b 0
pause
goto MENU

:RUN_NOGUI_FIX
echo.
echo [1/5] Killing any running IPTVBoss process...
taskkill /F /IM IPTVBoss.exe >nul 2>&1

echo [2/5] Waiting for clean shutdown...
timeout /t 5 /nobreak >nul

echo [3/5] Cleaning DB folder (keeping IPTVBoss.mv.db)...
for %%f in ("%DB_PATH%\*") do (
    if /I not "%%~nxf"=="IPTVBoss.mv.db" (
        echo Deleting: %%~nxf
        del /f /q "%%f" >nul 2>&1
    )
)

echo [4/5] Launching NoGUI sync...
cd /d "%IPTV_PATH%"
start "" /B IPTVBoss.exe -nogui

echo [5/5] Monitoring NoGUI sync (checks every 10s)...
:WAIT_LOOP
timeout /t 10 /nobreak >nul
tasklist /FI "IMAGENAME eq IPTVBoss.exe" | find /I "IPTVBoss.exe" >nul
if %ERRORLEVEL%==0 (
    echo noGUI sync is still running...
    goto WAIT_LOOP
)

echo NoGUI sync finished. You may now launch IPTVBoss normally.
if "%arg_mode%"=="true" exit /b 0
pause
goto MENU

:DNS_CHECK
echo.
echo === Network ^& Endpoint Connectivity Test ===
echo.
echo Checking DNS resolution for download.iptvboss.pro ...
nslookup download.iptvboss.pro >nul
if %errorlevel% neq 0 (
    powershell -Command "Write-Host '[FAIL] DNS resolution failed.' -ForegroundColor Red"
) else (
    powershell -Command "Write-Host '[PASS] DNS resolved successfully.' -ForegroundColor Green"
)
echo.
echo Pinging download.iptvboss.pro ...
ping -n 4 download.iptvboss.pro >nul
if %errorlevel% neq 0 (
    powershell -Command "Write-Host '[WARN] Ping failed or timed out.' -ForegroundColor Yellow"
) else (
    powershell -Command "Write-Host '[PASS] Ping successful.' -ForegroundColor Green"
)
echo.
echo Sending HTTP HEAD request to verify availability ...
powershell -Command ^
  "try { $r=Invoke-WebRequest -Uri 'https://download.iptvboss.pro' -UseBasicParsing -Method Head; if ($r.StatusCode -eq 200) { Write-Host '[PASS] HTTP 200 OK' -ForegroundColor Green } else { Write-Host ('[WARN] HTTP status code ' + $r.StatusCode) -ForegroundColor Yellow } } catch { Write-Host ('[FAIL] HTTP request failed - ' + $_.Exception.Message) -ForegroundColor Red }"
echo.
if "%arg_mode%"=="false" (
    set /p doTrace="Would you like to run a traceroute? (Y/N): "
    if /I "%doTrace%"=="Y" (
        echo.
        echo Running traceroute...
        tracert download.iptvboss.pro
        echo.
        pause
    )
)
if "%arg_mode%"=="true" exit /b 0
pause
goto MENU

:TAIL_LOG
echo.
echo Log Type Filters:
echo 1. IPTVBoss Logs
echo 2. AdvEPGDummy Logs
echo 3. NoGUI Logs
echo 4. All Logs
if "%arg_mode%"=="false" set /p logtype="Select log type to filter [1-4]: "
if "%logtype%"=="1" set "FILTER=IPTVBoss"
if "%logtype%"=="2" set "FILTER=AdvEPGDummy"
if "%logtype%"=="3" set "FILTER=NoGUI"
if "%logtype%"=="4" set "FILTER="
echo.
for /f "delims=" %%A in ('dir /b /o-d "%LOG_PATH%\%FILTER%*.log" 2^>nul') do (
    set "LATEST_LOG=%%A"
    goto SHOW_LOG
)
echo No matching log files found.
if "%arg_mode%"=="true" exit /b 0
pause
goto MENU

:SHOW_LOG
echo Displaying last 50 lines of: %LATEST_LOG%
powershell -Command "Get-Content -Path '%LOG_PATH%\%LATEST_LOG%' -Tail 50"
if "%arg_mode%"=="true" exit /b 0
pause
goto MENU

:MOVE_BACKUPS
echo.
echo [1/7] Preparing Desktop backup folder...
if not exist "%BACKUP_DEST%\deleted" mkdir "%BACKUP_DEST%\deleted"
echo [2/7] Moving existing backups to Desktop\deleted...
move /Y "%BACKUP_SRC%\*.*" "%BACKUP_DEST%\deleted" >nul
echo.
if "%arg_mode%"=="false" (
    set /p confirm="Do you want to delete DB and clear folders (Y/N)? "
) else (
    set "confirm=Y"
)
if /I not "%confirm%"=="Y" (
    echo Skipping DB reset.
    if "%arg_mode%"=="true" exit /b 0
    pause
    goto MENU
)
echo [3/7] Deleting DB files from: %DB_PATH%...
del /f /q "%DB_PATH%\IPTVBoss.mv.db"      >nul 2>&1
del /f /q "%DB_PATH%\IPTVBoss.lock.db"    >nul 2>&1
echo [4/7] Cleaning folders: cache, emailtemplates, langs, temp...
del /f /q "%CACHE_PATH%\*.*"              >nul 2>&1
del /f /q "%IPTV_PATH%\emailtemplates\*.*">nul 2>&1
del /f /q "%IPTV_PATH%\langs\*.*"       >nul 2>&1
del /f /q "%TEMP_PATH%\*.*"              >nul 2>&1
echo [5/7] Copying Desktop backups back into %BACKUP_SRC%...
xcopy "%BACKUP_DEST%\*.*" "%BACKUP_SRC%\" /Y /Q >nul
echo [6/7] Cleaning up duplicate .db files from Desktop...
del /f /q "%BACKUP_DEST%\IPTVBoss.mv.db"      >nul 2>&1
del /f /q "%BACKUP_DEST%\IPTVBoss.lock.db"    >nul 2>&1
echo [7/7] Move and cleanup completed.
if "%arg_mode%"=="true" exit /b 0
pause
goto MENU

:CHECK_AV
echo.
echo Checking antivirus status...
wmic /namespace:\\root\SecurityCenter2 path AntiVirusProduct get displayName,productState
if "%arg_mode%"=="true" exit /b 0
pause
goto MENU

:CHECK_DEFENDER
echo.
echo Checking Windows Defender status...
powershell -Command "Get-MpComputerStatus | Select-Object -Property AMServiceEnabled,RealTimeProtectionEnabled,AntispywareEnabled"
if "%arg_mode%"=="true" exit /b 0
pause
goto MENU

:TOGGLE_DEFENDER
echo.
echo Current Defender real-time protection status:
powershell -Command "Get-MpComputerStatus | Select-Object -ExpandProperty RealTimeProtectionEnabled"
echo.
if "%arg_mode%"=="false" (
    set /p rtaction="Would you like to (D)isable or (E)nable real-time protection? [D/E]: "
) else (
    set "rtaction=D"
)
if /I "%rtaction%"=="D" (
    echo Disabling real-time protection...
    powershell -Command "Set-MpPreference -DisableRealtimeMonitoring $true"
    echo Defender real-time protection DISABLED.
) else if /I "%rtaction%"=="E" (
    echo Enabling real-time protection...
    powershell -Command "Set-MpPreference -DisableRealtimeMonitoring $false"
    echo Defender real-time protection ENABLED.
) else (
    echo Invalid selection. No action taken.
)
if "%arg_mode%"=="true" exit /b 0
pause
goto MENU

