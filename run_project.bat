@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM run_project.bat — Interactive CLIF project execution script (Windows)

REM ── Setup logging ──────────────────────────────────────────────────────────────
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,8%_%dt:~8,6%"
set "SCRIPT_DIR=%~dp0"
set "LOG_FILE=%SCRIPT_DIR%logs\execution_log_%TIMESTAMP%.log"
if not exist "%SCRIPT_DIR%logs" mkdir "%SCRIPT_DIR%logs"

REM Initialize log file with header
echo CLIF Eligibility for Mobilization Project - Execution Log > "%LOG_FILE%"
echo Started at: %date% %time% >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"

REM Initialize failed steps tracking
set "FAILED_STEPS="
set "FAILED_COUNT=0"

REM Export environment variables for unbuffered output
set PYTHONUNBUFFERED=1
set MPLBACKEND=Agg

REM ── Go to script directory ──
cd /d %~dp0

REM Jump to main execution
goto main

REM ── Function to log and display ──────────────────────────────────────────────
:log_echo
echo %~1
echo %~1 >> "%LOG_FILE%"
goto :eof

:show_banner
cls
call :log_echo " "
call :log_echo "==============================================================================="
call :log_echo "                                                                               "
call :log_echo "                               CLIF                                            "
call :log_echo "                                                                               "
call :log_echo "                 ELIGIBILITY FOR MOBILIZATION PROJECT                          "
call :log_echo "                                                                               "
call :log_echo "==============================================================================="
call :log_echo " "
call :log_echo "Welcome to the CLIF Eligibility for Mobilization Project!"
call :log_echo " "
goto :eof

REM ── Progress separator ─────────────────────────────────────────────────────────
:separator
call :log_echo "=================================================="
goto :eof

REM ── Progress display function ──────────────────────────────────────────────────
:show_progress
call :separator
call :log_echo "Step %~1/%~2: %~3"
call :log_echo "[%date% %time%] Starting: %~3"
call :separator
goto :eof

REM ── Error handler - CONTINUES execution like Unix version ────────────────────
:handle_error
set "exit_code=%ERRORLEVEL%"
set "step_name=%~1"

call :log_echo " "
call :log_echo "[ERROR] ERROR OCCURRED!"
call :log_echo "Step failed: %step_name%"
call :log_echo "Exit code: %exit_code%"
call :log_echo "Check the log file for full details: %LOG_FILE%"
call :log_echo "Continuing with next step..."
call :log_echo " "

REM Add to failed steps list
set "FAILED_STEPS=%FAILED_STEPS%,%step_name%"
set /a FAILED_COUNT+=1

REM Return 0 to continue execution (like Unix version)
exit /b 0

REM ── Execute notebook with output capture ─────────────────────────────────────
:execute_notebook
set "notebook_name=%~1"
set "log_name=%~2"

call :log_echo "Executing %notebook_name%..."
call :log_echo "Converting and executing notebook..."

REM Run Jupyter nbconvert and pipe to Python directly
jupyter nbconvert --to script --stdout --log-level ERROR %notebook_name% 2>nul | python -u > "..\logs\%log_name%" 2>&1
set "exec_result=!ERRORLEVEL!"

REM Display the output to console while it's already saved to log
type "..\logs\%log_name%"

REM Check result and handle error if needed
if %exec_result% NEQ 0 (
    call :handle_error "Execute %notebook_name%"
    call :log_echo "[FAILED] %notebook_name%"
) else (
    call :log_echo "[OK] Completed: %notebook_name%"
)
goto :eof

REM ── Check and setup R environment ─────────────────────────────────────────────
:check_r_environment
call :show_progress 1 8 "Checking R Environment"

where Rscript >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    call :log_echo "[OK] R found in PATH"
    set "RSCRIPT_PATH=Rscript"
    goto :eof
)

call :log_echo "[WARNING] R not found in PATH"
call :log_echo " "
call :log_echo "Please choose an option:"
call :log_echo "1) Provide path to R installation"
call :log_echo "2) Run manually (script will skip R execution)"
call :log_echo "3) Exit and install R"
call :log_echo " "

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
        call :log_echo "[OK] R path accepted: !r_path!"
        goto :eof
    ) else (
        call :log_echo "[ERROR] Invalid path or file not found"
        goto :r_choice_loop
    )
) else if "!choice!"=="2" (
    set "RSCRIPT_PATH="
    call :log_echo "[WARNING] R execution will be skipped"
    goto :eof
) else if "!choice!"=="3" (
    call :log_echo "Please install R and try again"
    exit /b 0
) else (
    call :log_echo "Invalid choice. Please enter 1, 2, or 3"
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
    call :log_echo "Creating virtual environment (.mobilization)..."
    python -m venv .mobilization 2>&1
    if !ERRORLEVEL! NEQ 0 (
        call :handle_error "Create Virtual Environment"
    )
) else (
    call :log_echo "Virtual environment already exists."
)
call :log_echo "[OK] Completed: Create Virtual Environment"

REM Step 3: Activate virtual environment
call :show_progress 3 8 "Activate Virtual Environment"
call :log_echo "Activating virtual environment..."
call .mobilization\Scripts\activate.bat
if !ERRORLEVEL! NEQ 0 (
    call :handle_error "Activate Virtual Environment"
)
call :log_echo "[OK] Completed: Activate Virtual Environment"

