#!/usr/bin/env python3
"""
CLI for ANC (Absolute Neutrophil Count) Calculator.

Usage:
  python cli.py calculate --wbc 7.5 --segs 50 --bands 5
  python cli.py calculate --wbc 7.5 --neutrophils 55 --lymphocytes 30 --temp 38.5
  python cli.py batch -i input.csv -o results.csv
"""
import argparse
import json
import sys

from anc_calc import evaluate_anc, process_batch


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="anc-calculator",
        description="Absolute Neutrophil Count (ANC) & Absolute Lymphocyte Count (ALC) Calculator",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single calculation
    calc = subparsers.add_parser("calculate", help="Calculate ANC/ALC for a single patient")
    calc.add_argument("--wbc", type=float, required=True, help="WBC count (×10³/µL)")
    calc.add_argument("--segs", type=float, default=None, help="Segmented neutrophils %%")
    calc.add_argument("--bands", type=float, default=None, help="Band neutrophils %%")
    calc.add_argument("--neutrophils", type=float, default=None, help="Total neutrophils %%")
    calc.add_argument("--lymphocytes", type=float, default=None, help="Lymphocytes %%")
    calc.add_argument("--temp", type=float, default=None, help="Temperature in °C")
    calc.add_argument("--sustained-fever", action="store_true", help="Sustained fever >= 1 hour")

    # Batch processing
    batch = subparsers.add_parser("batch", help="Batch process CSV of patient records")
    batch.add_argument("-i", "--input", required=True, help="Input CSV file")
    batch.add_argument("-o", "--output", default="results.csv", help="Output CSV file")

    args = parser.parse_args(argv)

    if args.command == "calculate":
        result = evaluate_anc(
            wbc=args.wbc,
            segs_percent=args.segs,
            bands_percent=args.bands,
            neutrophils_percent=args.neutrophils,
            lymphocytes_percent=args.lymphocytes,
            temperature_celsius=args.temp,
            sustained_fever=args.sustained_fever,
        )
        print(json.dumps(result, indent=2))
        return 0

    elif args.command == "batch":
        n = process_batch(args.input, args.output)
        print(f"Processed {n} records -> {args.output}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
