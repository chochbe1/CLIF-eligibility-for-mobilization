#!/bin/bash

cd "$(dirname "$0")"

# Activate the virtual environment
source ../.mobilization/bin/activate

# Set project root and add the code directory to PYTHONPATH
export PROJECT_ROOT=$(pwd)
export PYTHONPATH="$PROJECT_ROOT/$PYTHONPATH"

# Suppress warnings
export PYTHONWARNINGS="ignore"

# Create logs directory if not exists
mkdir -p logs

# Run Python notebooks with logging
echo "Running 01_cohort_identification..."
papermill 01_cohort_identification.ipynb /dev/null \
  2>&1 | tee logs/01_cohort_identification.log

echo "Running 02_mobilization_analysis..."
papermill 02_mobilization_analysis.ipynb /dev/null \
  2>&1 | tee logs/02_mobilization_analysis.log

# Run R script and log
echo "Running 03_competing_risk_analysis.R..."
Rscript 03_competing_risk_analysis.R \
  2>&1 | tee logs/03_competing_risk_analysis.log

echo "✅ All scripts completed!"
