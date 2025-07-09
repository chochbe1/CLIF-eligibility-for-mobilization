import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta
import pyarrow.parquet as pq

st.set_page_config(
    page_title="Eligibility for mobilization Dashboard",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data(data_path):
    """Load all necessary data files"""
    try:
        required_files = {
            'hourly': data_path / "intermediate" / "final_df_w_criteria.parquet",
            'blocks': data_path / "intermediate" / "final_df_blocks.parquet",
            'outcomes': data_path / "intermediate" / "cohort_all_ids_w_outcome.parquet",
            'cr_patel': data_path / "intermediate" / "competing_risk_patel_final.parquet",
            'cr_team': data_path / "intermediate" / "competing_risk_team_final.parquet",
            'cr_green': data_path / "intermediate" / "competing_risk_green_final.parquet",
            'cr_yellow': data_path / "intermediate" / "competing_risk_yellow_final.parquet"
        }
        
        # Check which files exist
        missing_files = []
        for name, filepath in required_files.items():
            if not filepath.exists():
                missing_files.append(f"{name}: {filepath.name}")
        
        if missing_files:
            st.error("Missing required data files:")
            for missing in missing_files:
                st.error(f"  - {missing}")
            return None
        
        # Load all data files
        data = {}
        for name, filepath in required_files.items():
            data[name] = pd.read_parquet(filepath)
            
        return data
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def get_patient_metadata(data, encounter_block):
    """Extract patient metadata from cohort_all_ids_w_outcome data"""
    # Get data from cohort_all_ids_w_outcome
    outcome_row = data['outcomes'][data['outcomes']['encounter_block'] == encounter_block]
    
    if outcome_row.empty:
        return None
    
    row = outcome_row.iloc[0]
    
    # Get hourly data to calculate total hours
    patient_data = data['hourly'][data['hourly']['encounter_block'] == encounter_block]
    total_hours = len(patient_data) if not patient_data.empty else 0
    
    metadata = {
        'patient_id': row.get('patient_id', 'N/A'),
        'hospitalization_id': row.get('hospitalization_id', 'N/A'),
        'discharge_category': row.get('discharge_category', 'N/A'),
        'first_vital_dttm': row.get('block_first_vital_dttm', 'N/A'),
        'last_vital_dttm': row.get('block_last_vital_dttm', 'N/A'),
        'total_hours': total_hours
    }
    
    return metadata

def plot_vital_trends(patient_data, vital_columns, criteria_name):
    """Create plotly figure for vital trends"""
    fig = go.Figure()
    
    # Define colors for each vital
    colors = {
        'map': '#1f77b4',
        'sbp': '#ff7f0e', 
        'heart_rate': '#2ca02c',
        'resp_rate': '#d62728',
        'spo2': '#9467bd',
        'fio2': '#8c564b',
        'peep': '#e377c2',
        'lactate': '#7f7f7f',
        'norepinephrine_dose': '#bcbd22'
    }
    
    # Determine x-axis data
    if 'recorded_dttm' in patient_data.columns:
        x_data = patient_data['recorded_dttm']
        x_title = "Time"
    else:
        x_data = patient_data['time_from_vent']
        x_title = "Hours from Ventilation Start"
    
    for col in vital_columns:
        if col in patient_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=x_data,
                    y=patient_data[col],
                    mode='lines+markers',
                    name=col.replace('_', ' ').title(),
                    line=dict(color=colors.get(col, '#000000')),
                    hovertemplate='%{y:.2f}<extra></extra>'
                )
            )
    
    fig.update_layout(
        title=f"{criteria_name} - Vital Trends",
        xaxis_title=x_title,
        yaxis_title="Value",
        hovermode='x unified',
        height=400,
        template='plotly_white'
    )
    
    return fig

