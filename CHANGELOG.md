# CHANGELOG

**Author:** Kaveri Chhikara  
**Project:** CLIF Eligibility for Mobilization

---

## Version 1 – October 30, 2024

Initial implementation.

---

## Version 2 – February 10, 2025

- Extracted `discharge_dttm` and `death_dttm`. Every patient must have one; assume discharged alive if not dead.
- Created flags for paralytics. Instead of excluding patients, we now exclude only the hours when paralytics were active.
- Updated exclusion: exclude patients intubated for **< 4 hours** (previously 2 hours).
- Added stitching logic for encounters across multiple hospitals at the same site.
- Extended analysis to **competing risk** framework:
  - **Event 1**: Became eligible  
  - **Event 2**: Died  
  - **Event 3**: Discharged alive

---

## Version 3 – March 12, 2025

- Implemented automatic UTC → local time conversion using config file.
- No manual datetime adjustments required in downstream scripts.

---

## Version 4 – March 20, 2025

- Eligibility now only begins during **business hours**, enabling true time-to-eligibility measurement.
- Full hospitalization is now the input for **survival analysis**.
- Updated `.qmd` script for competing risk analysis and validated against UMN results.

---

## Version 5 – April 15, 2025

- Fixed lactate carry-forward bug: values were incorrectly filtered to the first 3 days.
- Now lactate carry-forward times out after **24 hours**.
- For TEAM: eligible if lactate ≤ 4 or missing.
- `team_ne` flag is 1 if **no NE administered** (no more NA).
- Added SOFA score calculation using the original **1997 definition**.

---

## Version 6 – April 17, 2025

- Default criteria flags to **1 (eligible)** for NAs, unless a lower threshold is defined.
- Cases where **NAs are not eligible**:
  - **Red**: NE > 0.3
  - **Yellow**: MAP ≥ 65 and NE in [0.1–0.3]
- General rule:  
  - If a **minimum threshold** exists → NA = not eligible  
  - If **no threshold** → NA = eligible

---

## Version 7 – April 23, 2025

- Integrated updated SOFA logic from `sofa_score.py`.
- Refactored waterfall logic to match **Nick Ingraham's R version**.

---

## Version 8 – April 28, 2025

- Updated outlier threshold config to include 0 as a **valid lower bound**.
- Red and paralytic **med flags set to 1 only if dose > 0**.
- Pressor summary: use **last recorded value** per hour (not max).
- Added **CRRT flag**: if CRRT administered within `[start_dttm - 72hrs, end_dttm]`, renal SOFA score = 4.

---

## Version 9 – May 1, 2025

- Reinforced **24-hour lactate timeout**.
- Final outcome set to **dead** if discharge category includes **both "Hospice" and "Expired"**.
- Updated TEAM criteria to use **respiratory rate from vitals**, not respiratory support. Same as the other two criteria.
- Pressor value logic now **always uses last recorded value** for the hour.
- The sequence of hours starts with the **first hour of intubation** to the last recorded hour for vitals, labs, and medications.

## Version 10 – May 5, 2025
- Updated the Chicago and consensus criteria to use Average MAP instead of the min and max value of MAP.
- Removed deprecated survival analysis code using Kaplan-Meier, superseded by competing risk framework on full patient timeline in 03 R script.
