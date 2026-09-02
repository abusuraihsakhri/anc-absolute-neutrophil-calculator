# Anc Absolute Neutrophil Calculator

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Absolute Neutrophil Count (ANC) & Absolute Lymphocyte Count (ALC) Calculator.

Formulas:
  ANC = WBC × (Segs% + Bands%) / 100
  ANC = WBC × (Neutrophils% / 100)   (when only total neutrophils given)
  ALC = WBC × Lymphocytes% / 100

Neutropenia classification (CTCAE / clinical):
  Normal:             ANC >= 1500 cells/µL
  Mild neutropenia:   ANC 1000–1499
  Moderate:           ANC 500–999
  Severe:             ANC < 500

Febrile neutropenia: ANC < 500 AND (single temp >= 38.3°C or sustained >= 38.0°C)

Immunocompromised: ALC < 1000 cells/µL

Zero-dependency Python stdlib implementation.
Author: Dr. Abu Suraih Sakhri
License: MIT

Longitudinal ANC enrichment features for anc-absolute-neutrophil-calculator.

Implements the top three items from specifications on standard hematology:

    ANC (cells/mm^3) = WBC [x10^9/L] x 1000 x (segmented% + bands%) / 100
    CTCAE v5 neutropenia: G1 LLN-1500, G2 1000-<1500,
                          G3 500-<1000, G4 < 500 cells/mm^3
    Febrile neutropenia: ANC < 500 AND temperature >= 38.3 C

1. Longitudinal trend tracking per chemotherapy cycle: nadir depth/date,
   duration below 500 and 1000, recovery day, cumulative neutropenia burden,
   and cycle-over-cycle nadir deepening (bone-marrow exhaustion signal).
2. CTCAE grading with febrile-neutropenia alerting.
3. Risk stratification into dose-continuation vs G-CSF support vs
   dose-reduction vs regimen-change tiers.

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`CycleSeries`** — dedicated module for cycle series evaluation and state verification.
- **`CycleNadirStats`** — dedicated module for cycle nadir stats evaluation and state verification.
- **`NadirTracker`** — dedicated module for nadir tracker evaluation and state verification.

---

## 📐 Mathematical Formulation & Logic

```text
  Formulas:
  Calculate Absolute Neutrophil Count (ANC) in cells/µL.
  Calculate Absolute Lymphocyte Count (ALC) in cells/µL.
  anc = calculate_anc(wbc, segs_percent, bands_percent, neutrophils_percent)
  alc = calculate_alc(wbc, lymphocytes_percent)
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --wbc <value> --segs <value> --bands <value> --neutrophils <value>
```

### Parameter Reference
- `--wbc`: Specifies input measurement or parameter value.
- `--segs`: Specifies input measurement or parameter value.
- `--bands`: Specifies input measurement or parameter value.
- `--neutrophils`: Specifies input measurement or parameter value.
- `--lymphocytes`: Specifies input measurement or parameter value.
- `--temp`: Specifies input measurement or parameter value.
- `--sustained-fever`: Specifies input measurement or parameter value.
- `--input`: Specifies input measurement or parameter value.
- `--output`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Parameter / observation metric | Required |
| `v1` | Parameter / observation metric | Required |
| `v2` | Parameter / observation metric | Required |
| `v3` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t anc-absolute-neutrophil-calculator .
docker run -p 8000:8000 anc-absolute-neutrophil-calculator
```
