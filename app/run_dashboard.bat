@echo off

REM Navigate to app directory
cd /d "%~dp0"

REM Check if virtual environment exists in parent directory
if exist "..\.mobilization" (
    echo Activating existing virtual environment...
    call ..\.mobilization\Scripts\activate
) else (
    echo Creating new virtual environment...
    python -m venv ..\.mobilization
    call ..\.mobilization\Scripts\activate
)

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Launch the dashboard
echo Launching Mobilization Eligibility Dashboard...
streamlit run mobilization_dashboard.py