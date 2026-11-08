#!/usr/bin/env python3
"""
generate_all.py - Master Orchestrator to Publish 700-Page PDF Monograph
Volume 1 (Exactly 350 Pages) & Volume 2 (Exactly 350 Pages)
Verified strictly via PyPDF.
"""

import sys
import os
import time
import pypdf

sys.path.insert(0, "/home/mowftee/thu-viec-ai")
from monograph.builder import build_volume_pdf
from monograph.content_volume1 import generate_pages_v1
from monograph.content_volume2 import generate_pages_v2

OUTPUT_VOL1 = "/home/mowftee/thu-viec-ai/Kinh_Thanh_Linux_SecOps_Tap1_350_Trang.pdf"
OUTPUT_VOL2 = "/home/mowftee/thu-viec-ai/Kinh_Thanh_Linux_SecOps_Tap2_350_Trang.pdf"

def main():
    print("=" * 80)
    print(" [XUẤT BẢN BỘ TOÀN THƯ 700 TRANG PDF] - KINH THÁNH LINUX SECOPS & ARCHITECTURE")
    print("=" * 80)

    start_time = time.time()

    # 1. BUILD VOLUME 1 (350 Pages)
    print("\n[*] Đang biên soạn Tập 1: Linux Kernel, Netfilter, eBPF XDP & WireGuard Noise_IK...")
    toc_v1, pages_v1 = generate_pages_v1()
    print(f"    - Mục lục: 4 trang ({len(toc_v1)} đề mục)")
    print(f"    - Nội dung chuyên sâu: {len(pages_v1)} trang (Đích: 346 trang)")
    assert len(pages_v1) == 346, f"Volume 1 content pages must be 346, got {len(pages_v1)}"

    build_volume_pdf(
        output_filename=OUTPUT_VOL1,
        volume_id=1,
        volume_title="Tập 1: Linux Kernel, Netfilter, eBPF XDP, Curve25519 & WireGuard Noise_IK",
        toc_data=toc_v1,
        pages_data=pages_v1
    )

    # Verify Volume 1 using pypdf
    reader_v1 = pypdf.PdfReader(OUTPUT_VOL1)
    v1_count = len(reader_v1.pages)
    v1_size_mb = os.path.getsize(OUTPUT_VOL1) / (1024 * 1024)
    print(f"[✓] TẬP 1 XUẤT BẢN THÀNH CÔNG: {v1_count} TRANG | Dung lượng: {v1_size_mb:.2f} MB")
    assert v1_count == 350, f"LỖI: Tập 1 yêu cầu đúng 350 trang, thực tế: {v1_count}"

    # 2. BUILD VOLUME 2 (350 Pages)
    print("\n[*] Đang biên soạn Tập 2: PostgreSQL 3NF/BRIN, WebSSH PTY, Red-Blue Wargame & SRE...")
    toc_v2, pages_v2 = generate_pages_v2()
    print(f"    - Mục lục: 4 trang ({len(toc_v2)} đề mục)")
    print(f"    - Nội dung chuyên sâu: {len(pages_v2)} trang (Đích: 346 trang)")
    assert len(pages_v2) == 346, f"Volume 2 content pages must be 346, got {len(pages_v2)}"

    build_volume_pdf(
        output_filename=OUTPUT_VOL2,
        volume_id=2,
        volume_title="Tập 2: PostgreSQL 3NF/BRIN, WebSSH PTY, Tác Chiến Red-Blue Team & SRE Khôi Phục Thảm Họa",
        toc_data=toc_v2,
        pages_data=pages_v2
    )

    # Verify Volume 2 using pypdf
    reader_v2 = pypdf.PdfReader(OUTPUT_VOL2)
    v2_count = len(reader_v2.pages)
    v2_size_mb = os.path.getsize(OUTPUT_VOL2) / (1024 * 1024)
    print(f"[✓] TẬP 2 XUẤT BẢN THÀNH CÔNG: {v2_count} TRANG | Dung lượng: {v2_size_mb:.2f} MB")
    assert v2_count == 350, f"LỖI: Tập 2 yêu cầu đúng 350 trang, thực tế: {v2_count}"

    elapsed = time.time() - start_time
    total_pages = v1_count + v2_count
    total_size_mb = v1_size_mb + v2_size_mb

    print("-" * 80)
    print(" [TỔNG KẾT XÁC THỰC NGHIÊM NGẶT - PYPDF VERIFICATION] ")
    print(f"  - Tập 1: {OUTPUT_VOL1} -> {v1_count} TRANG [ĐẠT CHUẨN]")
    print(f"  - Tập 2: {OUTPUT_VOL2} -> {v2_count} TRANG [ĐẠT CHUẨN]")
    print(f"  - Tổng số trang bộ đôi: {total_pages} TRANG (ĐÚNG 700 TRANG)")
    print(f"  - Tổng dung lượng PDF : {total_size_mb:.2f} MB (< 500 MB)")
    print(f"  - Thời gian biên tập  : {elapsed:.2f} giây")
    print("=" * 80)

if __name__ == "__main__":
    main()
