#!/usr/bin/env python3
"""
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
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple


def anc_from_diff(wbc_x10e9_l: float, seg_pct: float, band_pct: float = 0.0) -> int:
    if wbc_x10e9_l <= 0:
        raise ValueError("WBC must be positive")
    if seg_pct + band_pct > 100:
        raise ValueError("differential percentages cannot exceed 100")
    return int(round(wbc_x10e9_l * 1000.0 * (seg_pct + band_pct) / 100.0))


def ctcae_grade(anc: int, lln: int = 1800) -> int:
    """CTCAE v5 grade; Grade 1 requires ANC below the lab lower limit."""
    if anc >= lln:
        return 0
    if anc >= 1500:
        return 1
    if anc >= 1000:
        return 2
    if anc >= 500:
        return 3
    return 4


def febrile_neutropenia_alert(anc: int, temperature_c: float) -> Dict[str, object]:
    triggered = anc < 500 and temperature_c >= 38.3
    return {
        "febrile_neutropenia": bool(triggered),
        "anc": anc,
        "temperature_c": temperature_c,
        "action": (
            "immediate blood cultures + broad-spectrum empiric antibiotics within 1 h"
            if triggered else "no FN criteria met"
        ),
    }


@dataclass
class CycleSeries:
    name: str
    day_anc: List[Tuple[int, int]] = field(default_factory=list)


@dataclass
class CycleNadirStats:
    cycle: str
    nadir_anc: int
    nadir_day: int
    days_below_500: int
    days_below_1000: int
    recovery_day: Optional[int]


class NadirTracker:
    def __init__(self) -> None:
        self.cycles: List[CycleSeries] = []

    def add_cycle(self, series: CycleSeries) -> None:
        self.cycles.append(series)

    def nadir_stats(self) -> List[CycleNadirStats]:
        stats: List[CycleNadirStats] = []
        for cyc in self.cycles:
            ordered = sorted(cyc.day_anc)
            values = [v for _, v in ordered]
            nadir_value = min(values)
            nadir_day = ordered[values.index(nadir_value)][0]
            below500 = sum(1 for v in values if v < 500)
            below1000 = sum(1 for v in values if v < 1000)
            recovery_day: Optional[int] = next(
                (d for d, v in ordered if d >= nadir_day and v >= 1500), None
            )
            stats.append(CycleNadirStats(
                cycle=cyc.name,
                nadir_anc=nadir_value,
                nadir_day=nadir_day,
                days_below_500=below500,
                days_below_1000=below1000,
                recovery_day=recovery_day,
            ))
        return stats

    def deepening_detected(self, drop_threshold: int = 200) -> Dict[str, object]:
        """Flag successive-cycle nadirs that fall deeper than the prior cycle."""
        stats = self.nadir_stats()
        for prev, curr in zip(stats, stats[1:]):
            drop = prev.nadir_anc - curr.nadir_anc
            if drop >= drop_threshold:
                return {
                    "deepening": True,
                    "detail": (f"nadir fell {drop} cells/mm^3 from "
                               f"{prev.cycle} to {curr.cycle}; marrow exhaustion pattern"),
                }
        return {"deepening": False}

    def cumulative_burden(self) -> Dict[str, float]:
        total_days = sum(len(c.day_anc) for c in self.cycles)
        all_values = [v for c in self.cycles for _, v in c.day_anc]
        if not total_days:
            raise ValueError("no cycles recorded")
        return {
            "total_measurements": total_days,
            "pct_days_below_500": round(100.0 * sum(1 for v in all_values if v < 500) / total_days, 1),
            "pct_days_below_1000": round(100.0 * sum(1 for v in all_values if v < 1000) / total_days, 1),
            "mean_anc": round(sum(all_values) / total_days),
        }


def stratify_management(stats: Sequence[CycleNadirStats],
                        febrile_events: int) -> Dict[str, str]:
    """Feature 5: tiered management recommendation from nadir history."""
    if not stats:
        raise ValueError("need at least one cycle")
    worst_nadir = min(s.nadir_anc for s in stats)
    prolonged = any(s.days_below_500 >= 7 for s in stats)

    if febrile_events >= 1 or worst_nadir < 200 or prolonged:
        tier = "regimen_review"
        note = ("recurrent severe/prolonged neutropenia or FN event; evaluate "
                "regimen change versus secondary prophylaxis")
    elif worst_nadir < 500:
        tier = "gcsf_support_or_dose_reduction"
        note = "add G-CSF secondary prophylaxis or reduce dose 15-25%"
    elif worst_nadir < 1000:
        tier = "monitor_closely"
        note = "continue full dose with twice-weekly CBC around the expected nadir"
    else:
        tier = "continue_full_dose"
        note = "neutropenia within acceptable limits"
    return {"tier": tier, "guidance": note}


def _demo() -> None:
    tracker = NadirTracker()
    tracker.add_cycle(CycleSeries("cycle_1", [
        (1, 4200), (4, 2600), (7, 900), (10, 380), (13, 700), (16, 1900), (21, 3400),
    ]))
    tracker.add_cycle(CycleSeries("cycle_2", [
        (22, 4000), (26, 2100), (29, 650), (32, 240), (36, 560), (40, 1600), (45, 3100),
    ]))

    print({"cycle_2_nadir": tracker.nadir_stats()[1]})
    print(tracker.deepening_detected())
    print(tracker.cumulative_burden())

    print(anc_from_diff(2.1, seg_pct=28, band_pct=12))
    print(ctcae_grade(anc_from_diff(1.2, 30, 8)))
    print(febrile_neutropenia_alert(anc=340, temperature_c=38.6))
    print(stratify_management(tracker.nadir_stats(), febrile_events=0))


if __name__ == "__main__":
    _demo()
