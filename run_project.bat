@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM ── Step 0: Go to script directory ──
cd /d %~dp0

REM ── Step 1: Create virtual environment if missing ──
if not exist ".mobilization\" (
    echo Creating virtual environment...
    python -m venv .mobilization
) else (
    echo Virtual environment already exists.
)

REM ── Step 2: Activate virtual environment ──
call .mobilization\Scripts\activate.bat

REM ── Step 3: Install required packages ──
echo Installing dependencies...
pip install --quiet -r requirements.txt
pip install --quiet jupyter ipykernel papermill

REM ── Step 4: Register kernel ──
python -m ipykernel install --user --name=.mobilization --display-name="Python (mobilization)"

REM ── Step 5: Set environment variables ──
set PYTHONWARNINGS=ignore
set PYTHONPATH=%cd%\code;%PYTHONPATH%

REM ── Step 6: Change to code directory ──
cd code

REM ── Step 7: Create logs folder ──
if not exist logs (
    mkdir logs
)

REM ── Step 8: Run analysis notebooks using papermill ──
echo.
echo Running 01_cohort_identification.ipynb ...
papermill 01_cohort_identification.ipynb 01_cohort_identification.ipynb > logs\01_cohort_identification.log
echo Finished 01_cohort_identification.ipynb

echo.
echo Running 02_mobilization_analysis.ipynb ...
papermill 02_mobilization_analysis.ipynb 02_mobilization_analysis.ipynb > logs\02_mobilization_analysis.log
echo Finished 02_mobilization_analysis.ipynb

REM ── Step 9: Run R script ──
echo.
echo Running R script: 03_competing_risk_analysis.R ...

where Rscript >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Rscript not found. Please ensure R is installed and added to your PATH.
    echo Exiting script.
    exit /b 1
)

Rscript 03_competing_risk_analysis.R > logs\03_competing_risk_analysis.log
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Error running R script. Check logs\03_competing_risk_analysis.log for details.
    exit /b 1
)

REM ── Step 10: Done ──
echo.
echo ✅ All steps completed successfully!
pause
exit /b