REM Step 4: Install dependencies
call :show_progress 4 8 "Install Dependencies"
call :log_echo "Upgrading pip..."
python -m pip install --upgrade pip
if !ERRORLEVEL! NEQ 0 (
    call :handle_error "Upgrade pip"
)

call :log_echo "Installing dependencies..."
pip install -r requirements.txt
if !ERRORLEVEL! NEQ 0 (
    call :handle_error "Install requirements"
)

pip install jupyter ipykernel
if !ERRORLEVEL! NEQ 0 (
    call :handle_error "Install jupyter"
)
call :log_echo "[OK] Completed: Install Dependencies"

REM Step 5: Register Jupyter kernel
call :show_progress 5 8 "Register Jupyter Kernel"
call :log_echo "Registering Jupyter kernel..."
python -m ipykernel install --user --name=.mobilization --display-name="Python (mobilization)"
if !ERRORLEVEL! NEQ 0 (
    call :handle_error "Register Jupyter Kernel"
)
call :log_echo "[OK] Completed: Register Jupyter Kernel"

REM Step 6: Setup working directory and validate data
call :show_progress 6 8 "Setup Working Directory & Validate Data"
call :log_echo "Changing to code directory..."
cd code
if !ERRORLEVEL! NEQ 0 (
    call :handle_error "Change to code directory"
)

REM Check if data path exists
call :log_echo "Checking data configuration..."
if exist "..\config\config.json" (
    REM Try to read data path from config
    for /f "usebackq tokens=*" %%a in (`python -c "import json; print(json.load(open('../config/config.json'))['tables_path'])" 2^>nul`) do set "DATA_PATH=%%a"
    if defined DATA_PATH (
        if exist "!DATA_PATH!" (
            call :log_echo "[OK] Data path found: !DATA_PATH!"
        ) else (
            call :log_echo "[WARNING] Data path not found: !DATA_PATH!"
            call :log_echo "Please ensure the MIMIC-IV data is available at this location"
            call :log_echo "Or update config\config.json with the correct path"
            call :log_echo " "
            set /p "continue_choice=Continue anyway? (y/n): "
            if /i not "!continue_choice!"=="y" (
                call :log_echo "Exiting. Please set up the data path and try again."
                exit /b 0
            )
        )
    )
) else (
    call :log_echo "[WARNING] Config file not found: ..\config\config.json"
)

call :log_echo "[OK] Completed: Setup Working Directory"

REM Step 7: Execute notebooks
call :show_progress 7 8 "Execute Analysis Notebooks"

call :execute_notebook "01_cohort_identification.ipynb" "01_cohort_identification.log"

call :log_echo " "
call :execute_notebook "02_mobilization_analysis.ipynb" "02_mobilization_analysis.log"

REM Step 8: Run R script
call :show_progress 8 8 "Execute R Analysis"
if defined RSCRIPT_PATH (
    call :log_echo "Running R script: 03_competing_risk_analysis.R..."
    "%RSCRIPT_PATH%" 03_competing_risk_analysis.R > "..\logs\03_competing_risk_analysis.log" 2>&1
    set "r_result=!ERRORLEVEL!"
    
    REM Display R output
    type "..\logs\03_competing_risk_analysis.log"
    
    if !r_result! NEQ 0 (
        call :handle_error "Execute R Analysis"
        call :log_echo "[FAILED] R Analysis"
    ) else (
        call :log_echo "[OK] Completed: R Analysis"
    )
) else (
    call :log_echo "[WARNING] R script execution skipped. Please run manually:"
    call :log_echo "   cd code && Rscript 03_competing_risk_analysis.R"
)

REM Final summary (matching Unix version)
call :separator
call :log_echo "EXECUTION SUMMARY"
call :separator

REM Display success/failure summary
if %FAILED_COUNT% EQU 0 (
    call :log_echo "[SUCCESS] All analysis steps completed successfully!"
) else (
    call :log_echo "[WARNING] PARTIAL SUCCESS: Some steps failed"
    call :log_echo " "
    call :log_echo "Failed steps:"
    
    REM Parse and display failed steps
    for %%a in (%FAILED_STEPS%) do (
        if not "%%a"=="" call :log_echo "  [X] %%a"
    )
    
    call :log_echo " "
    call :log_echo "Please check the individual log files for error details"
)

call :log_echo " "
call :log_echo "Results saved to: output\"
call :log_echo "Full log saved to: %LOG_FILE%"
call :log_echo "Individual logs in: logs\"
call :separator

REM Dashboard option
call :log_echo " "
call :log_echo "Would you like to launch the visualization dashboard?"
call :log_echo "The dashboard provides interactive patient-level analysis"
call :log_echo " "

:dashboard_choice
set /p "dashboard_choice=Launch dashboard? (y/n): "
if /i "!dashboard_choice!"=="y" (
    call :log_echo "Starting dashboard..."
    cd ..\app
    streamlit run mobilization_dashboard.py
    goto :dashboard_done
) else if /i "!dashboard_choice!"=="n" (
    call :log_echo "Dashboard launch skipped. You can run it later with:"
    call :log_echo "   cd app && streamlit run mobilization_dashboard.py"
    goto :dashboard_done
) else (
    call :log_echo "Please answer y or n"
    goto :dashboard_choice
)

:dashboard_done
call :log_echo " "
call :log_echo "Thank you for running the CLIF Eligibility for Mobilization Project!"
pause
exit /b 0