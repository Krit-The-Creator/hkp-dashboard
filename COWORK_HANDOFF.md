# HKP Dashboard — Claude Cowork Handoff Transcript
**Date:** 28 May 2026  
**Project:** HKP Power Plant Performance Dashboard (EGAT — HKP Operation Section)  
**Handoff from:** Claude Code sessions (Website + Analysis)  
**Purpose:** Continue development in Claude Cowork

---

## PROJECT OVERVIEW

Static HTML/JS dashboard for monitoring Block 1 & Block 2 Combined Cycle Power Plant (M701J Gas Turbine).  
**No backend server** — all pages use `fetch('data.json')` client-side.  
**Hosted on GitHub Pages:** `https://krit-the-creator.github.io/hkp-dashboard/`

### Local Working Directory
```
/Users/krit/Desktop/01.EGAT/HKP/Claude Website/
```

### GitHub Repo
```
https://github.com/Krit-The-Creator/hkp-dashboard
```
> ⚠️ `git push` sometimes fails with `remote: fatal error in commit_refs`  
> Workaround: Use GitHub Contents API directly:
> ```bash
> FILE_B64=$(base64 -i "filename.html" | tr -d '\n')
> SHA=$(gh api repos/Krit-The-Creator/hkp-dashboard/contents/filename.html --jq '.sha')
> gh api repos/Krit-The-Creator/hkp-dashboard/contents/filename.html \
>   --method PUT \
>   --field message="deploy: filename" \
>   --field content="$FILE_B64" \
>   --field sha="$SHA"
> ```

---

## FILE STATUS (as of 28 May 2026)

### Local Files — `/Users/krit/Desktop/01.EGAT/HKP/Claude Website/`

| File | Size | Status | Notes |
|------|------|--------|-------|
| `index.html` | 66 KB | ✅ Deployed | Main overview dashboard |
| `gt_prototype.html` | 46 KB | ✅ Deployed | GT cross-section (SVG interactive) |
| `gt.html` | 49 KB | ✅ Deployed | GT live data page (alias of prototype) |
| `gt_dashboard.html` | 53 KB | ❌ NOT deployed | Newer GT dashboard with B1 vs B2 comparison |
| `st_analysis.html` | 77 KB | ✅ Deployed | ST analysis page |
| `hrsg_analysis.html` | 26 KB | ✅ Deployed | HRSG page (BROKEN — charts empty, see issue §5) |
| `anomaly_slides.html` | 88 KB | ✅ Deployed | Anomaly slides |
| `mobile.html` | 34 KB | ✅ Deployed | Mobile dashboard |
| `analysis.html` | 30 KB | ❌ NOT deployed | B2 Heat Rate Root Cause Analysis |
| `analysis_results.html` | 54 KB | ❌ NOT deployed | Full analysis results page |
| `data.json` | 43 KB | ✅ Deployed (old ver) | Local is newer than deployed |
| `generate_data.py` | 10 KB | ✅ On GitHub | Python script to regenerate data.json |
| `refresh.command` | 1 KB | ✅ On GitHub | Shell script to regenerate + push |

### Files Needing Deploy (Priority Order)
1. `analysis.html` — B2 Root Cause page (completed, not uploaded)
2. `data.json` — Local version is newer (43 KB vs deployed 17 KB)
3. `analysis_results.html` — Full results page
4. `gt_dashboard.html` — Newer GT page
5. Update `index.html` sidebar to add link to `analysis.html`

---

## DATA ARCHITECTURE

