#!/bin/bash

# Navigate to app directory
cd "$(dirname "$0")"

# Check if virtual environment exists in parent directory
if [ -d "../.mobilization" ]; then
    echo "Activating existing virtual environment..."
    source ../.mobilization/bin/activate
else
    echo "Creating new virtual environment..."
    python3 -m venv ../.mobilization
    source ../.mobilization/bin/activate
fi

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Launch the dashboard
echo "Launching Mobilization Eligibility Dashboard..."
streamlit run mobilization_dashboard.py