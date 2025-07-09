@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM ── Step 0: Go to script directory ──
cd /d %~dp0

REM ── Step 1: Check and setup R environment ──
where Rscript >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] R found in PATH
    set "RSCRIPT_PATH=Rscript"
    goto :create_venv
)

echo [WARNING] R not found in PATH
echo.
echo Please choose an option:
echo 1) Provide path to R installation
echo 2) Run manually (script will skip R execution)
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
        goto :create_venv
    ) else (
        echo [ERROR] Invalid path or file not found
        goto :r_choice_loop
    )
) else if "!choice!"=="2" (
    set "RSCRIPT_PATH="
    echo [WARNING] R execution will be skipped
    goto :create_venv
) else if "!choice!"=="3" (
    echo Please install R and try again
    exit /b 0
) else (
    echo Invalid choice. Please enter 1, 2, or 3
    goto :r_choice_loop
)

:create_venv
REM ── Step 2: Create virtual environment if missing ──
if not exist ".mobilization\" (
    echo Creating virtual environment...
    python -m venv .mobilization
) else (
    echo Virtual environment already exists.
)

REM ── Step 3: Activate virtual environment ──
call .mobilization\Scripts\activate.bat

REM ── Step 4: Install required packages ──
echo Installing dependencies...
pip install --quiet -r requirements.txt
pip install --quiet jupyter ipykernel papermill

REM ── Step 5: Register kernel ──
python -m ipykernel install --user --name=.mobilization --display-name="Python (mobilization)"

REM ── Step 6: Set environment variables ──
set PYTHONWARNINGS=ignore
set PYTHONPATH=%cd%\code;%PYTHONPATH%

REM ── Step 7: Change to code directory ──
cd code

REM ── Step 8: Create logs folder ──
if not exist logs (
    mkdir logs
)

REM ── Step 9: Run analysis notebooks using papermill ──
echo.
echo Running 01_cohort_identification.ipynb ...
papermill 01_cohort_identification.ipynb 01_cohort_identification.ipynb > logs\01_cohort_identification.log
echo Finished 01_cohort_identification.ipynb

echo.
echo Running 02_mobilization_analysis.ipynb ...
papermill 02_mobilization_analysis.ipynb 02_mobilization_analysis.ipynb > logs\02_mobilization_analysis.log
echo Finished 02_mobilization_analysis.ipynb

REM ── Step 10: Run R script ──
echo.
echo Running R script: 03_competing_risk_analysis.R ...

if defined RSCRIPT_PATH (
    "%RSCRIPT_PATH%" 03_competing_risk_analysis.R > logs\03_competing_risk_analysis.log
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Error running R script. Check logs\03_competing_risk_analysis.log for details.
        exit /b 1
    )
) else (
    echo [WARNING] R script execution skipped. Please run manually:
    echo    cd code && Rscript 03_competing_risk_analysis.R
)

REM ── Step 11: Done ──
echo.
echo ✅ All steps completed successfully! You can launch the dashboard from the app directory.
pause

REM ── Step 12: Ask to launch dashboard ──
echo.
echo Would you like to launch the visualization dashboard?
echo The dashboard provides interactive patient-level analysis.
echo.

:launch_dashboard_prompt
set /p "launch_dash=Launch dashboard? (y/n): "
if /I "!launch_dash!"=="Y" (
    echo 🚀 Starting dashboard...
    cd ..\app
    streamlit run mobilization_dashboard.py
) else if /I "!launch_dash!"=="N" (
    echo Dashboard launch skipped. You can run it later with:
    echo    cd app && streamlit run mobilization_dashboard.py
) else (
    echo Please enter Y or N.
    goto :launch_dashboard_prompt
)

exit /b 0