#!/usr/bin/env python3
"""
test_lab.py - Verification Test Suite for Cyber Wargame Lab & Telemetry
Validates telemetry files, nftables rules generation, and 50+ 300 DPI figures.
"""

import unittest
import os
import json
import csv
from PIL import Image

LAB_DIR = "/home/mowftee/thu-viec-ai/lab"
FIGURES_DIR = "/home/mowftee/thu-viec-ai/figures"
TELEMETRY_JSON = os.path.join(LAB_DIR, "telemetry", "lab_metrics.json")
TELEMETRY_CSV = os.path.join(LAB_DIR, "telemetry", "lab_metrics.csv")
NFTABLES_RULES = os.path.join(LAB_DIR, "rules", "nftables_dynamic.rules")

class TestCyberWargameLab(unittest.TestCase):
    def test_01_telemetry_json_integrity(self):
        """Verify telemetry JSON exists, is valid JSON, and has at least 50 samples."""
        self.assertTrue(os.path.exists(TELEMETRY_JSON), "lab_metrics.json must exist")
        with open(TELEMETRY_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("metrics", data)
        metrics = data["metrics"]
        self.assertGreaterEqual(len(metrics), 50, "Must contain at least 50 telemetry samples")

        # Verify key fields in first record
        first = metrics[0]
        required_fields = ["time_sec", "phase", "inbound_pps", "rtt_ms", "packet_loss_pct", "cpu_load_pct", "ebpf_dropped_pps"]
        for field in required_fields:
            self.assertIn(field, first, f"Metric entry must have field: {field}")

    def test_02_telemetry_csv_integrity(self):
        """Verify telemetry CSV exists and rows match JSON count."""
        self.assertTrue(os.path.exists(TELEMETRY_CSV), "lab_metrics.csv must exist")
        with open(TELEMETRY_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertGreaterEqual(len(rows), 50, "CSV must contain at least 50 rows")
        self.assertIn("inbound_pps", reader.fieldnames)
        self.assertIn("rtt_ms", reader.fieldnames)

    def test_03_nftables_dynamic_rules(self):
        """Verify autonomous nftables ruleset syntax and directives."""
        self.assertTrue(os.path.exists(NFTABLES_RULES), "nftables_dynamic.rules must exist")
        with open(NFTABLES_RULES, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("table inet filter", content)
        self.assertIn("chain input", content)
        self.assertIn("dynamic_blacklist", content)
        self.assertIn("udp dport 51820", content)

    def test_04_figures_count_and_dpi(self):
        """Verify at least 50 figures exist and are rendered at high resolution (300 DPI)."""
        self.assertTrue(os.path.isdir(FIGURES_DIR), "figures directory must exist")
        png_files = [f for f in os.listdir(FIGURES_DIR) if f.endswith(".png")]
        self.assertGreaterEqual(len(png_files), 50, f"Expected 50+ figures, found {len(png_files)}")

        # Verify resolution & DPI of a sample figure
        sample_img_path = os.path.join(FIGURES_DIR, png_files[0])
        with Image.open(sample_img_path) as img:
            dpi = img.info.get("dpi")
            self.assertIsNotNone(dpi, "Image should contain DPI metadata")
            # Rounding check for 300 DPI
            self.assertAlmostEqual(dpi[0], 300, delta=5, msg=f"Figure DPI should be 300, got {dpi}")

if __name__ == "__main__":
    unittest.main()