### data.json Structure
```json
{
  "meta": {
    "generated_at": "...",
    "date_range": "2025-01 to 2026-05",
    "outages_b1": [...],
    "outages_b2": [...]
  },
  "kpi": {
    "heat_rate": { "value": 6171.1, "unit": "kJ/kWh", "trend": "up" },
    "output_mw": { "value": 1422.3, "unit": "MW" },
    "energy_gwh": { "value": 656.9, "unit": "GWh" },
    "fuel_mmscfd": { "value": 6.1, "unit": "MMSCFD" }
  },
  "blocks": {
    "B1_GT": { "status": "running", "output_mw": 477.7, "heat_rate": 8680, "load_pct": 94.8 },
    "B1_ST": { "status": "running", "output_mw": 234.2, "heat_rate": 9167, "load_pct": 91.1 },
    "B2_GT": { "status": "running", "output_mw": 476.3, "heat_rate": 8695, "load_pct": 94.5 },
    "B2_ST": { "status": "derate", "output_mw": 228.6, "heat_rate": 9185, "load_pct": 88.9 }
  },
  "st_analysis": {
    "months": ["2025-08", "2025-09", ...],
    "gross_mw": { "b1": [...], "b2": [...] },
    "gt_hr": { "b1": [...], "b2": [...] },
    "st_hr": { "b1": [...], "b2": [...] },
    "heat_rate_compensate": { "b1": [...], "b2": [...] },
    "condenser_vacuum": { "b1": [...], "b2": [...] },
    "hp_main_steam_dp": { "b1": [...], "b2": [...] }
  },
  "hrsg_analysis": {
    "months": [...],
    "stack_temp": { "b1": [...], "b2": [...] },
    "gt_exhaust_temp": { "b1": [...], "b2": [...] },
    "hrsg_efficiency": { "b1": [...], "b2": [...] }
  },
  "did_summary": [ ...DiD analysis rows... ]
}
```

### Data Generation
```bash
cd "/Users/krit/Desktop/01.EGAT/HKP/Claude Website"
python3 generate_data.py   # reads Excel, writes data.json
```
Source Excel: `Block 1 & 2 Heat Rate Analysis Complete.xlsx`  
Filter applied: `GROSS POWER > 400 MW`

### Auto-refresh Pattern (all pages)
```javascript
fetch("data.json?t=" + Date.now())   // cache-busting
  .then(r => r.json())
  .then(data => renderDashboard(data));
setInterval(loadDashboardData, 10000); // refresh every 10 seconds
```

---

## KEY ANALYSIS FINDINGS

### B2 Heat Rate Root Cause (confirmed)
**Root cause: HP Main Steam Path Restriction** (post CI+ Outage)
- HP Main Steam ΔP: B2 jumped from 593 kPa → 706 kPa after outage
- B1 stayed stable: 607 kPa → 642 kPa
- DiD ST Heat Rate: B2 +52.5 kJ/kWh (post-outage vs pre-outage corrected for B1)

### DiD Decomposition of B2 Degradation
```
Total CC Heat Rate degradation:   +65.7 kJ/kWh
├── HP Steam Path Restriction:    +43.3 kJ/kWh  (66% of total) ← SMOKING GUN
├── Condenser Vacuum Loss:        +17.7 kJ/kWh  (27%)
└── HRSG/GT Contribution:         +4.7 kJ/kWh   (7%)
```

### Monthly Data (embedded in analysis.html)
```javascript
const months = ['ส.ค. 68','ก.ย. 68','ต.ค. 68','พ.ย. 68','ธ.ค. 68',
                'ม.ค. 69','ก.พ. 69','มี.ค. 69','เม.ย. 69','พ.ค. 69'];
// B2 Outage: เม.ย. 69 (indices 8-9 affected)

const stHR_B1 = [9213.0,9224.8,9213.2,9198.9,9165.8,9160.2,9148.5,9157.6,9167.5,9173.9];
const stHR_B2 = [9128.8,9145.2,9152.6,9164.3,9114.5,9111.2,9094.1,9106.1,9183.9,9185.1];
const ccHR_B1 = [6188.7,6201.6,6200.5,6209.4,6170.1,6167.9,6163.0,6164.3,6144.0,6144.8];
const ccHR_B2 = [6198.5,6209.4,6207.5,6213.5,6202.0,6195.8,6184.8,6187.1,6171.8,6163.4];

// HP Main Steam ΔP (kPa): [B1-Pre, B1-Post, B2-Pre, B2-Post]
const dpValues = [607.0, 642.5, 593.2, 705.7];
```

---

## ACTIVE ISSUES

