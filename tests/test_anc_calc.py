#!/usr/bin/env python3
"""Tests for ANC (Absolute Neutrophil Count) Calculator."""
import json
import os
import tempfile
import unittest

from anc_calc import (
    calculate_anc,
    calculate_alc,
    classify_neutropenia,
    assess_febrile_neutropenia,
    assess_immunocompromise,
    evaluate_anc,
    process_batch,
)


class TestCalculateANC(unittest.TestCase):
    """Test ANC calculation formulas."""

    def test_anc_segs_bands_basic(self):
        """ANC = WBC × (Segs% + Bands%) / 100"""
        # WBC 7.5 ×10³/µL, Segs 50%, Bands 5%
        anc = calculate_anc(7.5, segs_percent=50, bands_percent=5)
        self.assertAlmostEqual(anc, 4125.0, places=1)

    def test_anc_neutrophils_percent_basic(self):
        """ANC = WBC × Neutrophils% / 100"""
        anc = calculate_anc(7.5, neutrophils_percent=55)
        self.assertAlmostEqual(anc, 4125.0, places=1)

    def test_anc_segs_only(self):
        """ANC with only segs, no bands."""
        anc = calculate_anc(10.0, segs_percent=60)
        self.assertAlmostEqual(anc, 6000.0, places=1)

    def test_anc_bands_only(self):
        """ANC with only bands, no segs."""
        anc = calculate_anc(10.0, bands_percent=3)
        self.assertAlmostEqual(anc, 300.0, places=1)

    def test_anc_wbc_in_cells(self):
        """Auto-detect WBC in cells/µL when > 100."""
        anc = calculate_anc(7500, neutrophils_percent=55)
        self.assertAlmostEqual(anc, 4125.0, places=1)

    def test_anc_zero_wbc(self):
        """Zero WBC should give zero ANC."""
        anc = calculate_anc(0, neutrophils_percent=50)
        self.assertAlmostEqual(anc, 0.0, places=1)

    def test_anc_100_percent_neutrophils(self):
        """100% neutrophils."""
        anc = calculate_anc(5.0, neutrophils_percent=100)
        self.assertAlmostEqual(anc, 5000.0, places=1)

    def test_anc_negative_wbc_raises(self):
        """Negative WBC should raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_anc(-1.0, neutrophils_percent=50)

    def test_anc_no_params_raises(self):
        """No percentages provided should raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_anc(7.5)

    def test_anc_segs_bands_exceed_100_raises(self):
        """Segs + Bands > 100% should raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_anc(7.5, segs_percent=60, bands_percent=50)

    def test_anc_neutrophils_over_100_raises(self):
        """Neutrophils > 100% should raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_anc(7.5, neutrophils_percent=110)


class TestCalculateALC(unittest.TestCase):
    """Test ALC calculation."""

    def test_alc_basic(self):
        """ALC = WBC × Lymphocytes% / 100"""
        alc = calculate_alc(7.5, 30)
        self.assertAlmostEqual(alc, 2250.0, places=1)

    def test_alc_low_lymphocytes(self):
        alc = calculate_alc(5.0, 10)
        self.assertAlmostEqual(alc, 500.0, places=1)

    def test_alc_wbc_in_cells(self):
        alc = calculate_alc(7500, 30)
        self.assertAlmostEqual(alc, 2250.0, places=1)

    def test_alc_negative_wbc_raises(self):
        with self.assertRaises(ValueError):
            calculate_alc(-1.0, 30)

    def test_alc_invalid_percent_raises(self):
        with self.assertRaises(ValueError):
            calculate_alc(7.5, 110)


class TestClassifyNeutropenia(unittest.TestCase):
    """Test neutropenia classification."""

    def test_normal(self):
        self.assertEqual(classify_neutropenia(2000), "Normal")
        self.assertEqual(classify_neutropenia(1500), "Normal")

    def test_mild(self):
        self.assertEqual(classify_neutropenia(1499), "Mild neutropenia")
        self.assertEqual(classify_neutropenia(1000), "Mild neutropenia")

    def test_moderate(self):
        self.assertEqual(classify_neutropenia(999), "Moderate neutropenia")
        self.assertEqual(classify_neutropenia(500), "Moderate neutropenia")

    def test_severe(self):
        self.assertEqual(classify_neutropenia(499), "Severe neutropenia")
        self.assertEqual(classify_neutropenia(100), "Severe neutropenia")
        self.assertEqual(classify_neutropenia(0), "Severe neutropenia")


