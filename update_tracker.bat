@echo off
echo ============================================
echo  Phillies $97.7M Tracker - Auto Update
echo ============================================
echo.

:: Set working directory
cd /d C:\Users\jlynn\Data_Projects\phillies-tracker

:: Run fetch_stats.py
echo Fetching latest stats from Baseball Savant...
C:\Python313\python.exe fetch_stats.py
echo.

:: Check if fetch was successful
if %errorlevel% neq 0 (
    echo ERROR: fetch_stats.py failed! Aborting push.
    pause
    exit /b 1
)

:: Push updated CSVs to GitHub
echo Pushing updated CSVs to GitHub...
"C:\Program Files\Git\bin\git.exe" add data/game_log.csv data/team_record.csv
"C:\Program Files\Git\bin\git.exe" commit -m "Auto update stats %date%"
"C:\Program Files\Git\bin\git.exe" push origin main
echo.

if %errorlevel% neq 0 (
    echo ERROR: Git push failed!
    pause
    exit /b 1
)

echo ============================================
echo  Done! Streamlit app will update shortly.
echo ============================================
pause
