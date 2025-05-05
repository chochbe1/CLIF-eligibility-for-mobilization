#!/bin/bash

# Step 0: Move to the script's directory (project root)
cd "$(dirname "$0")"

# Step 1: Create virtual environment if it doesn't exist
if [ ! -d ".mobilization" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .mobilization
fi

# Step 2: Activate virtual environment
echo "Activating virtual environment..."
source .mobilization/bin/activate

# Step 3: Install required packages
echo "Installing dependencies..."
pip install --quiet -r requirements.txt
pip install --quiet jupyter ipykernel papermill

# Step 4: Register Jupyter kernel (if needed)
python -m ipykernel install --user --name=.mobilization --display-name="Python (mobilization)"

# Step 5: Run analysis
cd code

# Set project root and update PYTHONPATH
export PROJECT_ROOT=$(pwd)
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
export PYTHONWARNINGS="ignore"

# Create logs directory
mkdir -p logs

echo "Running 01_cohort_identification..."
papermill 01_cohort_identification.ipynb /dev/null \
  2>&1 | tee logs/01_cohort_identification.log

echo "Running 02_mobilization_analysis..."
papermill 02_mobilization_analysis.ipynb /dev/null \
  2>&1 | tee logs/02_mobilization_analysis.log

echo "Running 03_competing_risk_analysis.R..."
Rscript 03_competing_risk_analysis.R \
  2>&1 | tee logs/03_competing_risk_analysis.log

echo "✅ All setup and analysis scripts completed!"