### Issue 1: HRSG Page Charts Empty
**File:** `hrsg_analysis.html`  
**Symptom:** All 8 Chart.js charts empty, KPIs show "—", flow diagram hardcoded  
**Root Cause:** `fetch('data.json')` fails silently when opened as `file://`  
**Fix (Option A — recommended):** Update `generate_data.py` to also write `data_inline.js`:
```python
with open('data_inline.js', 'w') as f:
    f.write(f'window.HKP_DATA = {json.dumps(out, ensure_ascii=False)};')
```
Replace fetch in `hrsg_analysis.html`:
```html
<script src="data_inline.js"></script>
<script>
const data = window.HKP_DATA;
if (data && data.hrsg) initCharts(data.hrsg);
</script>
```

### Issue 2: analysis.html Not Deployed
**File:** `/Users/krit/Desktop/01.EGAT/HKP/Claude Website/analysis.html`  
**Status:** Created locally, NOT on GitHub Pages  
**Action needed:** Upload via GitHub Contents API + add sidebar link in index.html

### Issue 3: data.json Outdated on GitHub
**Local:** 43 KB (updated 27 May 2026)  
**Deployed:** 17 KB (older version)  
**Action needed:** Upload new data.json

---

## PAGES TO BUILD / CONTINUE

### Priority 1 — Deploy Existing Files
1. Upload `analysis.html` to GitHub Pages
2. Upload updated `data.json`
3. Add sidebar link in `index.html` → `analysis.html`

### Priority 2 — Fix HRSG Page
Apply inline data pattern (see Issue 1 above)

### Priority 3 — GT Dashboard Enhancement
`gt_dashboard.html` has B1 vs B2 comparison view — needs:
- Link from main navigation
- Connect to data.json live data
- Mobile responsiveness check

### Priority 4 — Mobile Dashboard
`mobile.html` exists but is from earlier version — needs updating for new data.json schema

### Priority 5 — Graph Viewer Integration (Phase ก, ข, ค)
From IMPLEMENTATION_SPEC in Claude Analysis session:
- Phase ก: Pattern Set Manager (`PatternSetManagerDialog` in `graph_app_qt.py`)
- Phase ข: Export for Web (`ExportForWebDialog`, `_build_data_json()`)
- Phase ค: Live connection between PyQt app and dashboard
Source: `/Users/krit/Desktop/01.EGAT/HKP/Claude Analysis/graph_app_qt.py`

---

## DESIGN SYSTEM

### Dark Theme Colors
```css
--bg-dark: #0f1117
--bg-card: #1a1d2e
--bg-card2: #16192a
--accent-blue: #3b82f6
--accent-green: #10b981
--accent-yellow: #f59e0b
--accent-red: #ef4444
--text-primary: #e2e8f0
--text-muted: #64748b
--border: rgba(255,255,255,0.05)
```

### Thai Month Conversion (used in all pages)
```javascript
function thaiMonth(yyyymm) {
  const names = ['ม.ค.','ก.พ.','มี.ค.','เม.ย.','พ.ค.','มิ.ย.',
                 'ก.ค.','ส.ค.','ก.ย.','ต.ค.','พ.ย.','ธ.ค.'];
  const [y, m] = yyyymm.split('-');
  return names[parseInt(m)-1] + ' ' + (parseInt(y)-2500+2500).toString().slice(-2);
  // e.g. "2025-08" → "ส.ค. 68"
}
```

### Chart.js Config (standard for all pages)
```javascript
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(255,255,255,0.05)';
// CDN: https://cdn.jsdelivr.net/npm/chart.js
// Outage reference line: custom afterDraw plugin
```

---

## GAS TURBINE SVG DIAGRAM

### File: `gt_prototype.html` (deployed as `gt.html`)
Interactive M701J cross-section with:
- Smooth bezier casing (bell mouth inlet, combustor dome, exhaust diffuser)
- JS-generated airfoil blades: 17 compressor stages + 4 turbine stages
- IGV/VIGV highlighted (stages 1-4 compressor)
- Can-annular combustor with flame glow
- 6 clickable hotspots → Chart.js popup trend
- 5 semicircle gauges: RPM, MW, Heat Rate, Pressure Ratio, EGT

