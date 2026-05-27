#!/usr/bin/env python3
"""
HKP Dashboard — Data Generator
Run this script whenever new Excel files are available to refresh data.json

Usage:
    python3 generate_data.py
"""

import pandas as pd
import numpy as np
import json
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings('ignore')

# ── Config ────────────────────────────────────────────────────────────────────
B1_PATH = '/Users/krit/Desktop/01.EGAT/HKP/04. PI for Claude/Monitor/Block 1 Heat Rate Analysis Complete.xlsx'
B2_PATH = '/Users/krit/Desktop/01.EGAT/HKP/04. PI for Claude/Monitor/Block 2 Heat Rate Analysis Complete.xlsx'
HRSG_DID_PATH = '/Users/krit/Desktop/01.EGAT/HKP/Claude Analysis/Offline Summary/HRSG_DiD_Full_Results.csv'
OUTPUT_PATH = Path(__file__).parent / 'data.json'

MIN_POWER_MW = 400  # Filter: operational rows only

# Outage periods (for annotations)
OUTAGES_B1 = [('2025-06-29', '2025-07-21')]
OUTAGES_B2 = [('2026-04-01', '2026-04-22'), ('2025-04-13', '2025-04-16'), ('2025-11-26', '2025-12-05')]

# ── Helpers ───────────────────────────────────────────────────────────────────
def safe(v):
    """Convert numpy types / NaN to JSON-safe Python types."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return round(float(v), 3)
    return v

def monthly_median(df, col):
    """Return {month: value} dict of monthly medians (operational data only)."""
    s = df.groupby('month')[col].median()
    return {str(k): safe(v) for k, v in s.items()}

def monthly_median_both(b1, b2, col):
    """Return aligned monthly series for B1 and B2."""
    s1 = b1.groupby('month')[col].median()
    s2 = b2.groupby('month')[col].median()
    months = sorted(set(s1.index) | set(s2.index), key=str)
    return {
        'months': [str(m) for m in months],
        'b1':     [safe(s1.get(m)) for m in months],
        'b2':     [safe(s2.get(m)) for m in months],
    }

def pct_series(b1, b2, num_col, denom_col):
    """Monthly median of (num/denom × 100) for both blocks."""
    b1 = b1.copy(); b2 = b2.copy()
    b1['__pct'] = b1[num_col] / b1[denom_col] * 100
    b2['__pct'] = b2[num_col] / b2[denom_col] * 100
    return monthly_median_both(b1, b2, '__pct')

# ── Load Data ─────────────────────────────────────────────────────────────────
print('[1/5] Loading B1 ...')
b1 = pd.read_excel(B1_PATH)
b1['Date'] = pd.to_datetime(b1['Date'])
b1 = b1[b1['GROSS POWER (MW)'] > MIN_POWER_MW].copy()
b1['month'] = b1['Date'].dt.to_period('M')

print('[2/5] Loading B2 ...')
b2 = pd.read_excel(B2_PATH)
b2['Date'] = pd.to_datetime(b2['Date'])
b2 = b2[b2['GROSS POWER (MW)'] > MIN_POWER_MW].copy()
b2['month'] = b2['Date'].dt.to_period('M')

date_min = min(b1['Date'].min(), b2['Date'].min()).strftime('%Y-%m-%d')
date_max = max(b1['Date'].max(), b2['Date'].max()).strftime('%Y-%m-%d')

print(f'    B1: {len(b1):,} rows  |  B2: {len(b2):,} rows')
print(f'    Range: {date_min} → {date_max}')

# ── KPI (latest month, both blocks) ──────────────────────────────────────────
print('[3/5] Computing KPIs ...')
latest_month = b2['month'].max()
b1_latest = b1[b1['month'] == latest_month]
b2_latest = b2[b2['month'] == latest_month]

kpi = {
    'period': str(latest_month),
    'b1': {
        'gross_mw':   safe(b1_latest['GROSS POWER (MW)'].median()),
        'gt_mw':      safe(b1_latest['GT MW'].median()),
        'st_mw':      safe(b1_latest['ST MW'].median()),
        'hr_plant':   safe(b1_latest['Heat_Rate_Compensate'].median()),
        'hr_margin':  safe(b1_latest['Heat_Rate_Margin'].median()),
        'hr_st':      safe(b1_latest['Heat_Rate_ST'].median()),
        'hr_gt':      safe(b1_latest['GAS TURBINE HEAT RATE'].median()),
        'vac':        safe(b1_latest['CONDENSER VACUUM PRESS'].median()),
    },
    'b2': {
        'gross_mw':   safe(b2_latest['GROSS POWER (MW)'].median()),
        'gt_mw':      safe(b2_latest['GT MW'].median()),
        'st_mw':      safe(b2_latest['ST MW'].median()),
        'hr_plant':   safe(b2_latest['Heat_Rate_Compensate'].median()),
        'hr_margin':  safe(b2_latest['Heat_Rate_Margin'].median()),
        'hr_st':      safe(b2_latest['Heat_Rate_ST'].median()),
        'hr_gt':      safe(b2_latest['GAS TURBINE HEAT RATE'].median()),
        'vac':        safe(b2_latest['CONDENSER VACUUM PRESS'].median()),
    },
}

# ── ST Overview ───────────────────────────────────────────────────────────────
print('[4/5] Building ST + HRSG overview data ...')

st = {
    # Heat Rate ST (Heat_Rate_ST) — user-specified column
    'hr_st':            monthly_median_both(b1, b2, 'Heat_Rate_ST'),
    # Plant HR Compensate
    'hr_plant':         monthly_median_both(b1, b2, 'Heat_Rate_Compensate'),
    # HR Margin (negative = better than guarantee)
    'hr_margin':        monthly_median_both(b1, b2, 'Heat_Rate_Margin'),
    # Condenser Vacuum
    'condenser_vac':    monthly_median_both(b1, b2, 'CONDENSER VACUUM PRESS'),
    # ST MW % of Gross Power
    'st_pct_gross':     pct_series(b1, b2, 'ST MW', 'GROSS POWER (MW)'),
    # HP Turbine Inlet Pressure
    'hp_turb_inlet':    monthly_median_both(b1, b2, 'HP TURBINE INLET STEAM PRESS'),
    # HPCV Position
    'hpcv_pos':         monthly_median_both(b1, b2, 'HPCV POSITION'),
}

# ── HRSG Overview ─────────────────────────────────────────────────────────────
hrsg = {
    # HP Drum Pressure
    'hp_drum_press':    monthly_median_both(b1, b2, 'HP DRUM PRESSURE'),
    # HP Steam Pressure (SH outlet)
    'hp_steam_press':   monthly_median_both(b1, b2, 'HP STEAM PRESSURE'),
    # HP Main Steam Pressure (to turbine)
    'hp_main_press':    monthly_median_both(b1, b2, 'HP MAIN STEAM PRESS'),
    # Pressure drop Drum → SH outlet (Dm_SH proxy — resistance inside SH tubes)
    # Positive = Drum is higher than SH outlet (normal direction)
    'dm_sh':            monthly_median_both(
                            b1.assign(__dm=b1['HP DRUM PRESSURE'] - b1['HP STEAM PRESSURE']),
                            b2.assign(__dm=b2['HP DRUM PRESSURE'] - b2['HP STEAM PRESSURE']),
                            '__dm'),
    # Stack Temperature
    'stack_temp':       monthly_median_both(b1, b2, 'STACK TEMP'),
    # GT Exhaust Temperature
    'gt_exhaust_temp':  monthly_median_both(b1, b2, 'GT EXHAUST GAS AVERAGE TEMPERATURE (EXHAUST)'),
    # HP Steam Flow
    'hp_steam_flow':    monthly_median_both(b1, b2, 'HP STEAM FLOW (COMPENSATED)'),
    # FGH 3rd Stage Inlet Flow
    'fgh3_flow':        monthly_median_both(b1, b2, 'GT FUEL GAS HEATER (3RD STAGE) INLET FEED WATER FLOW-1'),
}

# DiD Summary from CSV
did = []
try:
    did_df = pd.read_csv(HRSG_DID_PATH)
    for _, row in did_df.iterrows():
        did.append({k: safe(v) if isinstance(v, (float, int, np.number)) else str(v)
                    for k, v in row.items()})
    print(f'    DiD: {len(did)} rows loaded')
except Exception as e:
    print(f'    DiD CSV not found: {e}')

# ── Assemble + Write ──────────────────────────────────────────────────────────
print('[5/5] Writing data.json ...')

out = {
    'meta': {
        'generated_at':      datetime.now().isoformat(),
        'b1_source':         str(B1_PATH),
        'b2_source':         str(B2_PATH),
        'b1_rows':           len(b1),
        'b2_rows':           len(b2),
        'date_range':        {'from': date_min, 'to': date_max},
        'filter_min_mw':     MIN_POWER_MW,
        'outages_b1':        OUTAGES_B1,
        'outages_b2':        OUTAGES_B2,
    },
    'kpi':  kpi,
    'st':   st,
    'hrsg': hrsg,
    'did':  did,
}

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

size_kb = OUTPUT_PATH.stat().st_size / 1024
print(f'    Done → data.json ({size_kb:.1f} KB)')
print()
print('✅  data.json updated successfully.')
today = datetime.now().strftime('%Y-%m-%d')
commit_cmd = f'git add data.json && git commit -m "data: refresh {today}" && git push'
print(f'   Next: cd to website folder then run: {commit_cmd}')
