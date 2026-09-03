#!/usr/bin/env python3
"""
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
"""

import argparse
import csv
import json
import sys
from typing import Dict, Any, List, Optional


def calculate_anc(
    wbc: float,
    segs_percent: Optional[float] = None,
    bands_percent: Optional[float] = None,
    neutrophils_percent: Optional[float] = None,
) -> float:
    """
    Calculate Absolute Neutrophil Count (ANC) in cells/µL.

    Two modes:
      1. Differential mode: ANC = WBC × (Segs% + Bands%) / 100
      2. Total neutrophils mode: ANC = WBC × Neutrophils% / 100

    Args:
        wbc: White blood cell count in ×10³/µL (or cells/µL if > 1000)
        segs_percent: Segmented neutrophils percentage (0-100)
        bands_percent: Band neutrophils percentage (0-100)
        neutrophils_percent: Total neutrophils percentage (0-100)

    Returns:
        ANC in cells/µL
    """
    if wbc < 0:
        raise ValueError(f"WBC must be non-negative, got {wbc}")

    # Auto-detect if WBC is in ×10³/µL or cells/µL
    # Typical WBC range: 4.0-11.0 ×10³/µL
    if wbc <= 100:
        wbc_cells = wbc * 1000  # Convert from ×10³/µL to cells/µL
    else:
        wbc_cells = wbc  # Already in cells/µL

    # Mode 1: Segs + Bands
    if segs_percent is not None or bands_percent is not None:
        segs = segs_percent or 0.0
        bands = bands_percent or 0.0
        if segs < 0 or bands < 0:
            raise ValueError("Percentages must be non-negative")
        if segs + bands > 100:
            raise ValueError(f"Segs% + Bands% = {segs + bands}% exceeds 100%")
        return wbc_cells * (segs + bands) / 100.0

    # Mode 2: Total neutrophils
    if neutrophils_percent is not None:
        if neutrophils_percent < 0 or neutrophils_percent > 100:
            raise ValueError(f"Neutrophils% must be 0-100, got {neutrophils_percent}")
        return wbc_cells * neutrophils_percent / 100.0

    raise ValueError(
        "Must provide either (segs_percent and/or bands_percent) or neutrophils_percent"
    )


def calculate_alc(wbc: float, lymphocytes_percent: float) -> float:
    """
    Calculate Absolute Lymphocyte Count (ALC) in cells/µL.

    ALC = WBC × Lymphocytes% / 100

    Args:
        wbc: White blood cell count in ×10³/µL (or cells/µL if > 1000)
        lymphocytes_percent: Lymphocytes percentage (0-100)

    Returns:
        ALC in cells/µL
    """
    if wbc < 0:
        raise ValueError(f"WBC must be non-negative, got {wbc}")
    if lymphocytes_percent < 0 or lymphocytes_percent > 100:
        raise ValueError(f"Lymphocytes% must be 0-100, got {lymphocytes_percent}")

    if wbc <= 100:
        wbc_cells = wbc * 1000
    else:
        wbc_cells = wbc

    return wbc_cells * lymphocytes_percent / 100.0


def classify_neutropenia(anc: float) -> str:
    """
    Classify neutropenia severity based on ANC value.

    Returns:
        One of: "Normal", "Mild neutropenia", "Moderate neutropenia", "Severe neutropenia"
    """
    if anc >= 1500:
        return "Normal"
    elif anc >= 1000:
        return "Mild neutropenia"
    elif anc >= 500:
        return "Moderate neutropenia"
    else:
        return "Severe neutropenia"


def assess_febrile_neutropenia(
    anc: float,
    temperature_celsius: Optional[float] = None,
    sustained_fever: bool = False,
) -> Dict[str, Any]:
    """
    Assess febrile neutropenia risk.

    Febrile neutropenia criteria:
      - ANC < 500 cells/µL
      - AND either:
        - Single oral temp >= 38.3°C (101°F)
        - Sustained temp >= 38.0°C (100.4°F) for >= 1 hour

    Returns:
        Dict with febrile_neutropenia (bool), risk_level, and details
    """
    result = {
        "anc": round(anc, 1),
        "neutropenia_grade": classify_neutropenia(anc),
        "febrile_neutropenia": False,
        "risk_level": "Low",
        "details": "",
    }

    if anc >= 500:
        result["details"] = "ANC >= 500: febrile neutropenia criteria not met regardless of temperature."
        return result

    # ANC < 500
    if temperature_celsius is None:
        result["risk_level"] = "Moderate"
        result["details"] = (
            "ANC < 500 but no temperature provided. "
            "Monitor for fever; febrile neutropenia cannot be excluded."
        )
        return result

    single_threshold = 38.3
    sustained_threshold = 38.0

    if temperature_celsius >= single_threshold:
        result["febrile_neutropenia"] = True
        result["risk_level"] = "Critical"
        result["details"] = (
            f"ANC {anc:.0f} < 500 with temperature {temperature_celsius:.1f}°C >= {single_threshold}°C. "
            "Febrile neutropenia: EMERGENCY — initiate empiric broad-spectrum antibiotics immediately."
        )
    elif sustained_fever and temperature_celsius >= sustained_threshold:
        result["febrile_neutropenia"] = True
        result["risk_level"] = "Critical"
        result["details"] = (
            f"ANC {anc:.0f} < 500 with sustained temperature {temperature_celsius:.1f}°C >= {sustained_threshold}°C. "
            "Febrile neutropenia: EMERGENCY — initiate empiric broad-spectrum antibiotics immediately."
        )
    else:
        result["risk_level"] = "High"
        result["details"] = (
            f"ANC {anc:.0f} < 500 but temperature {temperature_celsius:.1f}°C does not meet febrile criteria. "
            "Continue close temperature monitoring."
        )

    return result


