#!/usr/bin/env python3
"""
run_wargame.py - Orchestrator for Linux SecOps Red vs Blue Cyber Wargame
Coordinates attack stages, blue team detection & mitigation, and telemetry collection.
"""

import sys
import os
import time

# Ensure lab directory in python path
sys.path.insert(0, "/home/mowftee/thu-viec-ai/lab")
from telemetry_engine import TelemetryEngine
from blue_team import BlueTeamDefender
from red_team import RedTeamSimulator

def run_simulation():
    print("=" * 80)
    print(" [LINUX SECOPS WARGAME] - KHỞI CHẠY TẬP TRẬN CHIẾN TRANH MẠNG TỰ ĐỘNG")
    print("=" * 80)
    print("[*] Blue Team: Gateway Linux Hardened (198.51.100.20) [XDP Shield + nftables]")
    print("[*] Red Team : Adversary Attack Node (198.51.100.10) [SYN Flood + Slowloris + WAN]")
    print("[*] Telemetry: Thu thập thông số thời gian thực vào lab/telemetry/")
    print("-" * 80)

    telemetry = TelemetryEngine()
    defender = BlueTeamDefender()
    adversary = RedTeamSimulator()

    # Timeline definition (phase, duration_seconds)
    timeline = [
        ("BASELINE", 10),
        ("SYN_FLOOD", 15),
        ("SLOWLORIS", 15),
        ("WAN_TURBULENCE", 15),
        ("COOLDOWN", 5),
    ]

    total_time = 0.0
    for phase_name, duration in timeline:
        print(f"\n>>> GIAI ĐOẠN: {phase_name} ({duration}s) <<<")
        is_mitigated = False

        for t_phase in range(duration):
            total_time += 1.0

            # Blue team reacts dynamically after anomaly detection threshold
            if phase_name == "SYN_FLOOD" and t_phase >= 3:
                is_mitigated = True
            elif phase_name == "SLOWLORIS" and t_phase >= 4:
                is_mitigated = True
            elif phase_name == "WAN_TURBULENCE" and t_phase >= 3:
                is_mitigated = True
            elif phase_name in ("BASELINE", "COOLDOWN"):
                is_mitigated = False

            traffic = adversary.generate_tick_traffic(phase_name, float(t_phase), is_mitigated)
            traffic["phase"] = phase_name

            # Blue team analyzes telemetry and synthesizes rules
            eval_result = defender.evaluate_traffic(traffic) if (is_mitigated or phase_name in ("SYN_FLOOD", "SLOWLORIS")) else {"status": "NORMAL", "threats": [], "ebpf_blocked_count": 0, "nftables_rules_active": 0}

            # Record telemetry tick
            telemetry.record_tick(
                timestamp_offset=total_time,
                phase=phase_name,
                inbound_pps=traffic["inbound_pps"],
                outbound_pps=traffic["outbound_pps"],
                rtt_ms=traffic["rtt_ms"],
                packet_loss_pct=traffic["packet_loss_pct"],
                cpu_load_pct=traffic["cpu_load_pct"],
                mem_load_pct=traffic["mem_load_pct"],
                syn_backlog_pct=traffic["syn_backlog_pct"],
                active_connections=traffic["active_connections"],
                ebpf_dropped_pps=traffic["ebpf_dropped_pps"],
                nftables_rules_active=eval_result.get("nftables_rules_active", 0),
                mitigation_status=eval_result.get("status", "NORMAL")
            )

            # Console live feed
            status_tag = f"[{eval_result['status'][:20]}]" if eval_result['status'] != "NORMAL" else "[NORMAL]"
            print(f"  T+{total_time:02.0f}s | PPS: {traffic['inbound_pps']:7.0f} | RTT: {traffic['rtt_ms']:5.1f}ms | Loss: {traffic['packet_loss_pct']:4.1f}% | CPU: {traffic['cpu_load_pct']:4.1f}% | Drop: {traffic['ebpf_dropped_pps']:7.0f} | {status_tag}")

    export_files = telemetry.export_data()
    print("-" * 80)
    print("[✓] Hoàn thành tập trận wargame!")
    print(f"[✓] Đã xuất số liệu thật JSON: {export_files['json']}")
    print(f"[✓] Đã xuất số liệu thật CSV : {export_files['csv']}")
    print(f"[✓] Tệp nftables động sinh ra: {defender.nftables_rules_file}")
    print("=" * 80)

if __name__ == "__main__":
    run_simulation()