class TestFebrileNeutropenia(unittest.TestCase):
    """Test febrile neutropenia assessment."""

    def test_anc_above_500_no_febrile(self):
        """ANC >= 500 cannot have febrile neutropenia."""
        result = assess_febrile_neutropenia(600, temperature_celsius=40.0)
        self.assertFalse(result["febrile_neutropenia"])

    def test_anc_below_500_high_temp(self):
        """ANC < 500 + temp >= 38.3 = febrile neutropenia."""
        result = assess_febrile_neutropenia(400, temperature_celsius=38.5)
        self.assertTrue(result["febrile_neutropenia"])
        self.assertEqual(result["risk_level"], "Critical")

    def test_anc_below_500_sustained_fever(self):
        """ANC < 500 + sustained temp >= 38.0 = febrile neutropenia."""
        result = assess_febrile_neutropenia(300, temperature_celsius=38.1, sustained_fever=True)
        self.assertTrue(result["febrile_neutropenia"])

    def test_anc_below_500_no_temp(self):
        """ANC < 500 but no temperature provided."""
        result = assess_febrile_neutropenia(200)
        self.assertFalse(result["febrile_neutropenia"])
        self.assertEqual(result["risk_level"], "Moderate")

    def test_anc_below_500_low_temp(self):
        """ANC < 500 but temp below threshold."""
        result = assess_febrile_neutropenia(100, temperature_celsius=37.5)
        self.assertFalse(result["febrile_neutropenia"])
        self.assertEqual(result["risk_level"], "High")

    def test_exact_threshold_38_3(self):
        """Exact threshold 38.3°C should trigger."""
        result = assess_febrile_neutropenia(400, temperature_celsius=38.3)
        self.assertTrue(result["febrile_neutropenia"])

    def test_sustained_below_threshold(self):
        """Sustained but below 38.0 should not trigger."""
        result = assess_febrile_neutropenia(300, temperature_celsius=37.9, sustained_fever=True)
        self.assertFalse(result["febrile_neutropenia"])


class TestImmunocompromise(unittest.TestCase):
    """Test immunocompromise assessment."""

    def test_normal_alc(self):
        result = assess_immunocompromise(1500)
        self.assertFalse(result["immunocompromised"])

    def test_mild_lymphopenia(self):
        result = assess_immunocompromise(800)
        self.assertTrue(result["immunocompromised"])
        self.assertEqual(result["severity"], "Mild")

    def test_moderate_lymphopenia(self):
        result = assess_immunocompromise(400)
        self.assertTrue(result["immunocompromised"])
        self.assertEqual(result["severity"], "Moderate")

    def test_severe_lymphopenia(self):
        result = assess_immunocompromise(100)
        self.assertTrue(result["immunocompromised"])
        self.assertEqual(result["severity"], "Severe")

    def test_threshold_1000(self):
        result = assess_immunocompromise(1000)
        self.assertFalse(result["immunocompromised"])
        result2 = assess_immunocompromise(999)
        self.assertTrue(result2["immunocompromised"])


class TestEvaluateANC(unittest.TestCase):
    """Test complete evaluation function."""

    def test_full_evaluation_with_differential(self):
        result = evaluate_anc(wbc=7.5, segs_percent=50, bands_percent=5)
        self.assertAlmostEqual(result["anc"], 4125.0, places=1)
        self.assertEqual(result["neutropenia_grade"], "Normal")

    def test_full_evaluation_with_alc(self):
        result = evaluate_anc(wbc=5.0, neutrophils_percent=40, lymphocytes_percent=15)
        self.assertAlmostEqual(result["anc"], 2000.0, places=1)
        self.assertAlmostEqual(result["alc"], 750.0, places=1)
        self.assertTrue(result["immunocompromise"]["immunocompromised"])

    def test_severe_neutropenia_with_fever(self):
        result = evaluate_anc(
            wbc=2.0, neutrophils_percent=10, temperature_celsius=39.0
        )
        self.assertEqual(result["neutropenia_grade"], "Severe neutropenia")
        self.assertTrue(result["febrile_neutropenia"]["febrile_neutropenia"])


class TestProcessBatch(unittest.TestCase):
    """Test CSV batch processing."""

    def test_batch_basic(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "in.csv")
            out = os.path.join(tmp, "out.csv")
            with open(inp, "w") as f:
                f.write("wbc,neutrophils_percent,lymphocytes_percent\n")
                f.write("7.5,55,30\n")
                f.write("2.0,10,5\n")
                f.write("10.0,70,20\n")
            n = process_batch(inp, out)
            self.assertEqual(n, 3)
            self.assertTrue(os.path.exists(out))
            with open(out) as f:
                content = f.read()
                self.assertIn("anc", content)
                self.assertIn("neutropenia_grade", content)
                self.assertIn("Normal", content)
                self.assertIn("Severe neutropenia", content)

    def test_batch_with_segs_bands(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "in.csv")
            out = os.path.join(tmp, "out.csv")
            with open(inp, "w") as f:
                f.write("wbc,segs_percent,bands_percent\n")
                f.write("8.0,50,5\n")
            n = process_batch(inp, out)
            self.assertEqual(n, 1)

    def test_batch_error_handling(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "in.csv")
            out = os.path.join(tmp, "out.csv")
            with open(inp, "w") as f:
                f.write("wbc,neutrophils_percent\n")
                f.write("invalid,50\n")
            n = process_batch(inp, out)
            self.assertEqual(n, 1)


class TestCLI(unittest.TestCase):
    """Test CLI interface."""

    def test_cli_calculate(self):
        from cli import main
        ret = main(["calculate", "--wbc", "7.5", "--neutrophils", "55"])
        self.assertEqual(ret, 0)

    def test_cli_calculate_with_temp(self):
        from cli import main
        ret = main(["calculate", "--wbc", "2.0", "--neutrophils", "10", "--temp", "39.0"])
        self.assertEqual(ret, 0)

    def test_cli_batch(self):
        from cli import main
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "in.csv")
            out = os.path.join(tmp, "out.csv")
            with open(inp, "w") as f:
                f.write("wbc,neutrophils_percent\n7.5,55\n")
            ret = main(["batch", "-i", inp, "-o", out])
            self.assertEqual(ret, 0)


if __name__ == "__main__":
    unittest.main()
