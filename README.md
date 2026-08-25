# ANC — Absolute Neutrophil Count Calculator

A zero-dependency Python tool for calculating Absolute Neutrophil Count (ANC) and Absolute Lymphocyte Count (ALC) from a complete blood count (CBC) differential.

## Formulas

```
ANC = WBC × (Segs% + Bands%) / 100
ANC = WBC × (Neutrophils% / 100)        # when only total neutrophils given
ALC = WBC × Lymphocytes% / 100
```

## Neutropenia Classification

| Grade | ANC Range (cells/µL) | Clinical Significance |
|-------|---------------------|----------------------|
| Normal | ≥ 1500 | No increased infection risk |
| Mild | 1000 – 1499 | Low infection risk |
| Moderate | 500 – 999 | Moderate infection risk |
| Severe | < 500 | High infection risk |

## Febrile Neutropenia

Defined as:
- **ANC < 500 cells/µL** AND
- Single oral temperature **≥ 38.3°C** (101°F), OR
- Sustained temperature **≥ 38.0°C** (100.4°F) for ≥ 1 hour

This is an **oncologic emergency** requiring empiric broad-spectrum antibiotics.

## Immunocompromise Assessment

- **ALC < 1000 cells/µL** → immunocompromised
- ALC 500–999: Mild lymphopenia
- ALC 200–499: Moderate (consider prophylaxis)
- ALC < 200: Severe (PCP prophylaxis recommended)

## Quick Start

### CLI — Single Patient

```bash
# Using differential (segs + bands)
python cli.py calculate --wbc 7.5 --segs 50 --bands 5

# Using total neutrophils
python cli.py calculate --wbc 7.5 --neutrophils 55 --lymphocytes 30

# With temperature for febrile neutropenia screening
python cli.py calculate --wbc 2.0 --neutrophils 10 --temp 39.0
```

### CLI — Batch Processing

```bash
python cli.py batch -i patients.csv -o results.csv
```

Input CSV columns: `wbc`, `neutrophils_percent` (or `segs_percent` + `bands_percent`), optionally `lymphocytes_percent`, `temperature_celsius`, `sustained_fever`.

### Python API

```python
from anc_calc import evaluate_anc

result = evaluate_anc(
    wbc=7.5,
    segs_percent=50,
    bands_percent=5,
    lymphocytes_percent=30,
    temperature_celsius=38.5,
)
print(result["anc"])                  # 4125.0
print(result["neutropenia_grade"])    # "Normal"
print(result["febrile_neutropenia"])  # assessment dict
```

## Running Tests

```bash
python -m pytest test_anc_calc.py -v
```

## License

MIT License.
