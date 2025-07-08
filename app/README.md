# Mobilization Eligibility Dashboard

A Streamlit-based visualization dashboard for debugging patient mobilization eligibility in the CLIF project.

## Features

- **Patient Selection**: Dropdown to select individual patients by encounter_block
- **Patient Metadata**: Display key patient information including hospitalization ID, discharge category, and vital timestamps
- **Vital Trends**: Interactive plots showing relevant vitals for each mobilization criteria
- **Eligibility Timeline**: Binary charts showing eligibility status over time with first eligibility annotations
- **Ineligibility Analysis**: Detailed breakdown of why patients failed to meet criteria
- **Multi-Criteria Comparison**: Tabs for Patel, TEAM, Green, and Yellow criteria
- **Data Export**: Download patient-specific data as CSV

## Installation

1. Navigate to the app directory:
```bash
cd app/
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the dashboard:
```bash
streamlit run mobilization_dashboard.py
```

The dashboard will open in your default web browser.

## Dashboard Layout

1. **Header**: Patient metadata including IDs, discharge category, and timeline
2. **Main Area**: Tabbed interface with:
   - **Patel Criteria**: MAP, SBP, heart rate, respiratory rate, SpO2 trends
   - **TEAM Criteria**: Heart rate, lactate, norepinephrine, FiO2, PEEP trends
   - **Green Criteria**: Consensus green light eligibility
   - **Yellow Criteria**: Consensus yellow/green light eligibility
   - **Summary**: Overall eligibility summary and data export

## Debugging Features

- **Ineligibility Reasons**: When a patient is never eligible, the dashboard shows which specific flags failed and for how many hours
- **First Eligibility Annotation**: Visual marker showing when patient first became eligible
- **Red Flag Detection**: For consensus criteria, displays which red flags were present
- **Download Functionality**: Export patient data for further analysis

## Performance

The dashboard uses Streamlit's caching mechanism to optimize performance when loading large parquet files. Initial load may take a few seconds, but subsequent interactions are fast.