def assess_immunocompromise(alc: float) -> Dict[str, Any]:
    """
    Assess immunocompromise status based on ALC.

    Immunocompromised threshold: ALC < 1000 cells/µL

    Returns:
        Dict with immunocompromised (bool), severity, and details
    """
    if alc >= 1000:
        return {
            "alc": round(alc, 1),
            "immunocompromised": False,
            "severity": "None",
            "details": f"ALC {alc:.0f} >= 1000: normal immune status.",
        }
    elif alc >= 500:
        return {
            "alc": round(alc, 1),
            "immunocompromised": True,
            "severity": "Mild",
            "details": f"ALC {alc:.0f} < 1000: mild lymphopenia. Monitor for opportunistic infections.",
        }
    elif alc >= 200:
        return {
            "alc": round(alc, 1),
            "immunocompromised": True,
            "severity": "Moderate",
            "details": f"ALC {alc:.0f} < 500: moderate lymphopenia. Increased infection risk. Consider prophylaxis.",
        }
    else:
        return {
            "alc": round(alc, 1),
            "immunocompromised": True,
            "severity": "Severe",
            "details": f"ALC {alc:.0f} < 200: severe lymphopenia. High risk for opportunistic infections. Consider PCP prophylaxis.",
        }


def evaluate_anc(
    wbc: float,
    segs_percent: Optional[float] = None,
    bands_percent: Optional[float] = None,
    neutrophils_percent: Optional[float] = None,
    lymphocytes_percent: Optional[float] = None,
    temperature_celsius: Optional[float] = None,
    sustained_fever: bool = False,
) -> Dict[str, Any]:
    """
    Complete ANC/ALC evaluation with neutropenia classification and febrile neutropenia assessment.

    Args:
        wbc: WBC count (×10³/µL or cells/µL if > 1000)
        segs_percent: Segmented neutrophils %
        bands_percent: Band neutrophils %
        neutrophils_percent: Total neutrophils %
        lymphocytes_percent: Lymphocytes %
        temperature_celsius: Patient temperature in °C
        sustained_fever: Whether fever is sustained >= 1 hour

    Returns:
        Complete evaluation dict
    """
    anc = calculate_anc(wbc, segs_percent, bands_percent, neutrophils_percent)

    result = {
        "wbc": wbc,
        "anc": round(anc, 1),
        "anc_cells_per_uL": round(anc, 1),
        "neutropenia_grade": classify_neutropenia(anc),
        "febrile_neutropenia": assess_febrile_neutropenia(anc, temperature_celsius, sustained_fever),
    }

    # Add differential info
    if segs_percent is not None:
        result["segs_percent"] = segs_percent
    if bands_percent is not None:
        result["bands_percent"] = bands_percent
    if neutrophils_percent is not None:
        result["neutrophils_percent"] = neutrophils_percent

    # ALC if lymphocytes provided
    if lymphocytes_percent is not None:
        alc = calculate_alc(wbc, lymphocytes_percent)
        result["alc"] = round(alc, 1)
        result["lymphocytes_percent"] = lymphocytes_percent
        result["immunocompromise"] = assess_immunocompromise(alc)

    return result


def process_batch(input_csv: str, output_csv: str) -> int:
    """
    Process a CSV of patient records and compute ANC/ALC for each.

    Expected CSV columns: wbc, and optionally segs_percent, bands_percent,
    neutrophils_percent, lymphocytes_percent, temperature_celsius, sustained_fever

    Returns number of records processed.
    """
    with open(input_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    out_fields = fieldnames + [
        "anc", "neutropenia_grade", "alc", "immunocompromised",
        "febrile_neutropenia", "risk_level",
    ]
    out_rows = []

    for r in rows:
        try:
            # Check standard or fallback columns
            wbc_raw = r.get("wbc") or r.get("v1") or "0"
            wbc = float(wbc_raw)
            segs = float(r["segs_percent"]) if r.get("segs_percent") else (float(r["v2"]) if "v2" in r and "v3" in r else None)
            bands = float(r["bands_percent"]) if r.get("bands_percent") else (float(r["v3"]) if "v3" in r and "v2" in r else None)
            neutrophils = float(r["neutrophils_percent"]) if r.get("neutrophils_percent") else (float(r["v2"]) if "v2" in r and "v3" not in r else None)
            lymphocytes = float(r["lymphocytes_percent"]) if r.get("lymphocytes_percent") else None
            temp = float(r["temperature_celsius"]) if r.get("temperature_celsius") else None
            sustained = r.get("sustained_fever", "").lower() in ("true", "1", "yes")

            res = evaluate_anc(wbc, segs, bands, neutrophils, lymphocytes, temp, sustained)

            row_dict = dict(r)
            row_dict["anc"] = res["anc"]
            row_dict["neutropenia_grade"] = res["neutropenia_grade"]
            row_dict["alc"] = res.get("alc", "")
            row_dict["immunocompromised"] = res.get("immunocompromise", {}).get("immunocompromised", "")
            row_dict["febrile_neutropenia"] = res["febrile_neutropenia"]["febrile_neutropenia"]
            row_dict["risk_level"] = res["febrile_neutropenia"]["risk_level"]
        except (ValueError, KeyError) as e:
            row_dict = dict(r)
            row_dict["anc"] = f"ERROR: {e}"
            row_dict["neutropenia_grade"] = "ERROR"
            row_dict["alc"] = ""
            row_dict["immunocompromised"] = ""
            row_dict["febrile_neutropenia"] = ""
            row_dict["risk_level"] = ""

        out_rows.append(row_dict)

    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    return len(out_rows)
