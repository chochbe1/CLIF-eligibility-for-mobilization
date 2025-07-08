#!/usr/bin/env bash

# Enhanced setup_and_run.sh — Interactive CLIF project execution script (Mac/Linux)

set -e
set -o pipefail

# ── ANSI colours for pretty output ─────────────────────────────────────────────
YELLOW="\033[33m"
CYAN="\033[36m"
GREEN="\033[32m"
RED="\033[31m"
BLUE="\033[34m"
BOLD="\033[1m"
RESET="\033[0m"

# ── Setup logging ──────────────────────────────────────────────────────────────
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_FILE="${SCRIPT_DIR}/output/execution_log_${TIMESTAMP}.log"
mkdir -p "${SCRIPT_DIR}/output"

# Function to log and display
log_echo() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# Initialize log file with header
echo "CLIF Eligibility for Mobilization Analysis Pipeline - Execution Log" > "$LOG_FILE"
echo "Started at: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# ── ASCII Welcome Banner ───────────────────────────────────────────────────────
show_banner() {
    clear
    log_echo "${CYAN}${BOLD}"
    log_echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    log_echo "║                                                                              ║"
    log_echo "║                              ██████ ██      ██ ███████                       ║"
    log_echo "║                             ██      ██      ██ ██                            ║"
    log_echo "║                             ██      ██      ██ █████                         ║"
    log_echo "║                             ██      ██      ██ ██                            ║"
    log_echo "║                              ██████ ███████ ██ ██                            ║"
    log_echo "║                                                                              ║"
    log_echo "║                         ELIGIBILITY   FOR    MOBILIZATION                    ║"
    log_echo "║                                                                              ║"
    log_echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    log_echo "${RESET}"
    log_echo ""
    log_echo "${GREEN}Welcome to the CLIF Eligibility for Mobilization Analysis Pipeline!${RESET}"
    log_echo "${BLUE}This script will guide you through the complete analysis workflow.${RESET}"
    log_echo ""
}

# ── Progress separator ─────────────────────────────────────────────────────────
separator() {
    log_echo "${YELLOW}==================================================${RESET}"
}

# ── Progress bar function ──────────────────────────────────────────────────────
show_progress() {
    local step=$1
    local total=$2
    local description=$3
    
    separator
    log_echo "${CYAN}${BOLD}Step ${step}/${total}: ${description}${RESET}"
    log_echo "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] Starting: ${description}${RESET}"
    separator
}

# ── Error handler ──────────────────────────────────────────────────────────────
handle_error() {
    local exit_code=$?
    local step_name=$1
    
    log_echo ""
    log_echo "${RED}${BOLD}❌ ERROR OCCURRED!${RESET}"
    log_echo "${RED}Step failed: ${step_name}${RESET}"
    log_echo "${RED}Exit code: ${exit_code}${RESET}"
    log_echo ""
    
    # Check for common errors
    if grep -q "FileNotFoundError.*MIMIC-IV" "$LOG_FILE" 2>/dev/null; then
        log_echo "${YELLOW}It looks like the MIMIC-IV data files are not found.${RESET}"
        log_echo "${YELLOW}Please ensure you have:${RESET}"
        log_echo "${YELLOW}1. Downloaded the MIMIC-IV dataset${RESET}"
        log_echo "${YELLOW}2. Updated config/config.json with the correct data path${RESET}"
        log_echo "${YELLOW}3. Converted the data to CLIF format${RESET}"
        log_echo ""
    fi
    
    log_echo "${RED}Check the log file for full details: ${LOG_FILE}${RESET}"
    log_echo ""
    exit $exit_code
}

# Export environment variables for unbuffered output
export PYTHONUNBUFFERED=1
export MPLBACKEND=Agg

# ── Main execution flow ────────────────────────────────────────────────────────
show_banner

# Step 1: Check R environment
show_progress 1 8 "Checking R Environment"

