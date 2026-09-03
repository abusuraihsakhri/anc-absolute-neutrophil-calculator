# Absolute Neutrophil Count (ANC) & Absolute Lymphocyte Count (ALC) Calculator

A pure Python clinical hematology, oncology, and febrile neutropenia risk assessment framework implementing standard CTCAE v5.0 grading:
- **ANC Calculation:** Computes absolute neutrophil count from total WBC and differential counts (Segmented neutrophils + Band forms) or total neutrophil percentage.
- **ALC Calculation & Immunocompromise Screening:** Evaluates absolute lymphocyte count ($\text{ALC} < 1,000\text{ cells/}\mu\text{L}$) to detect lymphopenia and compromised cell-mediated immunity.
- **CTCAE v5.0 Neutropenia Severity Grading:**
  - **Normal:** $\text{ANC} \ge 1,500\text{ cells/}\mu\text{L}$
  - **Grade 1 (Mild):** $\text{ANC } 1,000 - 1,499\text{ cells/}\mu\text{L}$
  - **Grade 2 (Moderate):** $\text{ANC } 500 - 999\text{ cells/}\mu\text{L}$
  - **Grade 3 (Severe):** $\text{ANC } 100 - 499\text{ cells/}\mu\text{L}$
  - **Grade 4 (Life-threatening):** $\text{ANC } < 100\text{ cells/}\mu\text{L}$
- **Febrile Neutropenia Oncologic Emergency Alerts:** Triggered when $\text{ANC} < 500\text{ cells/}\mu\text{L}$ (or expected to fall below 500 within 48h) in the presence of a single oral temperature $\ge 38.3^\circ\text{C}$ ($\ge 101.0^\circ\text{F}$) or sustained $\ge 38.0^\circ\text{C}$ ($\ge 100.4^\circ\text{F}$) for $\ge 1\text{ hour}$.
- **Longitudinal Chemotherapy Nadir Tracking:** Analyzes cycle-over-cycle nadir depth, duration of severe neutropenia, and days to bone marrow recovery.
- **High-Throughput Batch CSV Cohort Processing:** Rapidly classifies hematology panels for oncology day wards and inpatient units.

Requires Python standard library only (zero external runtime dependencies).

---

## Clinical Formulation & Mathematical Logic

### Absolute Neutrophil Count (ANC)
$$\text{ANC (cells/}\mu\text{L)} = \text{WBC (cells/}\mu\text{L)} \times \frac{\% \text{Segmented Neutrophils} + \% \text{Bands}}{100}$$
$$\text{Alternative:} \quad \text{ANC} = \text{WBC} \times \frac{\% \text{Total Neutrophils}}{100}$$

*Note: If WBC is supplied in standard laboratory units ($10^3/\mu\text{L}$ or $10^9/\text{L}$), the engine automatically scales by 1,000.*

### Absolute Lymphocyte Count (ALC)
$$\text{ALC (cells/}\mu\text{L)} = \text{WBC (cells/}\mu\text{L)} \times \frac{\% \text{Lymphocytes}}{100}$$

---

## Features

- **Automatic Unit Ingestion:** Seamlessly handles WBC inputs whether reported in $10^3/\mu\text{L}$ (e.g. 7.5) or absolute count (e.g. 7500).
- **Differential & Aggregate Modes:** Computes ANC directly from segmented + band percentages or combined neutrophil fractions.
- **Oncology Safety Rules:** Instantly flags febrile neutropenia requiring immediate broad-spectrum empiric IV antibiotic therapy (e.g., Cefepime, Meropenem, or Piperacillin-Tazobactam).
- **Batch CSV Processing:** Evaluates large inpatient oncology registries.

---

## Installation & Requirements

- Python 3.10+ (tested on 3.10, 3.11, 3.12)
- Zero external runtime dependencies. `pytest` is optional for running tests.

```bash
git clone https://github.com/abusuraihsakhri/anc-absolute-neutrophil-calculator.git
cd anc-absolute-neutrophil-calculator
```

---

## CLI Usage

### 1. Calculate ANC via Granular Differential
```bash
python cli.py calculate --wbc 7.5 --segs 50 --bands 5
```

### 2. Evaluate Febrile Neutropenia with Temperature
```bash
python cli.py calculate --wbc 1.2 --neutrophils 20 --lymphocytes 45 --temp 38.6
```

### 3. Batch CSV Cohort Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

---

## Python API Quickstart

```python
from anc_calc import evaluate_anc

result = evaluate_anc(
    wbc=1.2,                # 1.2 x 10^3/uL
    neutrophils_percent=25.0, # 25% neutrophils -> ANC = 300 cells/uL
    lymphocytes_percent=40.0,
    temperature_celsius=38.5,
)

print(f"ANC: {result['anc']} cells/uL")
print(f"Neutropenia Grade: {result['neutropenia_grade']}")
print(f"Febrile Neutropenia: {result['febrile_neutropenia']['febrile_neutropenia']}")
print(f"Clinical Alert: {result['febrile_neutropenia']['details']}")
```

---

## Running Tests

Run the test suite using standard `unittest` or `pytest`:

```bash
pytest -v
```

