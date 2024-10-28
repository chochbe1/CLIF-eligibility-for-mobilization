# Eligibility for Mobilization

## Objective

The primary objective of this project is to determine the windows of opportunity for safely mobilizing patients on ventilators within the first 72 hours of first intubation, during business hours (8am-5pm). The analysis is guided by two established criteria sets, *Patel et al.* and *TEAM Study*, as well as a consensus criteria approach, which includes Green, Yellow, and Red safety flags.


## Required CLIF tables and fields

The following tables are required:
1. **patient**: `patient_id`, `race_category`, `ethnicity_category`, `sex_category`
2. **hospitalization**: `patient_id`, `hospitalization_id`, `admission_dttm`, `discharge_dttm`, `age_at_admission`
3. **vitals**: `hospitalization_id`, `recorded_dttm`, `vital_category`, `vital_value`
   - `vital_category` = 'heart_rate', 'resp_rate', 'sbp', 'dbp', 'map', 'resp_rate', 'spo2'
4. **labs**: `hospitalization_id`, `lab_result_dttm`, `lab_category`, `lab_value`
   - `lab_category` = 'lactate'
5. **medication_admin_continuous**: `hospitalization_id`, `admin_dttm`, `med_name`, `med_category`, `med_dose`, `med_dose_unit`
   - `med_category` = "norepinephrine", "epinephrine", "phenylephrine", "vasopressin", "dopamine", "angiotensin", "nicardipine", "nitroprusside", "clevidipine", "cisatracurium"
6. **respiratory_support**: `hospitalization_id`, `recorded_dttm`, `device_category`, `mode_category`, `tracheostomy`, `fio2_set`, `lpm_set`, `resp_rate_set`, `peep_set`, `resp_rate_obs`

## Cohort Identification 

The study period is from March 1, 2020, to March 31, 2022. The cohort consists of patients who were placed on invasive ventilation at any point during their hospitalization within this time period. Encounters were excluded from the analysis based on the following criteria:
- Encounters that were intubated for less than 2 hours
- Encounters that received a tracheostomy within 72 hours of their first intubation
- Encounters that received Cisatracurium at any point in the first 72 hours

## Configuration

1. Navigate to the `config/` directory.
2. Rename `config_template.json` to `config.json`.
3. Update the `config.json` with site-specific settings.


## Environment setup

The environment setup code is provided in the `setup.sh` file. 

1. Make the script executable: 
```bash
chmod +x setup.sh
```

2. Run the script:
```bash
./setup.sh
```

3. Restart your IDE to load the new virtual environment and select the `Python (mobilization)` kernel in the Jupyter notebook. 


## Criteria for Safe Therapy

### 1. Patel et al. Criteria
The *Patel et al.* criteria define safe physiological ranges that must be met for mobilization:
- **Mean arterial blood pressure (MAP):** 65-110 mm Hg
- **Systolic blood pressure (SBP):** ≤ 200 mm Hg
- **Heart rate:** 40-130 beats per minute
- **Respiratory rate:** 5-40 breaths per minute
- **Pulse oximetry (SpO2):** ≥ 88%

### 2. TEAM Study Criteria
The *TEAM Study* criteria focus on hemodynamic and respiratory stability:
- **Heart rate:** ≤ 150 bpm
- **Most recent lactate:** ≤ 4.0 mmol/L
- **Noradrenaline infusion rate:**
  - ≤ 0.2 mcg/kg/min, OR
  - 0.1-0.2 mcg/kg/min (without an increase in the infusion rate of more than 25% in the last 6 hours)
- **Respiratory stability:**
  - FiO2: ≤ 0.6
  - PEEP: ≤ 16 cm H2O
- **Current respiratory rate:** ≤ 45 breaths per minute

### 3. Consensus Criteria
The Consensus Criteria categorize safety flags into Green, Yellow, and Red, providing a hierarchical assessment of patient stability:

#### Green Criteria
- **Respiratory:**
  - SpO2 ≥ 90%
  - Respiratory rate ≤ 30 breaths/min
  - FiO2 ≤ 0.6
  - PEEP ≤ 10 cm H2O
- **Cardiovascular:**
  - MAP ≥ 65 mm Hg with no or low support (Norepi < 0.1 μg/kg/min)
  - Heart rate < 120 bpm
  - Lactate < 4 mmol/L
  - Heart rate > 40 bpm

#### Yellow Criteria
- **Respiratory:**
  - SpO2 ≥ 90%
  - FiO2 > 0.6
  - Respiratory rate > 30 breaths/min
  - PEEP > 10 cm H2O
- **Cardiovascular:**
  - MAP ≥ 65 mm Hg with moderate support (Norepi 0.1-0.3 μg/kg/min)
  - Heart rate 120-150 bpm
  - Shock with lactate > 4 mmol/L
  - Heart rate > 40 bpm

#### Red Criteria
- **Respiratory:**
  - SpO2 < 90%
- **Cardiovascular:**
  - MAP < 65 mm Hg despite support
  - MAP ≥ 65 mm Hg but on high support (Norepi > 0.3 μg/kg/min)
  - IV therapy for hypertensive emergency (SBP > 200 mm Hg or MAP > 110 mm Hg with specific medications)
  - Heart rate > 150 bpm or < 40 bpm