if command -v Rscript >/dev/null 2>&1; then
    R_VERSION=$(Rscript --version 2>&1 | head -n1)
    log_echo "${GREEN}✅ R found: ${R_VERSION}${RESET}"
    RSCRIPT_PATH="Rscript"
else
    log_echo "${YELLOW}⚠️  R not found in PATH${RESET}"
    log_echo ""
    log_echo "Please choose an option:"
    log_echo "1) Provide path to R installation"
    log_echo "2) Run manually (script will skip R execution)"
    log_echo "3) Exit and install R"
    log_echo ""
    
    while true; do
        read -p "Enter your choice (1-3): " choice
        case $choice in
            1)
                read -p "Enter path to Rscript: " r_path
                if [ -f "$r_path" ] && [ -x "$r_path" ]; then
                    RSCRIPT_PATH="$r_path"
                    log_echo "${GREEN}✅ R path accepted: ${r_path}${RESET}"
                    break
                else
                    log_echo "${RED}❌ Invalid path or file not executable${RESET}"
                fi
                ;;
            2)
                RSCRIPT_PATH=""
                log_echo "${YELLOW}⚠️  R execution will be skipped${RESET}"
                break
                ;;
            3)
                log_echo "${BLUE}Please install R and try again${RESET}"
                exit 0
                ;;
            *)
                log_echo "${RED}Invalid choice. Please enter 1, 2, or 3${RESET}"
                ;;
        esac
    done
fi

# Step 2: Create virtual environment
show_progress 2 8 "Create Virtual Environment"
if [ ! -d ".mobilization" ]; then
    log_echo "Creating virtual environment (.mobilization)..."
    python3 -m venv .mobilization 2>&1 | tee -a "$LOG_FILE" || handle_error "Create Virtual Environment"
else
    log_echo "Virtual environment already exists."
fi
log_echo "${GREEN}✅ Completed: Create Virtual Environment${RESET}"

# Step 3: Activate virtual environment
show_progress 3 8 "Activate Virtual Environment"
log_echo "Activating virtual environment..."
source .mobilization/bin/activate || handle_error "Activate Virtual Environment"
log_echo "${GREEN}✅ Completed: Activate Virtual Environment${RESET}"

# Step 4: Install dependencies
show_progress 4 8 "Install Dependencies"
log_echo "Upgrading pip..."
python -m pip install --upgrade pip 2>&1 | tee -a "$LOG_FILE" || handle_error "Upgrade pip"

log_echo "Installing dependencies..."
pip install -r requirements.txt 2>&1 | tee -a "$LOG_FILE" || handle_error "Install requirements"
pip install jupyter ipykernel 2>&1 | tee -a "$LOG_FILE" || handle_error "Install jupyter"
log_echo "${GREEN}✅ Completed: Install Dependencies${RESET}"

# Step 5: Register Jupyter kernel
show_progress 5 8 "Register Jupyter Kernel"
log_echo "Registering Jupyter kernel..."
python -m ipykernel install --user --name=.mobilization --display-name="Python (mobilization)" 2>&1 | tee -a "$LOG_FILE" || handle_error "Register Jupyter Kernel"
log_echo "${GREEN}✅ Completed: Register Jupyter Kernel${RESET}"

# Step 6: Change to code directory and validate data
show_progress 6 8 "Setup Working Directory & Validate Data"
log_echo "Changing to code directory..."
cd code || handle_error "Change to code directory"
mkdir -p logs

# Check if data path exists
log_echo "Checking data configuration..."
CONFIG_FILE="../config/config.json"
if [ -f "$CONFIG_FILE" ]; then
    DATA_PATH=$(python -c "import json; print(json.load(open('$CONFIG_FILE'))['tables_path'])" 2>/dev/null)
    if [ -n "$DATA_PATH" ]; then
        if [ -d "$DATA_PATH" ]; then
            log_echo "${GREEN}✅ Data path found: $DATA_PATH${RESET}"
        else
            log_echo "${YELLOW}⚠️  Data path not found: $DATA_PATH${RESET}"
            log_echo "${YELLOW}Please ensure the MIMIC-IV data is available at this location${RESET}"
            log_echo "${YELLOW}Or update config/config.json with the correct path${RESET}"
            log_echo ""
            read -p "Continue anyway? (y/n): " continue_choice
            if [[ ! "$continue_choice" =~ ^[Yy]$ ]]; then
                log_echo "${BLUE}Exiting. Please set up the data path and try again.${RESET}"
                exit 0
            fi
        fi
    fi