### Blade Generation
```javascript
// Compressor: 17 stages, x: 150→490, rx: lerp(14,8,t), ry: lerp(1.8,1.3,t)
// Rotor angle: 52°, Stator angle: -42°, 4 blades/row upper+lower
// Turbine: 4 stages, x: 648→828, rx: lerp(18,22,t), ry: lerp(2.8,3.5,t)
// Colors: stage1 #c05830 → stage4 #783010
function makeBlade(cx, cy, rx, ry, angleDeg, fill, stroke, sw) { ... }
```

---

## RELATED SESSIONS / FILES

### Claude Analysis Session
```
/Users/krit/Desktop/01.EGAT/HKP/Claude Analysis/
├── B2_Heat_Rate_Report/
│   ├── HKP_Performance_Analysis_2025_2026.pdf  (2.2 MB, 8 pages)
│   └── analysis_summary.txt
├── Offline Summary/
│   └── Comprehensive_B1_B2_Comparison_v2.csv   ← source for analysis.html charts
├── PI Tag Templates/                             ← Excel macros for PI data
└── graph_app_qt.py                               ← PyQt Graph Viewer app
```

### Data Filters Applied in Analysis
```python
GROSS POWER > 400 MW
b2['HKP MRS 0322A ENERGY FLOWRATE'] <= 10   # B2 Run A meter exclusion
# Outage exclusions (whole month):
# B1 CI+: 2025-07
# B2 CI+: 2026-04
# B2 BPT Trip: 2025-12
```

---

## QUICK DEPLOY COMMANDS

```bash
# Deploy any file to GitHub Pages
deploy_file() {
  local FILE="$1"
  local NAME=$(basename "$FILE")
  local B64=$(base64 -i "$FILE" | tr -d '\n')
  local SHA=$(gh api "repos/Krit-The-Creator/hkp-dashboard/contents/$NAME" --jq '.sha' 2>/dev/null || echo "")
  if [ -n "$SHA" ]; then
    gh api "repos/Krit-The-Creator/hkp-dashboard/contents/$NAME" \
      --method PUT \
      --field message="deploy: $NAME" \
      --field content="$B64" \
      --field sha="$SHA"
  else
    gh api "repos/Krit-The-Creator/hkp-dashboard/contents/$NAME" \
      --method PUT \
      --field message="add: $NAME" \
      --field content="$B64"
  fi
}

# Usage:
cd "/Users/krit/Desktop/01.EGAT/HKP/Claude Website"
deploy_file "analysis.html"
deploy_file "data.json"
```

---

## IMMEDIATE TODO FOR COWORK SESSION

### Step 1 — Deploy Pending Files
```
[ ] Upload analysis.html to GitHub Pages
[ ] Upload updated data.json (43 KB version)
[ ] Add analysis.html link to index.html sidebar
[ ] Upload updated index.html
```

### Step 2 — Fix HRSG Charts
```
[ ] Update generate_data.py to also write data_inline.js
[ ] Update hrsg_analysis.html to use window.HKP_DATA pattern
[ ] Test locally, then deploy
```

### Step 3 — Navigation Polish
```
[ ] Add "วิเคราะห์" section to sidebar in index.html
[ ] Link: analysis.html (B2 Root Cause)
[ ] Link: analysis_results.html (Full Results)
[ ] Verify all sidebar links work on GitHub Pages
```

### Step 4 — GT Dashboard
```
[ ] Review gt_dashboard.html (B1 vs B2 comparison, 53 KB)
[ ] Decide: replace gt.html or add as separate page
[ ] Connect live data.json fetch
```

### Step 5 (Optional) — Graph Viewer Export
```
[ ] Phase ข in graph_app_qt.py: ExportForWebDialog
[ ] _build_data_json() function → generate data.json from PyQt app
[ ] This would replace the manual Python script workflow
```

---

## CONTACTS / CONTEXT
- **Project:** HKP Combined Cycle Power Plant — EGAT Operation Section
- **Plant:** Block 1 (B1) + Block 2 (B2) — M701J Gas Turbine + Steam Turbine
- **Dashboard URL:** https://krit-the-creator.github.io/hkp-dashboard/
- **Language:** Thai (UI labels in Thai, data in English)
- **Stack:** HTML + CSS + Chart.js (no framework, no build tool)

---
*Generated by Claude Code — 28 May 2026*
