@echo off
REM FPL Complete Analysis - Run everything with one command!
REM הרץ הכל בפקודה אחת ל-Windows

setlocal enabledelayedexpansion

REM Get the script directory
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

echo ==================================
echo FPL Complete Analysis
echo ==================================
echo.

REM Check if league ID is provided
if "%1"=="" (
    echo Error: Please provide league ID
    echo.
    echo Usage: scripts\run_all.bat LEAGUE_ID [optional: "your name"]
    echo Example: scripts\run_all.bat 922765
    echo Example: scripts\run_all.bat 922765 "Sagi Cohen"
    echo.
    echo To find your league ID:
    echo 1. Go to fantasy.premierleague.com
    echo 2. Click on your league
    echo 3. Look at URL: .../leagues/922765/standings/c
    echo 4. The number ^(922765^) is your league ID
    pause
    exit /b 1
)

set LEAGUE_ID=%1
set YOUR_NAME=%~2

echo League ID: %LEAGUE_ID%
if not "%YOUR_NAME%"=="" (
    echo Analyzing for: %YOUR_NAME%
)
echo.

REM Change to project root
cd /d "%PROJECT_ROOT%"

REM Step 1: Collect data
echo ==================================
echo Step 1/6: Collecting data...
echo ==================================
python src/fpl_data_collector.py %LEAGUE_ID%
if errorlevel 1 (
    echo Failed to collect data
    pause
    exit /b 1
)
echo Data collected successfully!
echo.

REM Step 2: Basic analysis
echo ==================================
echo Step 2/6: Basic Analysis
echo ==================================
python src/analyze_data.py
echo.

REM Step 3: Weekly Report
echo ==================================
echo Step 3/6: Weekly League Report
echo ==================================
python src/weekly_report.py
echo.

REM Step 4: Gold mine analysis
echo ==================================
echo Step 4/6: Gold Mine Analysis
echo ==================================
python src/gold_mine_analysis.py
echo.

REM Step 5: Transfer recommendations
echo ==================================
echo Step 5/6: Transfer Recommendations
echo ==================================
if not "%YOUR_NAME%"=="" (
    python src/transfer_recommendations.py "%YOUR_NAME%"
) else (
    python src/transfer_recommendations.py
)
echo.

REM Step 6: Captain selection
echo ==================================
echo Step 6/6: Captain Selection
echo ==================================
if not "%YOUR_NAME%"=="" (
    python src/captain_selector.py "%YOUR_NAME%"
) else (
    python src/captain_selector.py
)
echo.

REM Step 7: WhatsApp Summary
echo ==================================
echo Bonus: WhatsApp Summary (Hebrew)
echo ==================================
python src/whatsapp_summary.py
echo.

REM Final message
echo ==================================
echo ANALYSIS COMPLETE!
echo ==================================
echo.
echo You now have complete insights!
echo Reports saved in: fpl_data\reports\
echo.
echo Next steps:
echo    - Review differential players
echo    - Check transfer recommendations
echo    - Choose your captain
echo    - Share the WhatsApp summary!
echo    - WIN your league!
echo.
pause
