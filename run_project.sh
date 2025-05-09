#!/usr/bin/env bash

# setup_and_run.sh — Combined setup and notebook execution script for CLIF project (Mac/Linux)

set -e
set -o pipefail

# ── ANSI colours for pretty output ─────────────────────────────────────────────
YELLOW="\033[33m"
CYAN="\033[36m"
GREEN="\033[32m"
RESET="\033[0m"

separator() {
  echo -e "${YELLOW}==================================================${RESET}"
}

# ── 1. Create virtual environment ──────────────────────────────────────────────
separator
if [ ! -d ".mobilization" ]; then
  echo -e "${CYAN}Creating virtual environment (.mobilization)...${RESET}"
  python3 -m venv .mobilization
else
  echo -e "${CYAN}Virtual environment already exists.${RESET}"
fi

# ── 2. Activate virtual environment ────────────────────────────────────────────
separator
echo -e "${CYAN}Activating virtual environment...${RESET}"
# shellcheck source=/dev/null
source .mobilization/bin/activate

# ── 3. Upgrade pip ─────────────────────────────────────────────────────────────
separator
echo -e "${CYAN}Upgrading pip...${RESET}"
python -m pip install --upgrade pip

# ── 4. Install required packages ───────────────────────────────────────────────
separator
echo -e "${CYAN}Installing dependencies...${RESET}"
pip install --quiet -r requirements.txt
pip install --quiet jupyter ipykernel

# ── 5. Register Jupyter kernel ─────────────────────────────────────────────────
separator
echo -e "${CYAN}Registering Jupyter kernel...${RESET}"
python -m ipykernel install --user --name=.mobilization --display-name="Python (mobilization)"

# ── 6. Change to code directory ────────────────────────────────────────────────
separator
echo -e "${CYAN}Changing to code directory...${RESET}"
cd code || { echo "❌  'code' directory not found."; exit 1; }

# ── 7. Convert and execute notebooks, streaming + logging ──────────────────────
mkdir -p logs

NOTEBOOKS=(
  "01_cohort_identification.ipynb"
  "02_mobilization_analysis.ipynb"
)

for nb in "${NOTEBOOKS[@]}"; do
  base_name="${nb%.ipynb}"
  log_file="logs/${base_name}.log"
  separator
  echo -e "${CYAN}Executing ${nb} and logging output to ${log_file}...${RESET}"
  export MPLBACKEND=Agg
  jupyter nbconvert --to script --stdout "$nb" | python 2>&1 | tee "$log_file"
done

# ── 8. Run R script ────────────────────────────────────────────────────────────
separator
echo -e "${CYAN}Running R script: 03_competing_risk_analysis.R...${RESET}"
Rscript 03_competing_risk_analysis.R 2>&1 | tee logs/03_competing_risk_analysis.log

# ── 9. Done ────────────────────────────────────────────────────────────────────
separator
echo -e "${GREEN}✅ All setup and analysis scripts completed successfully!${RESET}"

read -rp "Press [Enter] to exit..."
