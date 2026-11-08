#!/usr/bin/env python3
"""
telemetry_engine.py - High-Resolution Network & SecOps Telemetry Collector
Records real-time metrics during wargame scenarios and persists to JSON/CSV.
"""

import os
import json
import csv
import time
from typing import List, Dict, Any

class TelemetryEngine:
    def __init__(self, output_dir: str = "/home/mowftee/thu-viec-ai/lab/telemetry"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.records: List[Dict[str, Any]] = []

    def record_tick(
        self,
        timestamp_offset: float,
        phase: str,
        inbound_pps: float,
        outbound_pps: float,
        rtt_ms: float,
        packet_loss_pct: float,
        cpu_load_pct: float,
        mem_load_pct: float,
        syn_backlog_pct: float,
        active_connections: int,
        ebpf_dropped_pps: float,
        nftables_rules_active: int,
        mitigation_status: str
    ):
        entry = {
            "time_sec": round(timestamp_offset, 2),
            "phase": phase,
            "inbound_pps": round(inbound_pps, 1),
            "outbound_pps": round(outbound_pps, 1),
            "rtt_ms": round(rtt_ms, 2),
            "packet_loss_pct": round(packet_loss_pct, 2),
            "cpu_load_pct": round(cpu_load_pct, 1),
            "mem_load_pct": round(mem_load_pct, 1),
            "syn_backlog_pct": round(syn_backlog_pct, 1),
            "active_connections": active_connections,
            "ebpf_dropped_pps": round(ebpf_dropped_pps, 1),
            "nftables_rules_active": nftables_rules_active,
            "mitigation_status": mitigation_status
        }
        self.records.append(entry)

    def export_data(self) -> Dict[str, str]:
        json_path = os.path.join(self.output_dir, "lab_metrics.json")
        csv_path = os.path.join(self.output_dir, "lab_metrics.csv")

        # Write JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "experiment": "Linux SecOps Red vs Blue Wargame Telemetry",
                "total_samples": len(self.records),
                "generated_at": time.time(),
                "metrics": self.records
            }, f, indent=2)

        # Write CSV
        if self.records:
            fieldnames = list(self.records[0].keys())
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.records)

        return {"json": json_path, "csv": csv_path}
