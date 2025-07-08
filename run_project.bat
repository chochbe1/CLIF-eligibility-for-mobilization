@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM Enhanced run_project.bat — Interactive CLIF project execution script (Windows)

REM ── Setup logging ──────────────────────────────────────────────────────────────
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,8%_%dt:~8,6%"
set "LOG_FILE=output\execution_log_%TIMESTAMP%.log"
if not exist "output" mkdir "output"

REM Initialize log file with header
echo CLIF Eligibility for Mobilization Analysis Pipeline - Execution Log > "%LOG_FILE%"
echo Started at: %date% %time% >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"

REM ── Go to script directory ──
cd /d %~dp0

REM ── ASCII Welcome Banner ───────────────────────────────────────────────────────
:show_banner
cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                                                                              ║
echo ║                              ██████ ██      ██ ███████                       ║
echo ║                             ██      ██      ██ ██                            ║
echo ║                             ██      ██      ██ █████                         ║
echo ║                             ██      ██      ██ ██                            ║
echo ║                              ██████ ███████ ██ ██                            ║
echo ║                                                                              ║
echo ║            ELIGIBILITY FOR MOBILIZATION ANALYSIS PROJECT                    ║
echo ║                                                                              ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.
echo Welcome to the CLIF Eligibility for Mobilization Analysis Pipeline!
echo This script will guide you through the complete analysis workflow.
echo.

REM ── Progress separator ─────────────────────────────────────────────────────────
:separator
echo ==================================================
goto :eof

REM ── Progress display function ──────────────────────────────────────────────────
:show_progress
echo.
call :separator
echo Step %~1/%~2: %~3
echo [%date% %time%] Starting: %~3
call :separator
goto :eof

REM ── Error handler ──────────────────────────────────────────────────────────────
:handle_error
echo.
echo ❌ ERROR OCCURRED!
echo Step failed: %~1
echo Exit code: %~2
echo.

REM Check for common errors
findstr /i "FileNotFoundError.*MIMIC-IV" "%LOG_FILE%" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo It looks like the MIMIC-IV data files are not found.
    echo Please ensure you have:
    echo 1. Downloaded the MIMIC-IV dataset
    echo 2. Updated config/config.json with the correct data path
    echo 3. Converted the data to CLIF format
    echo.
)

echo Check the log file for full details: %LOG_FILE%
echo.
exit /b %~2

REM ── Check and setup R environment ─────────────────────────────────────────────
:check_r_environment
call :show_progress 1 8 "Checking R Environment"

where Rscript >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ R found in PATH
    set "RSCRIPT_PATH=Rscript"
    goto :eof
)

echo ⚠️  R not found in PATH
echo.
echo Please choose an option:
echo 1) Provide path to R installation
echo 2) Run manually (script will skip R execution^)
echo 3) Exit and install R
echo.

:r_choice_loop
set /p "choice=Enter your choice (1-3): "
if "!choice!"=="1" (
    set /p "r_path=Enter path to Rscript.exe: "
    if exist "!r_path!" (
        set "RSCRIPT_PATH=!r_path!"
        echo ✅ R path accepted: !r_path!
        goto :eof
    ) else (
        echo ❌ Invalid path or file not found
        goto :r_choice_loop
    )
) else if "!choice!"=="2" (
    set "RSCRIPT_PATH="
    echo ⚠️  R execution will be skipped
    goto :eof
) else if "!choice!"=="3" (
    echo Please install R and try again
    exit /b 0
) else (
    echo Invalid choice. Please enter 1, 2, or 3
    goto :r_choice_loop
)

REM ── Main execution flow ────────────────────────────────────────────────────────
call :show_banner

REM Check R environment first
call :check_r_environment

REM Step 2: Create virtual environment
call :show_progress 2 8 "Create Virtual Environment"
if not exist ".mobilization\" (
    echo Creating virtual environment...
    python -m venv .mobilization 2>&1 | tee -a "%LOG_FILE%"
    if %ERRORLEVEL% NEQ 0 call :handle_error "Create Virtual Environment" %ERRORLEVEL%
) else (
    echo Virtual environment already exists.
    echo Virtual environment already exists. >> "%LOG_FILE%"
)
echo ✅ Completed: Create Virtual Environment

REM Step 3: Activate virtual environment
call :show_progress 3 8 "Activate Virtual Environment"
echo Activating virtual environment...
echo Activating virtual environment... >> "%LOG_FILE%"
call .mobilization\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 call :handle_error "Activate Virtual Environment" %ERRORLEVEL%
echo ✅ Completed: Activate Virtual Environment

