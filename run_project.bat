@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:: ── Colors (Only for aesthetics in some terminals) ──
set "YELLOW====="
set "CYAN=>>>>>>"
set "GREEN=++++++"

:: ── Function: separator ──
call :separator

:: ── 1. Create virtual environment ──
if not exist ".mobilization\" (
    echo %CYAN% Creating virtual environment (.mobilization)...
    python -m venv .mobilization
) else (
    echo %CYAN% Virtual environment already exists.
)

:: ── 2. Activate virtual environment ──
call :separator
echo %CYAN% Activating virtual environment...
call .mobilization\Scripts\activate.bat

:: ── 3. Upgrade pip ──
call :separator
echo %CYAN% Upgrading pip...
python -m pip install --upgrade pip

:: ── 4. Install dependencies ──
call :separator
echo %CYAN% Installing dependencies...
pip install --quiet -r requirements.txt
pip install --quiet jupyter ipykernel

:: ── 5. Register Jupyter kernel ──
call :separator
echo %CYAN% Registering Jupyter kernel...
python -m ipykernel install --user --name=.mobilization --display-name="Python (mobilization)"

:: ── 6. Change to code directory ──
call :separator
echo %CYAN% Changing to code directory...
cd code
if errorlevel 1 (
    echo ❌ 'code' directory not found.
    exit /b 1
)

:: ── 7. Convert and execute notebooks, streaming + logging ──
if not exist logs (
    mkdir logs
)

set NOTEBOOKS=01_cohort_identification.ipynb 02_mobilization_analysis.ipynb

for %%N in (%NOTEBOOKS%) do (
    call :separator
    set "NB=%%N"
    set "BASE=%%~nN"
    set "LOG=logs\!BASE!.log"
    echo %CYAN% Executing %%N and logging output to !LOG!...
    set MPLBACKEND=Agg
    jupyter nbconvert --to script --stdout "%%N" | python > "!LOG!" 2>&1
)

:: ── 8. Run R script ──
call :separator
echo %CYAN% Running R script: 03_competing_risk_analysis.R...
Rscript 03_competing_risk_analysis.R > logs\03_competing_risk_analysis.log 2>&1

:: ── 9. Done ──
call :separator
echo %GREEN% ✅ All setup and analysis scripts completed successfully!

pause
exit /b 0

:: ── Function: separator ──
:separator
echo ==================================================
exit /b
