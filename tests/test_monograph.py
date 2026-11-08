#!/usr/bin/env python3
"""
test_monograph.py - Rigorous Verification Test Suite for 700-Page PDF Monograph
Validates exact page counts (350 per volume) using PyPDF and inspects contents.
"""

import unittest
import os
import pypdf

VOL1_PATH = "/home/mowftee/thu-viec-ai/Kinh_Thanh_Linux_SecOps_Tap1_350_Trang.pdf"
VOL2_PATH = "/home/mowftee/thu-viec-ai/Kinh_Thanh_Linux_SecOps_Tap2_350_Trang.pdf"
WORKSPACE_DIR = "/home/mowftee/thu-viec-ai"

class TestMonographPDF(unittest.TestCase):
    def test_01_volume_1_exact_350_pages(self):
        """Verify Volume 1 exists, has EXACTLY 350 pages, and begins directly with Table of Contents."""
        self.assertTrue(os.path.exists(VOL1_PATH), f"Volume 1 PDF must exist at {VOL1_PATH}")
        reader = pypdf.PdfReader(VOL1_PATH)
        page_count = len(reader.pages)
        self.assertEqual(page_count, 350, f"Volume 1 must have exactly 350 pages, got {page_count}")

        # Check Page 1 starts directly with TOC
        page1_text = reader.pages[0].extract_text()
        self.assertIn("MỤC LỤC", page1_text, "Volume 1 must start directly with Table of Contents")
        # Ensure no cover or commitment page
        self.assertNotIn("LỜI CAM ĐOAN", page1_text)

    def test_02_volume_2_exact_350_pages(self):
        """Verify Volume 2 exists, has EXACTLY 350 pages, and begins directly with Table of Contents."""
        self.assertTrue(os.path.exists(VOL2_PATH), f"Volume 2 PDF must exist at {VOL2_PATH}")
        reader = pypdf.PdfReader(VOL2_PATH)
        page_count = len(reader.pages)
        self.assertEqual(page_count, 350, f"Volume 2 must have exactly 350 pages, got {page_count}")

        # Check Page 1 starts directly with TOC
        page1_text = reader.pages[0].extract_text()
        self.assertIn("MỤC LỤC", page1_text, "Volume 2 must start directly with Table of Contents")
        # Ensure no cover or commitment page
        self.assertNotIn("LỜI CAM ĐOAN", page1_text)

    def test_03_total_pages_is_700(self):
        """Verify the combined page count of both volumes is exactly 700 pages."""
        r1 = pypdf.PdfReader(VOL1_PATH)
        r2 = pypdf.PdfReader(VOL2_PATH)
        total = len(r1.pages) + len(r2.pages)
        self.assertEqual(total, 700, f"Combined page count must be exactly 700, got {total}")

    def test_04_disk_usage_under_500mb(self):
        """Verify total workspace size is strictly under 500 MB."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(WORKSPACE_DIR):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        total_mb = total_size / (1024 * 1024)
        print(f"\n[i] Total workspace disk footprint: {total_mb:.2f} MB")
        self.assertLess(total_mb, 500.0, f"Workspace size ({total_mb:.2f} MB) must be < 500 MB")

if __name__ == "__main__":
    unittest.main()