REM Step 4: Install dependencies
call :show_progress 4 8 "Install Dependencies"
echo Upgrading pip...
python -m pip install --upgrade pip 2>&1 | tee -a "%LOG_FILE%"
if %ERRORLEVEL% NEQ 0 call :handle_error "Install Dependencies" %ERRORLEVEL%

echo Installing dependencies...
pip install -r requirements.txt 2>&1 | tee -a "%LOG_FILE%"
if %ERRORLEVEL% NEQ 0 call :handle_error "Install Dependencies" %ERRORLEVEL%

pip install jupyter ipykernel 2>&1 | tee -a "%LOG_FILE%"
if %ERRORLEVEL% NEQ 0 call :handle_error "Install Dependencies" %ERRORLEVEL%
echo ✅ Completed: Install Dependencies

REM Step 5: Register Jupyter kernel
call :show_progress 5 8 "Register Jupyter Kernel"
echo Registering Jupyter kernel...
python -m ipykernel install --user --name=.mobilization --display-name="Python (mobilization)" 2>&1 | tee -a "%LOG_FILE%"
if %ERRORLEVEL% NEQ 0 call :handle_error "Register Jupyter Kernel" %ERRORLEVEL%
echo ✅ Completed: Register Jupyter Kernel

REM Step 6: Setup working directory and validate data
call :show_progress 6 8 "Setup Working Directory & Validate Data"
echo Changing to code directory...
cd code
if %ERRORLEVEL% NEQ 0 call :handle_error "Setup Working Directory" %ERRORLEVEL%

if not exist logs mkdir logs

REM Check if data path exists (basic check for Windows)
echo Checking data configuration...
if exist "..\config\config.json" (
    echo Config file found, proceeding with analysis...
) else (
    echo ⚠️  Config file not found: ..\config\config.json
)

echo ✅ Completed: Setup Working Directory

REM Step 7: Execute notebooks
call :show_progress 7 8 "Execute Analysis Notebooks"

echo Executing 01_cohort_identification.ipynb...
REM Use jupyter nbconvert with unbuffered output
jupyter nbconvert --to script --stdout --log-level ERROR 01_cohort_identification.ipynb 2>nul | python -u 2>&1 | tee logs\01_cohort_identification.log | tee -a "%LOG_FILE%"
if %ERRORLEVEL% NEQ 0 call :handle_error "Execute 01_cohort_identification.ipynb" %ERRORLEVEL%
echo ✅ Completed: 01_cohort_identification.ipynb

echo.
echo Executing 02_mobilization_analysis.ipynb...
jupyter nbconvert --to script --stdout --log-level ERROR 02_mobilization_analysis.ipynb 2>nul | python -u 2>&1 | tee logs\02_mobilization_analysis.log | tee -a "%LOG_FILE%"
if %ERRORLEVEL% NEQ 0 call :handle_error "Execute 02_mobilization_analysis.ipynb" %ERRORLEVEL%
echo ✅ Completed: 02_mobilization_analysis.ipynb

REM Step 8: Run R script
call :show_progress 8 8 "Execute R Analysis"
if defined RSCRIPT_PATH (
    echo Running R script: 03_competing_risk_analysis.R...
    "%RSCRIPT_PATH%" 03_competing_risk_analysis.R 2>&1 | tee logs\03_competing_risk_analysis.log | tee -a "%LOG_FILE%"
    if %ERRORLEVEL% NEQ 0 call :handle_error "Execute R Analysis" %ERRORLEVEL%
    echo ✅ Completed: R Analysis
) else (
    echo ⚠️  R script execution skipped. Please run manually:
    echo    cd code && Rscript 03_competing_risk_analysis.R
)

REM Success message
call :separator
echo 🎉 SUCCESS! All analysis steps completed successfully!
echo 📊 Results saved to: output\
echo 📝 Full log saved to: %LOG_FILE%
call :separator

REM Dashboard option
echo.
echo Would you like to launch the visualization dashboard?
echo The dashboard provides interactive patient-level analysis
echo.

:dashboard_choice
set /p "dashboard_choice=Launch dashboard? (y/n): "
if /i "!dashboard_choice!"=="y" (
    echo 🚀 Starting dashboard...
    cd ..\app
    streamlit run mobilization_dashboard.py
    goto :dashboard_done
) else if /i "!dashboard_choice!"=="n" (
    echo Dashboard launch skipped. You can run it later with:
    echo    cd app && streamlit run mobilization_dashboard.py
    goto :dashboard_done
) else (
    echo Please answer y or n
    goto :dashboard_choice
)

:dashboard_done
echo.
echo Thank you for using the CLIF Eligibility for Mobilization Analysis Pipeline!
pause
exit /b 0