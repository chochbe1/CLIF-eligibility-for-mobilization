# Eligibility for Mobilization

## Objective

The primary objective of this project is to determine the windows of opportunity for safely mobilizing patients on ventilators within the first 72 hours of first intubation, during business hours (8am-5pm). The analysis is guided by three established criteria sets, *Patel et al.*, and  *TEAM Study*, as well as a consensus criteria approach, which includes Green, Yellow, and Red safety flags.


## Required CLIF tables and fields

The following tables are required:
1. **patient**: `patient_id`, `race_category`, `ethnicity_category`, `sex_category`, `death_dttm`
2. **hospitalization**: `patient_id`, `hospitalization_id`, `admission_dttm`, `discharge_dttm`, `age_at_admission`
3. **vitals**: `hospitalization_id`, `recorded_dttm`, `vital_category`, `vital_value`
   - `vital_category` = 'heart_rate', 'resp_rate', 'sbp', 'dbp', 'map', 'resp_rate', 'spo2', ''weight_kg', 'height_cm'
4. **labs**: `hospitalization_id`, `lab_result_dttm`, `lab_category`, `lab_value`
   - `lab_category` = 'lactate', 'creatinine', 'bilirubin_total', 'po2_arterial', 'platelet_count'
5. **medication_admin_continuous**: `hospitalization_id`, `admin_dttm`, `med_name`, `med_category`, `med_dose`, `med_dose_unit`
   - `med_category` = "norepinephrine", "epinephrine", "phenylephrine", "vasopressin", "dopamine", "angiotensin", "nicardipine", "nitroprusside", "clevidipine", "cisatracurium", "vecuronium", "rocuronium"
6. **respiratory_support**: `hospitalization_id`, `recorded_dttm`, `device_category`, `mode_category`, `tracheostomy`, `fio2_set`, `lpm_set`, `resp_rate_set`, `peep_set`, `resp_rate_obs`
7. crrt_therapy: `hospitalization_id`, `recorded_dttm`

## Cohort Identification 

The study period is from January 1, 2018, to December 31, 2024. The cohort consists of patients who were placed on invasive ventilation at any point during their hospitalization within this time period. Encounters that were intubated for less than 4 hours were excluded. Additionally, encounters that received tracheostomy or were receiving any paralytic drug were considered ineligible to be mobilised for that hour.

## Configuration

1. Navigate to the `config/` directory.
2. Rename `config_template.json` to `config.json`.
3. Update the `config.json` with site-specific settings.


## Environment setup and project execution

The environment setup code is provided in the `run_project.sh` file for macOS and `run_project.bat` for Windows.

**For macOS:**

1. Make the script executable: 
```bash
chmod +x run_project.sh
```

2. Run the script:
```bash
./run_project.sh
```

3. Restart your IDE to load the new virtual environment and select the `Python (mobilization)` kernel in the Jupyter notebook.

**For Windows:**

1. Run the script in the command prompt:
```bat
run_project.bat
```

## Manual Setup and Execution

If you prefer to run the analysis manually, follow these steps:

1. **Setup Python Environment**
   - Create a virtual environment: `python -m venv .mobilization`
   - Activate the environment:
     - Windows: `.mobilization\Scripts\activate`
     - macOS/Linux: `source .mobilization/bin/activate`
   - Install dependencies: 
     ```bash
     pip install -r requirements.txt
     pip install jupyter ipykernel papermill
     ```
   - Register kernel: `python -m ipykernel install --user --name=.mobilization --display-name="Python (mobilization)"`
   - Restart your IDE to load the new virtual environment and select the `Python (mobilization)` kernel in the Jupyter notebook.

3. **Run Analysis**
   Run the following files from the code directory:
   1. Run the [01_cohort_identification.ipynb](01_cohort_identification.ipynb). Make sure you have all the required tables, variables and elements mentioned at the beginning of the script.
   2. Run the [02_mobilization_analysis.ipynb](02_mobilization_analysis.ipynb). 
   3. Run the [03_competing_risk_analysis.R](03_competing_risk_analysis.R). 
   4. Upload results from [output/final](../output/final/) to the project box folder. 

4. **OPTIONAL: Launch Dashboard**
   If you want to explore the patient level data for each criteria, checkout this dashboard
   - Navigate to app directory: `cd ../app`
   - Start Streamlit server: `streamlit run mobilization_dashboard.py`


## References

1. Patel BK, Wolfe KS, Patel SB, Dugan KC, Esbrook CL, Pawlik AJ, Stulberg M, Kemple C, Teele M, Zeleny E, Hedeker D, Pohlman AS, Arora VM, Hall JB, Kress JP. Effect of early mobilisation on long-term cognitive impairment in critical illness in the USA: a randomised controlled trial. Lancet Respir Med. 2023 Jun;11(6):563-572. doi: 10.1016/S2213-2600(22)00489-1. Epub 2023 Jan 21. [Link](https://pubmed.ncbi.nlm.nih.gov/36693400/)
2. The TEAM Study Investigators and the ANZICS Clinical Trials Group. Early Active Mobilization during Mechanical Ventilation in the ICU. N Engl J Med. 2022 Oct 26;387(19):1747-1758. doi: 10.1056/NEJMoa2209083. [Link](https://www.nejm.org/doi/full/10.1056/NEJMoa2209083)
3. Hodgson CL, Stiller K, Needham DM, Tipping CJ, Harrold M, Baldwin CE, Bradley S, Berney S, Caruana LR, Elliott D, Green M, Haines K, Higgins AM, Kaukonen KM, Leditschke IA, Nickels MR, Paratz J, Patman S, Skinner EH, Young PJ, Zanni JM, Denehy L, Webb SA. Expert consensus and recommendations on safety criteria for active mobilization of mechanically ventilated critically ill adults. Crit Care. 2014 Dec 4;18(6):658. doi: 10.1186/s13054-014-0658-y. [Link](https://pubmed.ncbi.nlm.nih.gov/25475522/)
4. Ohbe H, Jo T, Matsui H, Fushimi K, Yasunaga H. Differences in effect of early enteral nutrition on mortality among ventilated adults with shock requiring low-, medium-, and high-dose noradrenaline: A propensity-matched analysis. Clin Nutr. 2020 Feb;39(2):460-467. doi: 10.1016/j.clnu.2019.02.020. [Link](https://pubmed.ncbi.nlm.nih.gov/30808573/)
5. Goradia S, Sardaneh AA, Narayan SW, Penm J, Patanwala AE. Vasopressor dose equivalence: A scoping review and suggested formula. J Crit Care. 2021 Feb;61:233-240. doi: 10.1016/j.jcrc.2020.11.002. [Link](https://pubmed.ncbi.nlm.nih.gov/33220576/)


