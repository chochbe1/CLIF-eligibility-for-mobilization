@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM Step 0: Navigate to script directory (project root)
cd /d %~dp0

REM Step 1: Create virtual environment if it doesn't exist
if not exist ".mobilization\" (
    echo Creating virtual environment...
    python -m venv .mobilization
)

REM Step 2: Activate virtual environment
call .mobilization\Scripts\activate.bat

REM Step 3: Install dependencies
echo Installing Python dependencies...
pip install --quiet -r requirements.txt
pip install --quiet jupyter ipykernel papermill

REM Step 4: Register Jupyter kernel
python -m ipykernel install --user --name=.mobilization --display-name="Python (mobilization)"

REM Step 5: Set environment variables
set PYTHONWARNINGS=ignore
set PYTHONPATH=%cd%\code;%PYTHONPATH%

REM Step 6: Change to code directory
cd code

REM Step 7: Create logs directory if not exists
if not exist logs (
    mkdir logs
)

REM Step 8: Run Python notebooks and log outputs
echo Running 01_cohort_identification...
papermill 01_cohort_identification.ipynb nul > logs\01_cohort_identification.log 2>&1

echo Running 02_mobilization_analysis...
papermill 02_mobilization_analysis.ipynb nul > logs\02_mobilization_analysis.log 2>&1

REM Step 9: Run R script and log output
echo Running 03_competing_risk_analysis.R...
Rscript 03_competing_risk_analysis.R > logs\03_competing_risk_analysis.log 2>&1

echo ✅ All setup and analysis scripts completed!