def plot_eligibility_timeline(patient_data, eligibility_col, criteria_name, first_eligible_time=None):
    """Create eligibility timeline plot with failed flags on hover and trach/paralytic indicators"""
    fig = go.Figure()
    
    # Check if eligibility column exists
    if eligibility_col not in patient_data.columns:
        fig.add_annotation(
            text=f"Column '{eligibility_col}' not found in data",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )
        return fig
    
    # Determine x-axis data
    if 'recorded_dttm' in patient_data.columns:
        x_data = patient_data['recorded_dttm']
        x_title = "Time"
    else:
        x_data = patient_data['time_from_vent']
        x_title = "Hours from Ventilation Start"
    
    # Create hover text with failed flags and business hours info
    hover_text = []
    
    # Check for business hours using recorded_hour column (8-16 inclusive)
    business_hours_info = []
    if 'recorded_hour' in patient_data.columns:
        for idx, row in patient_data.iterrows():
            hour = row['recorded_hour']
            if pd.notna(hour):
                is_business_time = 8 <= hour <= 16
                business_hours_info.append(is_business_time)
            else:
                business_hours_info.append(False)  # Assume non-business if unknown
    else:
        # If no recorded_hour column, assume all are non-business hours
        business_hours_info = [False] * len(patient_data)
    
    # Define flag mappings for different criteria
    criteria_flags = {
        'patel': ['patel_map_flag', 'patel_sbp_flag', 'patel_pulse_flag', 'patel_resp_rate_flag', 'patel_spo2_flag'],
        'team': ['team_pulse_flag', 'team_lactate_flag', 'team_ne_flag', 'team_fio2_flag', 'team_peep_flag', 'team_resp_rate_flag'],
        'green': ['green_resp_spo2_flag', 'green_resp_rate_flag', 'green_fio2_flag', 'green_peep_flag', 'green_map_flag', 'green_pulse_flag', 'green_lactate_flag', 'green_hr_flag'],
        'yellow': ['yellow_resp_spo2_flag', 'yellow_fio2_flag', 'yellow_resp_rate_flag', 'yellow_peep_flag', 'yellow_map_flag', 'yellow_pulse_flag', 'yellow_lactate_flag']
    }
    
    criteria_key = criteria_name.lower()
    if criteria_key in criteria_flags:
        flags = criteria_flags[criteria_key]
        
        for idx, (patient_idx, row) in enumerate(patient_data.iterrows()):
            eligible = row[eligibility_col]
            is_business = business_hours_info[idx]
            
            # Get hour number
            if 'time_from_vent' in row:
                hour_num = int(row['time_from_vent']) if pd.notna(row['time_from_vent']) else idx
            else:
                hour_num = idx
            
            if not is_business:
                hover_text.append(f"Hour {hour_num}: Outside business hours")
            elif eligible == 1:
                hover_text.append(f"Hour {hour_num}: Eligible")
            else:
                failed_flags = []
                other_reasons = []
                
                # Check individual flags
                for flag in flags:
                    if flag in row and row[flag] == 0:
                        flag_name = flag.replace(f'{criteria_key}_', '').replace('_flag', '').upper()
                        failed_flags.append(flag_name)
                
                # Check for trach and paralytics (applies to all criteria)
                if 'hourly_trach' in row and row['hourly_trach'] == 1:
                    other_reasons.append("TRACH")
                if 'paralytics_flag' in row and row['paralytics_flag'] == 1:
                    other_reasons.append("PARALYTICS")
                
                # For green/yellow criteria, also check for red flags
                if criteria_key in ['green', 'yellow']:
                    if 'any_red' in row and row['any_red'] == 1:
                        other_reasons.append("RED_FLAGS")
                
                all_reasons = failed_flags + other_reasons
                
                if all_reasons:
                    hover_text.append(f"Hour {hour_num}: Failed: {', '.join(all_reasons)}")
                else:
                    hover_text.append(f"Hour {hour_num}: Not Eligible (Check data)")
    else:
        # For other criteria, show eligible/not eligible with business hours
        for idx, (patient_idx, row) in enumerate(patient_data.iterrows()):
            eligible = row[eligibility_col]
            is_business = business_hours_info[idx]
            
            # Get hour number
            if 'time_from_vent' in row:
                hour_num = int(row['time_from_vent']) if pd.notna(row['time_from_vent']) else idx
            else:
                hour_num = idx
            
            if not is_business:
                hover_text.append(f"Hour {hour_num}: Outside business hours")
            elif eligible == 1:
                hover_text.append(f"Hour {hour_num}: Eligible")
            else:
                hover_text.append(f"Hour {hour_num}: Not Eligible")
    
    # Main eligibility line with custom hover text
    fig.add_trace(
        go.Scatter(
            x=x_data,
            y=patient_data[eligibility_col].astype(int),
            mode='lines',
            fill='tozeroy',
            name='Eligible',
            line=dict(color='green', width=2),
            fillcolor='rgba(0, 255, 0, 0.2)',
            text=hover_text,
            hovertemplate='%{text}<extra></extra>'
        )
    )
    
    # Add tracheostomy indicators (only when present)
    if 'hourly_trach' in patient_data.columns:
        trach_periods = patient_data[patient_data['hourly_trach'] == 1]
        if not trach_periods.empty:
            fig.add_trace(
                go.Scatter(
                    x=trach_periods[x_data.name] if hasattr(x_data, 'name') else x_data[trach_periods.index],
                    y=[-0.05] * len(trach_periods),
                    mode='markers',
                    marker=dict(symbol='square', size=8, color='orange'),
                    name='Tracheostomy',
                    hovertemplate='Tracheostomy<extra></extra>'
                )
            )
    
    # Add paralytic indicators (only when present)
    if 'paralytics_flag' in patient_data.columns:
        paralytic_periods = patient_data[patient_data['paralytics_flag'] == 1]
        if not paralytic_periods.empty:
            fig.add_trace(
                go.Scatter(
                    x=paralytic_periods[x_data.name] if hasattr(x_data, 'name') else x_data[paralytic_periods.index],
                    y=[-0.08] * len(paralytic_periods),
                    mode='markers',
                    marker=dict(symbol='diamond', size=8, color='red'),
                    name='Paralytics',
                    hovertemplate='Paralytics<extra></extra>'
                )
            )
    
    
    # Add annotation for first eligibility
    if first_eligible_time is not None and first_eligible_time > 0:
        if 'recorded_dttm' in patient_data.columns:
            first_eligible_dt = patient_data.iloc[int(first_eligible_time)]['recorded_dttm']
            fig.add_vline(
                x=first_eligible_dt,
                line_dash="dash",
                line_color="blue",
                annotation_text=f"First Eligible (Hour {int(first_eligible_time)})",
                annotation_position="top"
            )
        else:
            fig.add_vline(
                x=first_eligible_time,
                line_dash="dash",
                line_color="blue",
                annotation_text=f"First Eligible (Hour {int(first_eligible_time)})",
                annotation_position="top"
            )
    
    # Add note about trach/paralytics status
    trach_status = ""
    paralytic_status = ""
    
    if 'hourly_trach' in patient_data.columns:
        has_trach = (patient_data['hourly_trach'] == 1).any()
        if has_trach:
            trach_status = "Tracheostomy periods shown as orange squares"
        else:
            trach_status = "No tracheostomy throughout stay"
    
    if 'paralytics_flag' in patient_data.columns:
        has_paralytics = (patient_data['paralytics_flag'] == 1).any()
        if has_paralytics:
            paralytic_status = "Paralytic periods shown as red diamonds"
        else:
            paralytic_status = "No paralytics throughout stay"
    
    # Create subtitle with status notes
    subtitle_parts = []
    if trach_status:
        subtitle_parts.append(trach_status)
    if paralytic_status:
        subtitle_parts.append(paralytic_status)
    
    subtitle = " | ".join(subtitle_parts) if subtitle_parts else ""
    
    # Add second x-axis for recorded_hour
    if 'recorded_hour' in patient_data.columns:
        # Create secondary x-axis data
        fig.update_layout(
            xaxis2=dict(
                title="Time of Day (Hour)",
                overlaying='x',
                side='bottom',
                position=0,
                anchor='y',
                tickmode='array',
                tickvals=x_data,
                ticktext=[f"{int(h):02d}:00" if pd.notna(h) else "" for h in patient_data['recorded_hour']]
            )
        )
    
    fig.update_layout(
        title=dict(
            text=f"{criteria_name} - Eligibility Status<br><span style='font-size:12px;color:gray'>{subtitle}</span>",
            x=0,  # Left align
            xanchor='left'
        ),
        xaxis_title=x_title,
        xaxis=dict(domain=[0, 1]),
        yaxis_title="Eligible (1) / Not Eligible (0)",
        yaxis=dict(tickmode='linear', tick0=0, dtick=1, range=[-0.15, 1.1]),
        height=320,
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def get_ineligibility_reasons(patient_data, criteria_prefix):
    """Analyze why patient was never eligible"""
    flag_columns = [col for col in patient_data.columns if col.startswith(f'{criteria_prefix}_') and col.endswith('_flag')]
    
    reasons = []
    for col in flag_columns:
        if (patient_data[col] == 0).any():
            failed_hours = (patient_data[col] == 0).sum()
            total_hours = len(patient_data)
            percentage = (failed_hours / total_hours) * 100
            reasons.append({
                'flag': col.replace(f'{criteria_prefix}_', '').replace('_flag', ''),
                'failed_hours': failed_hours,
                'percentage': percentage
            })
    
    return sorted(reasons, key=lambda x: x['percentage'], reverse=True)

def plot_patel_components(patient_data):
    """Create component trend plots for Chicago criteria with threshold lines"""
    
    # Determine x-axis data
    if 'recorded_dttm' in patient_data.columns:
        x_data = patient_data['recorded_dttm']
        x_title = "Time"
    else:
        x_data = patient_data['time_from_vent']
        x_title = "Hours from Ventilation Start"
    
    # Define Chicago components and their thresholds
    patel_components = {
        'avg_map': {
            'title': 'Mean Arterial Pressure (MAP)',
            'y_title': 'Avg MAP (mmHg)',
            'unit': 'mmHg',
            'thresholds': {'min': 65, 'max': 110},
            'color': '#1f77b4'
        },
        'max_sbp': {
            'title': 'Systolic Blood Pressure (SBP)',
            'y_title': 'Max SBP (mmHg)',
            'unit': 'mmHg', 
            'thresholds': {'max': 200},
            'color': '#ff7f0e'
        },
        'min_heart_rate': {
            'title': 'Heart Rate (Min)',
            'unit': 'bpm',
            'thresholds': {'min': 40},
            'color': '#2ca02c'
        },
        'max_heart_rate': {
            'title': 'Heart Rate (Max)',
            'unit': 'bpm',
            'thresholds': {'max': 130},
            'color': '#2ca02c'
        },
        'min_respiratory_rate': {
            'title': 'Respiratory Rate (Min)',
            'unit': 'breaths/min',
            'thresholds': {'min': 5},
            'color': '#d62728'
        },
        'max_respiratory_rate': {
            'title': 'Respiratory Rate (Max)', 
            'unit': 'breaths/min',
            'thresholds': {'max': 40},
            'color': '#d62728'
        },
        'min_spo2': {
            'title': 'Pulse Oximetry (SpO2)',
            'unit': '%',
            'thresholds': {'min': 88},
            'color': '#9467bd'
        }
    }
    
    # Create subplots for each component
    figs = {}
    
    for component, config in patel_components.items():
        if component not in patient_data.columns:
            continue
            
        fig = go.Figure()
        
        # Add the trend line
        fig.add_trace(
            go.Scatter(
                x=x_data,
                y=patient_data[component],
                mode='lines+markers',
                name=config['title'],
                line=dict(color=config['color'], width=2),
                marker=dict(size=4),
                hovertemplate=f'%{{y:.1f}} {config["unit"]}<extra></extra>'
            )
        )
        
        # Add threshold lines
        if 'min' in config['thresholds']:
            min_val = config['thresholds']['min']
            fig.add_hline(
                y=min_val,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Min: {min_val} {config['unit']}",
                annotation_position="bottom right"
            )
        
        if 'max' in config['thresholds']:
            max_val = config['thresholds']['max']
            fig.add_hline(
                y=max_val,
                line_dash="dash", 
                line_color="red",
                annotation_text=f"Max: {max_val} {config['unit']}",
                annotation_position="top right"
            )
        
        # Update layout
        y_axis_title = config.get('y_title', f"{config['title']} ({config['unit']})")
        fig.update_layout(
            title=config['title'],
            xaxis_title=x_title,
            yaxis_title=y_axis_title,
            height=300,
            template='plotly_white',
            showlegend=False
        )
        
        figs[component] = fig
    
    return figs

def plot_team_components(patient_data):
    """Create component trend plots for TEAM criteria with threshold lines"""
    
    # Determine x-axis data
    if 'recorded_dttm' in patient_data.columns:
        x_data = patient_data['recorded_dttm']
        x_title = "Time"
    else:
        x_data = patient_data['time_from_vent']
        x_title = "Hours from Ventilation Start"
    
    # Define TEAM components and their thresholds
    team_components = {
        'max_heart_rate': {
            'title': 'Heart Rate',
            'y_title': 'Max Heart Rate (bpm)',
            'unit': 'bpm',
            'thresholds': {'max': 150},
            'color': '#2ca02c'
        },
        'lactate': {
            'title': 'Lactate',
            'y_title': 'Lactate (mmol/L)',
            'unit': 'mmol/L',
            'thresholds': {'max': 4.0},
            'color': '#ff7f0e'
        },
        'ne_calc_last': {
            'title': 'Norepinephrine',
            'y_title': 'Norepinephrine (mcg/kg/min)',
            'unit': 'mcg/kg/min',
            'thresholds': {'max': 0.2},
            'color': '#d62728'
        },
        'min_fio2_set': {
            'title': 'FiO2',
            'y_title': 'Min FiO2',
            'unit': '',
            'thresholds': {'max': 0.6},
            'color': '#9467bd'
        },
        'max_peep_set': {
            'title': 'PEEP',
            'y_title': 'Max PEEP (cm H2O)',
            'unit': 'cm H2O',
            'thresholds': {'max': 16},
            'color': '#8c564b'
        },
        'max_respiratory_rate': {
            'title': 'Respiratory Rate',
            'y_title': 'Max Resp Rate (breaths/min)',
            'unit': 'breaths/min',
            'thresholds': {'max': 45},
            'color': '#e377c2'
        }
    }
    
    # Create subplots for each component
    figs = {}
    
    for component, config in team_components.items():
        if component not in patient_data.columns:
            continue
            
        fig = go.Figure()
        
        # Add the trend line
        fig.add_trace(
            go.Scatter(
                x=x_data,
                y=patient_data[component],
                mode='lines+markers',
                name=config['title'],
                line=dict(color=config['color'], width=2),
                marker=dict(size=4),
                hovertemplate=f'%{{y:.2f}} {config["unit"]}<extra></extra>'
            )
        )
        
        # Add threshold lines
        if 'min' in config['thresholds']:
            min_val = config['thresholds']['min']
            fig.add_hline(
                y=min_val,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Min: {min_val} {config['unit']}",
                annotation_position="bottom right"
            )
        
        if 'max' in config['thresholds']:
            max_val = config['thresholds']['max']
            fig.add_hline(
                y=max_val,
                line_dash="dash", 
                line_color="red",
                annotation_text=f"Max: {max_val} {config['unit']}",
                annotation_position="top right"
            )
        
        # Update layout
        y_axis_title = config.get('y_title', f"{config['title']} ({config['unit']})")
        fig.update_layout(
            title=config['title'],
            xaxis_title=x_title,
            yaxis_title=y_axis_title,
            height=300,
            template='plotly_white',
            showlegend=False
        )
        
        figs[component] = fig
    
    return figs

def plot_green_components(patient_data):
    """Create component trend plots for Green criteria with threshold lines"""
    
    # Determine x-axis data
    if 'recorded_dttm' in patient_data.columns:
        x_data = patient_data['recorded_dttm']
        x_title = "Time"
    else:
        x_data = patient_data['time_from_vent']
        x_title = "Hours from Ventilation Start"
    
    # Define Green components and their thresholds
    green_components = {
        'min_spo2': {
            'title': 'SpO2',
            'y_title': 'Min SpO2 (%)',
            'unit': '%',
            'thresholds': {'min': 90},
            'color': '#2ca02c'
        },
        'avg_map': {
            'title': 'Mean Arterial Pressure',
            'y_title': 'Avg MAP (mmHg)',
            'unit': 'mmHg',
            'thresholds': {'min': 65},
            'color': '#1f77b4'
        },
        'ne_calc_last': {
            'title': 'Norepinephrine',
            'y_title': 'Norepinephrine (mcg/kg/min)',
            'unit': 'mcg/kg/min',
            'thresholds': {'max': 0.1},
            'color': '#d62728'
        },
        'max_heart_rate': {
            'title': 'Heart Rate (Max)',
            'y_title': 'Max Heart Rate (bpm)',
            'unit': 'bpm',
            'thresholds': {'max': 150},
            'color': '#ff7f0e'
        },
        'min_heart_rate': {
            'title': 'Heart Rate (Min)',
            'y_title': 'Min Heart Rate (bpm)', 
            'unit': 'bpm',
            'thresholds': {'min': 40, 'max': 120},
            'color': '#ff7f0e'
        },
        'min_fio2_set': {
            'title': 'FiO2',
            'y_title': 'Min FiO2',
            'unit': '',
            'thresholds': {'max': 0.6},
            'color': '#9467bd'
        },
        'max_respiratory_rate': {
            'title': 'Respiratory Rate',
            'y_title': 'Max Resp Rate (breaths/min)',
            'unit': 'breaths/min',
            'thresholds': {'max': 30},
            'color': '#e377c2'
        },
        'min_peep_set': {
            'title': 'PEEP',
            'y_title': 'Min PEEP (cm H2O)',
            'unit': 'cm H2O',
            'thresholds': {'max': 10},
            'color': '#8c564b'
        },
        'lactate': {
            'title': 'Lactate',
            'y_title': 'Lactate (mmol/L)',
            'unit': 'mmol/L',
            'thresholds': {'max': 4.0},
            'color': '#bcbd22'
        }
    }
    
    # Create subplots for each component
    figs = {}
    
    for component, config in green_components.items():
        if component not in patient_data.columns:
            continue
            
        fig = go.Figure()
        
        # Add the trend line
        fig.add_trace(
            go.Scatter(
                x=x_data,
                y=patient_data[component],
                mode='lines+markers',
                name=config['title'],
                line=dict(color=config['color'], width=2),
                marker=dict(size=4),
                hovertemplate=f'%{{y:.2f}} {config["unit"]}<extra></extra>'
            )
        )
        
        # Add threshold lines
        if 'min' in config['thresholds']:
            min_val = config['thresholds']['min']
            fig.add_hline(
                y=min_val,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Min: {min_val} {config['unit']}",
                annotation_position="bottom right"
            )
        
        if 'max' in config['thresholds']:
            max_val = config['thresholds']['max']
            fig.add_hline(
                y=max_val,
                line_dash="dash", 
                line_color="red",
                annotation_text=f"Max: {max_val} {config['unit']}",
                annotation_position="top right"
            )
        
        # Update layout
        y_axis_title = config.get('y_title', f"{config['title']} ({config['unit']})")
        fig.update_layout(
            title=config['title'],
            xaxis_title=x_title,
            yaxis_title=y_axis_title,
            height=300,
            template='plotly_white',
            showlegend=False
        )
        
        figs[component] = fig
    
    return figs

def main():
    st.title("🚦 Eligibility for mobilization Dashboard")
    st.markdown("Patient-level visualization for exploring mobilization eligibility criteria")
    
    # Get the project root directory using multiple fallback methods
    current_dir = Path.cwd()
    script_dir = Path(__file__).parent if '__file__' in globals() else current_dir
    
    # Try different approaches to find the project root
    possible_roots = [
        script_dir.parent,  # If running from app/ folder
        current_dir,        # If running from project root
        current_dir.parent  # If running from app/ folder via cwd
    ]
    
    # Find the correct project root by looking for output directory
    project_root = None
    for root in possible_roots:
        if (root / "output").exists():
            project_root = root
            break
    
    if project_root is None:
        st.error("Could not find project root directory with 'output' folder")
        st.info("Please run the dashboard from the project root or app directory")
        return
    
    # Use the main output directory with intermediate files
    data_path = project_root / "output"
    
    # Check if data path exists
    if not data_path.exists():
        st.error(f"Data directory not found: {data_path}")
        st.info("Please ensure you have run the analysis pipeline to generate the data files.")
        return
    
    # Check if intermediate directory exists
    intermediate_path = data_path / "intermediate"
    if not intermediate_path.exists():
        st.error(f"Intermediate directory not found: {intermediate_path}")
        st.info("Please ensure the analysis has been completed and intermediate files have been generated.")
        return
    
    # Load data
    with st.spinner("Loading data..."):
        data = load_data(data_path)
    
    if data is None:
        st.error("Failed to load data. Please check the data path.")
        return
    
    # SIDEBAR: Patient Selection and Information
    st.sidebar.title("Patient Selection")
    encounter_blocks = sorted(data['hourly']['encounter_block'].unique())
    
    selected_encounter = st.sidebar.selectbox(
        "Select Encounter Block",
        options=encounter_blocks,
        index=0
    )
    
    # Display patient metadata in sidebar
    metadata = get_patient_metadata(data, selected_encounter)
    
    if metadata:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Patient Information")
        
        # Use smaller font size for patient information
        st.sidebar.markdown(f"""
        <div style="font-size: 14px;">
        <b>Patient ID:</b> {metadata['patient_id']}<br>
        <b>Hospitalization ID:</b> {metadata['hospitalization_id']}<br>
        <b>Discharge Category:</b> {metadata['discharge_category']}<br>
        <b>First Vital:</b> {metadata['first_vital_dttm'].strftime('%Y-%m-%d %H:%M') if pd.notna(metadata['first_vital_dttm']) and not isinstance(metadata['first_vital_dttm'], str) else metadata['first_vital_dttm']}<br>
        <b>Last Vital:</b> {metadata['last_vital_dttm'].strftime('%Y-%m-%d %H:%M') if pd.notna(metadata['last_vital_dttm']) and not isinstance(metadata['last_vital_dttm'], str) else metadata['last_vital_dttm']}<br>
        <b>Total Hours:</b> {metadata['total_hours']}
        </div>
        """, unsafe_allow_html=True)
    
    # Get patient data
    patient_data = data['hourly'][data['hourly']['encounter_block'] == selected_encounter].copy()
    
    # Sort by time column (prefer recorded_dttm, fallback to time_from_vent)
    if 'recorded_dttm' in patient_data.columns:
        patient_data = patient_data.sort_values('recorded_dttm')
    elif 'time_from_vent' in patient_data.columns:
        patient_data = patient_data.sort_values('time_from_vent')
    
    # Main visualization area
    st.markdown("""
    <h2 style="text-align: center; margin-bottom: 30px; color: white;">
        Time to First Eligibility Since Intubation
    </h2>
    """, unsafe_allow_html=True)
    
    # Get competing risk data for this patient
    cr_data = {
        'patel': data['cr_patel'][data['cr_patel']['encounter_block'] == selected_encounter],
        'team': data['cr_team'][data['cr_team']['encounter_block'] == selected_encounter],
        'green': data['cr_green'][data['cr_green']['encounter_block'] == selected_encounter],
        'yellow': data['cr_yellow'][data['cr_yellow']['encounter_block'] == selected_encounter]
    }
    
    # Create circular status boxes for each criteria
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        patel_eligible = cr_data['patel']['time_eligibility'].iloc[0] if not cr_data['patel'].empty else None
        if patel_eligible is not None and not pd.isna(patel_eligible):
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #8B4B6B, #A0537A);
                color: white;
                border-radius: 50%;
                width: 140px;
                height: 140px;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                margin: auto;
                font-size: 16px;
                font-weight: bold;
                box-shadow: 0 4px 15px rgba(139, 75, 107, 0.6);
                border: 3px solid rgba(255, 255, 255, 0.1);
                transition: transform 0.2s ease;
                opacity: 0.9;
            ">
                CHICAGO<br>Hour {int(patel_eligible)}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #D3D3D3, #A9A9A9);
                color: #666;
                border-radius: 50%;
                width: 140px;
                height: 140px;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                margin: auto;
                font-size: 16px;
                font-weight: bold;
                box-shadow: 0 4px 15px rgba(169, 169, 169, 0.3);
                border: 3px solid rgba(255, 255, 255, 0.2);
                opacity: 0.7;
            ">
                CHICAGO
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        team_eligible = cr_data['team']['time_eligibility'].iloc[0] if not cr_data['team'].empty else None
        if team_eligible is not None and not pd.isna(team_eligible):
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #7B99C4, #8AA5CC);
                color: white;
                border-radius: 50%;
                width: 140px;
                height: 140px;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                margin: auto;
                font-size: 16px;
                font-weight: bold;
                box-shadow: 0 4px 15px rgba(123, 153, 196, 0.6);
                border: 3px solid rgba(255, 255, 255, 0.1);
                transition: transform 0.2s ease;
                opacity: 0.9;
            ">
                TEAM<br>Hour {int(team_eligible)}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #D3D3D3, #A9A9A9);
                color: #666;
                border-radius: 50%;
                width: 140px;
                height: 140px;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                margin: auto;
                font-size: 16px;
                font-weight: bold;
                box-shadow: 0 4px 15px rgba(169, 169, 169, 0.3);
                border: 3px solid rgba(255, 255, 255, 0.2);
                opacity: 0.7;
            ">
                TEAM
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        yellow_eligible = cr_data['yellow']['time_eligibility'].iloc[0] if not cr_data['yellow'].empty else None
        if yellow_eligible is not None and not pd.isna(yellow_eligible):
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #E5BE60, #EBC87A);
                color: white;
                border-radius: 50%;
                width: 140px;
                height: 140px;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                margin: auto;
                font-size: 16px;
                font-weight: bold;
                box-shadow: 0 4px 15px rgba(229, 190, 96, 0.6);
                border: 3px solid rgba(255, 255, 255, 0.1);
                transition: transform 0.2s ease;
                opacity: 0.9;
            ">
                YELLOW<br>Hour {int(yellow_eligible)}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #D3D3D3, #A9A9A9);
                color: #666;
                border-radius: 50%;
                width: 140px;
                height: 140px;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                margin: auto;
                font-size: 16px;
                font-weight: bold;
                box-shadow: 0 4px 15px rgba(169, 169, 169, 0.3);
                border: 3px solid rgba(255, 255, 255, 0.2);
                opacity: 0.7;
            ">
                YELLOW
            </div>
            """, unsafe_allow_html=True)
    
    with col4:
        green_eligible = cr_data['green']['time_eligibility'].iloc[0] if not cr_data['green'].empty else None
        if green_eligible is not None and not pd.isna(green_eligible):
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #8BC98E, #97D19A);
                color: white;
                border-radius: 50%;
                width: 140px;
                height: 140px;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                margin: auto;
                font-size: 16px;
                font-weight: bold;
                box-shadow: 0 4px 15px rgba(139, 201, 142, 0.6);
                border: 3px solid rgba(255, 255, 255, 0.1);
                transition: transform 0.2s ease;
                opacity: 0.9;
            ">
                GREEN<br>Hour {int(green_eligible)}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #D3D3D3, #A9A9A9);
                color: #666;
                border-radius: 50%;
                width: 140px;
                height: 140px;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                margin: auto;
                font-size: 16px;
                font-weight: bold;
                box-shadow: 0 4px 15px rgba(169, 169, 169, 0.3);
                border: 3px solid rgba(255, 255, 255, 0.2);
                opacity: 0.7;
            ">
                GREEN
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
    
    # Create tabs for each criteria
    tabs = st.tabs(["Chicago Criteria", "TEAM Criteria", "Green Criteria", "Yellow Criteria", "Summary"])
    
    # Chicago Criteria Tab
    with tabs[0]:
        st.subheader("Chicago Criteria Analysis")
        
        # Eligibility timeline at the top
        first_eligible = cr_data['patel']['time_eligibility'].iloc[0] if not cr_data['patel'].empty else None
        fig_patel_elig = plot_eligibility_timeline(patient_data, 'patel_flag', "Chicago", first_eligible)
        st.plotly_chart(fig_patel_elig, use_container_width=True, key="patel_eligibility")
        
        # Component trend plots with thresholds
        st.subheader("Component Trends vs Thresholds")
        patel_figs = plot_patel_components(patient_data)
        
        # Display component plots in a 2-column layout
        col1, col2 = st.columns(2)
        
        component_order = ['avg_map', 'max_sbp', 'min_heart_rate', 'max_heart_rate', 
                          'min_respiratory_rate', 'max_respiratory_rate', 'min_spo2']
        
        for i, component in enumerate(component_order):
            if component in patel_figs:
                if i % 2 == 0:
                    with col1:
                        st.plotly_chart(patel_figs[component], use_container_width=True, key=f"patel_{component}")
                else:
                    with col2:
                        st.plotly_chart(patel_figs[component], use_container_width=True, key=f"patel_{component}")
        
        # Ineligibility reasons
        if first_eligible is None or np.isnan(first_eligible):
            st.warning("Patient was never eligible for Chicago criteria")
            reasons = get_ineligibility_reasons(patient_data, 'patel')
            if reasons:
                st.write("**Reasons for ineligibility:**")
                for reason in reasons[:5]:  # Show top 5 reasons
                    st.write(f"- {reason['flag']}: Failed {reason['failed_hours']} hours ({reason['percentage']:.1f}%)")
    
    # TEAM Criteria Tab
    with tabs[1]:
        st.subheader("TEAM Criteria Analysis")
        
        # Eligibility timeline at the top
        first_eligible = cr_data['team']['time_eligibility'].iloc[0] if not cr_data['team'].empty else None
        fig_team_elig = plot_eligibility_timeline(patient_data, 'team_flag', "TEAM", first_eligible)
        st.plotly_chart(fig_team_elig, use_container_width=True, key="team_eligibility")
        
        # Component trend plots with thresholds
        st.subheader("Component Trends vs Thresholds")
        team_figs = plot_team_components(patient_data)
        
        # Display component plots in a 2-column layout
        col1, col2 = st.columns(2)
        
        component_order = ['max_heart_rate', 'lactate', 'ne_calc_last', 
                          'min_fio2_set', 'max_peep_set', 'max_respiratory_rate']
        
        for i, component in enumerate(component_order):
            if component in team_figs:
                if i % 2 == 0:
                    with col1:
                        st.plotly_chart(team_figs[component], use_container_width=True, key=f"team_{component}")
                else:
                    with col2:
                        st.plotly_chart(team_figs[component], use_container_width=True, key=f"team_{component}")
        
        # Ineligibility reasons
        if first_eligible is None or np.isnan(first_eligible):
            st.warning("Patient was never eligible for TEAM criteria")
            reasons = get_ineligibility_reasons(patient_data, 'team')
            if reasons:
                st.write("**Reasons for ineligibility:**")
                for reason in reasons[:5]:
                    st.write(f"- {reason['flag']}: Failed {reason['failed_hours']} hours ({reason['percentage']:.1f}%)")
    
    # Green Criteria Tab
    with tabs[2]:
        st.subheader("Green (Consensus) Criteria Analysis")
        
        # Eligibility timeline at the top
        if 'all_green_no_red' in patient_data.columns:
            first_eligible = cr_data['green']['time_eligibility'].iloc[0] if not cr_data['green'].empty else None
            fig_green_elig = plot_eligibility_timeline(patient_data, 'all_green_no_red', "Green", first_eligible)
            st.plotly_chart(fig_green_elig, use_container_width=True, key="green_eligibility")
            
            # Component trend plots with thresholds
            st.subheader("Component Trends vs Thresholds")
            green_figs = plot_green_components(patient_data)
            
            # Display component plots in a 2-column layout
            col1, col2 = st.columns(2)
            
            component_order = ['min_spo2', 'avg_map', 'ne_calc_last', 'max_heart_rate',
                              'min_heart_rate', 'min_fio2_set', 'max_respiratory_rate', 
                              'min_peep_set', 'lactate']
            
            for i, component in enumerate(component_order):
                if component in green_figs:
                    if i % 2 == 0:
                        with col1:
                            st.plotly_chart(green_figs[component], use_container_width=True, key=f"green_{component}")
                    else:
                        with col2:
                            st.plotly_chart(green_figs[component], use_container_width=True, key=f"green_{component}")
            
            if first_eligible is None or np.isnan(first_eligible):
                st.warning("Patient was never eligible for Green criteria")
                # Show red flags present
                red_flag_cols = [col for col in patient_data.columns if 'red' in col and col.endswith('_flag')]
                if red_flag_cols:
                    st.write("**Red flags present:**")
                    for col in red_flag_cols:
                        if (patient_data[col] == 1).any():
                            hours = (patient_data[col] == 1).sum()
                            st.write(f"- {col}: {hours} hours")
            else:
                st.success(f"Patient became eligible at hour {int(first_eligible)}")
    
    # Yellow Criteria Tab
    with tabs[3]:
        st.subheader("Yellow (Consensus) Criteria Analysis")
        
        # Eligibility timeline at the top
        if 'any_yellow_or_green_no_red' in patient_data.columns:
            first_eligible = cr_data['yellow']['time_eligibility'].iloc[0] if not cr_data['yellow'].empty else None
            fig_yellow_elig = plot_eligibility_timeline(patient_data, 'any_yellow_or_green_no_red', "Yellow", first_eligible)
            st.plotly_chart(fig_yellow_elig, use_container_width=True, key="yellow_eligibility")
            
            # Component trend plots (same as green, since yellow allows green + yellow flags)
            st.subheader("Component Trends vs Thresholds")
            yellow_figs = plot_green_components(patient_data)  # Reuse green components for yellow
            
            # Display component plots in a 2-column layout
            col1, col2 = st.columns(2)
            
            component_order = ['min_spo2', 'avg_map', 'ne_calc_last', 'max_heart_rate',
                              'min_heart_rate', 'min_fio2_set', 'max_respiratory_rate', 
                              'min_peep_set', 'lactate']
            
            for i, component in enumerate(component_order):
                if component in yellow_figs:
                    if i % 2 == 0:
                        with col1:
                            st.plotly_chart(yellow_figs[component], use_container_width=True, key=f"yellow_{component}")
                    else:
                        with col2:
                            st.plotly_chart(yellow_figs[component], use_container_width=True, key=f"yellow_{component}")
            
            if first_eligible is None or np.isnan(first_eligible):
                st.warning("Patient was never eligible for Yellow criteria")
            else:
                st.success(f"Patient became eligible at hour {int(first_eligible)}")
    
    # Summary Tab
    with tabs[4]:
        st.subheader("Summary")
        
        # Create summary table
        summary_data = []
        for criteria, cr_df in cr_data.items():
            if not cr_df.empty:
                row = cr_df.iloc[0]
                summary_data.append({
                    'Criteria': criteria.upper(),
                    'Ever Eligible': 'Yes' if not pd.isna(row['time_eligibility']) else 'No',
                    'First Eligible Hour': int(row['time_eligibility']) if not pd.isna(row['time_eligibility']) else 'N/A',
                    'Outcome': 'Eligible' if row['outcome'] == 1 else ('Death' if row['outcome'] == 2 else 'Discharge'),
                    'Event Time': int(row['t_event']) if not pd.isna(row['t_event']) else 'N/A'
                })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)
        
        # Download button for patient data
        st.download_button(
            label="Download Patient Data (CSV)",
            data=patient_data.to_csv(index=False),
            file_name=f"patient_{selected_encounter}_data.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()