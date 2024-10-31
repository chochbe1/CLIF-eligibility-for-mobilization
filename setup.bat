@echo off
REM setup.bat

REM Create a virtual environment named .mobilization
python -m venv .mobilization

REM Activate the virtual environment
call .\.mobilization\Scripts\activate.bat

REM Upgrade pip to the latest version
python -m pip install --upgrade pip

REM Install packages from requirements.txt
pip install -r requirements.txt

REM Install Jupyter and IPykernel
pip install jupyter ipykernel

REM Register the virtual environment as a Jupyter kernel
python -m ipykernel install --user --name=.mobilization --display-name="Python (mobilization)"
