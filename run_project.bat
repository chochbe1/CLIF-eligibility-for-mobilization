@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM Enhanced run_project.bat — Interactive CLIF project execution script (Windows)

REM ── Setup logging ──────────────────────────────────────────────────────────────
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,8%_%dt:~8,6%"
set "LOG_FILE=logs\execution_log_%TIMESTAMP%.log"
if not exist "logs" mkdir "logs"

REM Initialize log file with header
echo CLIF Eligibility for Mobilization Analysis Pipeline - Execution Log > "%LOG_FILE%"
echo Started at: %date% %time% >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"

REM ── Go to script directory ──
cd /d %~dp0

REM Jump to main execution
goto main

:show_banner
cls
echo.
echo ===============================================================================
echo                                                                               
echo                               CLIF                                 
echo                                                                               
echo                 ELIGIBILITY FOR MOBILIZATION PROJECT                    
echo                                                                               
echo ===============================================================================
echo.
echo Welcome to the CLIF Eligibility for Mobilization Analysis Pipeline!
echo.

REM ── Progress separator ─────────────────────────────────────────────────────────
:separator
echo ==================================================
echo ================================================== >> "%LOG_FILE%"
goto :eof

REM ── Progress display function ──────────────────────────────────────────────────
:show_progress
echo.
echo. >> "%LOG_FILE%"
call :separator
echo Step %~1/%~2: %~3
echo Step %~1/%~2: %~3 >> "%LOG_FILE%"
echo [%date% %time%] Starting: %~3
echo [%date% %time%] Starting: %~3 >> "%LOG_FILE%"
call :separator
goto :eof

REM ── Error handler ──────────────────────────────────────────────────────────────
:handle_error
echo.
echo [ERROR] ERROR OCCURRED!
echo Step failed: %~1
echo Exit code: %~2
echo.


echo Check the log file for full details: %LOG_FILE%
echo.
exit /b %~2

REM ── Check and setup R environment ─────────────────────────────────────────────
:check_r_environment
call :show_progress 1 8 "Checking R Environment"

where Rscript >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] R found in PATH
    set "RSCRIPT_PATH=Rscript"
    goto :eof
)

echo [WARNING] R not found in PATH
echo.
echo Please choose an option:
echo 1) Provide path to R installation
echo 2) Run manually (script will skip R execution^)
echo 3) Exit and install R
echo.

:r_choice_loop
set /p "choice=Enter your choice (1-3): "
if "!choice!"=="1" (
    echo Examples:
    echo   Windows: C:\Program Files\R\R-4.3.0\bin\Rscript.exe
    echo   Windows: C:\Program Files\R\R-4.4.0\bin\Rscript.exe
    echo.
    set /p "r_path=Enter path to Rscript.exe: "
    if exist "!r_path!" (
        set "RSCRIPT_PATH=!r_path!"
        echo [OK] R path accepted: !r_path!
        goto :eof
    ) else (
        echo [ERROR] Invalid path or file not found
        goto :r_choice_loop
    )
) else if "!choice!"=="2" (
    set "RSCRIPT_PATH="
    echo [WARNING] R execution will be skipped
    goto :eof
) else if "!choice!"=="3" (
    echo Please install R and try again
    exit /b 0
) else (
    echo Invalid choice. Please enter 1, 2, or 3
    goto :r_choice_loop
)

REM ── Main execution flow ────────────────────────────────────────────────────────
:main
call :show_banner

REM Check R environment first
call :check_r_environment

REM Step 2: Create virtual environment
call :show_progress 2 8 "Create Virtual Environment"
if not exist ".mobilization\" (
    echo Creating virtual environment...
    python -m venv .mobilization > temp.log 2>&1
    type temp.log
    type temp.log >> "%LOG_FILE%"
    del temp.log
    if %ERRORLEVEL% NEQ 0 call :handle_error "Create Virtual Environment" %ERRORLEVEL%
) else (
    echo Virtual environment already exists.
    echo Virtual environment already exists. >> "%LOG_FILE%"
)
echo [OK] Completed: Create Virtual Environment

REM Step 3: Activate virtual environment
call :show_progress 3 8 "Activate Virtual Environment"
echo Activating virtual environment...
echo Activating virtual environment... >> "%LOG_FILE%"
call .mobilization\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 call :handle_error "Activate Virtual Environment" %ERRORLEVEL%
echo [OK] Completed: Activate Virtual Environment