else
    log_echo "${YELLOW}⚠️  Config file not found: $CONFIG_FILE${RESET}"
fi

log_echo "${GREEN}✅ Completed: Setup Working Directory${RESET}"

# Step 7: Execute notebooks
show_progress 7 8 "Execute Analysis Notebooks"

log_echo "Executing 01_cohort_identification.ipynb..."
# Ensure buffer is flushed before executing
sync
# Convert notebook to script, suppress nbconvert messages, then run with Python
jupyter nbconvert --to script --stdout --log-level ERROR 01_cohort_identification.ipynb 2>/dev/null | python -u 2>&1 | tee logs/01_cohort_identification.log | tee -a "$LOG_FILE"
if [ ${PIPESTATUS[1]} -ne 0 ]; then
    handle_error "Execute 01_cohort_identification.ipynb"
fi
log_echo "${GREEN}✅ Completed: 01_cohort_identification.ipynb${RESET}"

log_echo ""
log_echo "Executing 02_mobilization_analysis.ipynb..."
# Convert notebook to script, suppress nbconvert messages, then run with Python
jupyter nbconvert --to script --stdout --log-level ERROR 02_mobilization_analysis.ipynb 2>/dev/null | python -u 2>&1 | tee logs/02_mobilization_analysis.log | tee -a "$LOG_FILE"
if [ ${PIPESTATUS[1]} -ne 0 ]; then
    handle_error "Execute 02_mobilization_analysis.ipynb"
fi
log_echo "${GREEN}✅ Completed: 02_mobilization_analysis.ipynb${RESET}"

# Step 8: Run R script
show_progress 8 8 "Execute R Analysis"
if [ -n "$RSCRIPT_PATH" ]; then
    log_echo "Running R script: 03_competing_risk_analysis.R..."
    "$RSCRIPT_PATH" 03_competing_risk_analysis.R 2>&1 | tee logs/03_competing_risk_analysis.log | tee -a "$LOG_FILE" || handle_error "Execute R Analysis"
    log_echo "${GREEN}✅ Completed: R Analysis${RESET}"
else
    log_echo "${YELLOW}⚠️  R script execution skipped. Please run manually:${RESET}"
    log_echo "${BLUE}   cd code && Rscript 03_competing_risk_analysis.R${RESET}"
fi

# Success message
separator
log_echo "${GREEN}${BOLD}🎉 SUCCESS! All analysis steps completed successfully!${RESET}"
log_echo "${BLUE}📊 Results saved to: output/${RESET}"
log_echo "${BLUE}📝 Full log saved to: ${LOG_FILE}${RESET}"
separator

# Dashboard option
log_echo ""
log_echo "${CYAN}Would you like to launch the visualization dashboard?${RESET}"
log_echo "${BLUE}The dashboard provides interactive patient-level analysis${RESET}"
log_echo ""

while true; do
    read -p "Launch dashboard? (y/n): " yn
    case $yn in
        [Yy]*)
            log_echo "${GREEN}🚀 Starting dashboard...${RESET}"
            cd ../app
            streamlit run mobilization_dashboard.py
            break
            ;;
        [Nn]*)
            log_echo "${BLUE}Dashboard launch skipped. You can run it later with:${RESET}"
            log_echo "${BLUE}   cd app && streamlit run mobilization_dashboard.py${RESET}"
            break
            ;;
        *)
            log_echo "${RED}Please answer y or n${RESET}"
            ;;
    esac
done

log_echo ""
log_echo "${GREEN}Thank you for running the CLIF Eligibility for Mobilization Analysis Pipeline!${RESET}"
read -rp "Press [Enter] to exit..."