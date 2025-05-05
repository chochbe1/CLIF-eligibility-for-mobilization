#!/bin/bash

set -e  # Exit immediately on error
set -o pipefail  # Propagate errors through pipes

# Function to handle errors and print custom message
handle_error() {
  echo "❌ ERROR in step: $1"
  exit 1
}

# Step 0: Move to the script's directory (project root)
cd "$(dirname "$0")" || handle_error "Change to script directory"

# Step 1: Create virtual environment if it doesn't exist
if [ ! -d ".mobilization" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .mobilization || handle_error "Creating virtual environment"
fi

# Step 2: Activate virtual environment
echo "Activating virtual environment..."
source .mobilization/bin/activate || handle_error "Activating virtual environment"

# Step 3: Install required packages
echo "Installing dependencies..."
pip install --quiet -r requirements.txt || handle_error "Installing packages from requirements.txt"
pip install --quiet jupyter ipykernel papermill || handle_error "Installing jupyter/ipykernel/papermill"

# Step 4: Register Jupyter kernel
python -m ipykernel install --user --name=.mobilization --display-name="Python (mobilization)" || handle_error "Registering Jupyter kernel"

# Step 5: Run analysis
cd code || handle_error "Changing to 'code' directory"

# Set environment variables
export PROJECT_ROOT=$(pwd)
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
export PYTHONWARNINGS="ignore"

mkdir -p logs

echo "Running 01_cohort_identification..."
papermill 01_cohort_identification.ipynb /dev/null \
  2>&1 | tee logs/01_cohort_identification.log || handle_error "01_cohort_identification.ipynb"

echo "Running 02_mobilization_analysis..."
papermill 02_mobilization_analysis.ipynb /dev/null \
  2>&1 | tee logs/02_mobilization_analysis.log || handle_error "02_mobilization_analysis.ipynb"

echo "Running 03_competing_risk_analysis.R..."
Rscript 03_competing_risk_analysis.R \
  2>&1 | tee logs/03_competing_risk_analysis.log || handle_error "03_competing_risk_analysis.R"

echo "✅ All setup and analysis scripts completed successfully!"