REM Step 4: Install dependencies
call :show_progress 4 8 "Install Dependencies"
echo Upgrading pip...
python -m pip install --upgrade pip > temp.log 2>&1
type temp.log
type temp.log >> "%LOG_FILE%"
del temp.log
if %ERRORLEVEL% NEQ 0 call :handle_error "Install Dependencies" %ERRORLEVEL%

echo Installing dependencies...
pip install -r requirements.txt > temp.log 2>&1
type temp.log
type temp.log >> "%LOG_FILE%"
del temp.log
if %ERRORLEVEL% NEQ 0 call :handle_error "Install Dependencies" %ERRORLEVEL%

pip install jupyter ipykernel > temp.log 2>&1
type temp.log
type temp.log >> "%LOG_FILE%"
del temp.log
if %ERRORLEVEL% NEQ 0 call :handle_error "Install Dependencies" %ERRORLEVEL%
echo [OK] Completed: Install Dependencies

REM Step 5: Register Jupyter kernel
call :show_progress 5 8 "Register Jupyter Kernel"
echo Registering Jupyter kernel...
python -m ipykernel install --user --name=.mobilization --display-name="Python (mobilization)" > temp.log 2>&1
type temp.log
type temp.log >> "%LOG_FILE%"
del temp.log
if %ERRORLEVEL% NEQ 0 call :handle_error "Register Jupyter Kernel" %ERRORLEVEL%
echo [OK] Completed: Register Jupyter Kernel

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
    echo [WARNING] Config file not found: ..\config\config.json
)

echo [OK] Completed: Setup Working Directory

REM Step 7: Execute notebooks
call :show_progress 7 8 "Execute Analysis Notebooks"

echo Executing 01_cohort_identification.ipynb...
echo Executing 01_cohort_identification.ipynb... >> "%LOG_FILE%"
REM Use jupyter nbconvert with output redirection for Windows
jupyter nbconvert --to script --stdout --log-level ERROR 01_cohort_identification.ipynb 2>nul | python -u > logs\01_cohort_identification.log 2>&1
type logs\01_cohort_identification.log
type logs\01_cohort_identification.log >> "%LOG_FILE%"
if %ERRORLEVEL% NEQ 0 call :handle_error "Execute 01_cohort_identification.ipynb" %ERRORLEVEL%
echo [OK] Completed: 01_cohort_identification.ipynb
echo [OK] Completed: 01_cohort_identification.ipynb >> "%LOG_FILE%"

echo.
echo Executing 02_mobilization_analysis.ipynb...
echo Executing 02_mobilization_analysis.ipynb... >> "%LOG_FILE%"
jupyter nbconvert --to script --stdout --log-level ERROR 02_mobilization_analysis.ipynb 2>nul | python -u > logs\02_mobilization_analysis.log 2>&1
type logs\02_mobilization_analysis.log
type logs\02_mobilization_analysis.log >> "%LOG_FILE%"
if %ERRORLEVEL% NEQ 0 call :handle_error "Execute 02_mobilization_analysis.ipynb" %ERRORLEVEL%
echo [OK] Completed: 02_mobilization_analysis.ipynb
echo [OK] Completed: 02_mobilization_analysis.ipynb >> "%LOG_FILE%"

REM Step 8: Run R script
call :show_progress 8 8 "Execute R Analysis"
if defined RSCRIPT_PATH (
    echo Running R script: 03_competing_risk_analysis.R...
    echo Running R script: 03_competing_risk_analysis.R... >> "%LOG_FILE%"
    "%RSCRIPT_PATH%" 03_competing_risk_analysis.R > logs\03_competing_risk_analysis.log 2>&1
    type logs\03_competing_risk_analysis.log
    type logs\03_competing_risk_analysis.log >> "%LOG_FILE%"
    if %ERRORLEVEL% NEQ 0 call :handle_error "Execute R Analysis" %ERRORLEVEL%
    echo [OK] Completed: R Analysis
    echo [OK] Completed: R Analysis >> "%LOG_FILE%"
) else (
    echo [WARNING] R script execution skipped. Please run manually:
    echo    cd code && Rscript 03_competing_risk_analysis.R
)

REM Success message
call :separator
echo [SUCCESS] All analysis steps completed successfully!
echo Results saved to: output\
echo Full log saved to: %LOG_FILE%
call :separator

REM Dashboard option
echo.
echo Would you like to launch the visualization dashboard?
echo The dashboard provides interactive patient-level analysis
echo.

:dashboard_choice
set /p "dashboard_choice=Launch dashboard? (y/n): "
if /i "!dashboard_choice!"=="y" (
    echo Starting dashboard...
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