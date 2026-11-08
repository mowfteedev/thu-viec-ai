#!/usr/bin/env python3
"""
red_team.py - Autonomous Cyber Adversary Simulation Engine
Orchestrates TCP SYN Flood, Slowloris Exhaustion, and WAN Network Storms (150ms delay, 10% loss).
"""

import math
import random
from typing import Dict, Any

class RedTeamSimulator:
    def __init__(self, target_ip: str = "198.51.100.20", attacker_ip: str = "198.51.100.10"):
        self.target_ip = target_ip
        self.attacker_ip = attacker_ip

    def generate_tick_traffic(self, phase: str, t_in_phase: float, is_mitigated: bool) -> Dict[str, Any]:
        """
        Generate realistic traffic characteristics based on current attack campaign.
        """
        base_noise = random.uniform(-0.05, 0.05)

        if phase == "BASELINE":
            # Normal enterprise traffic
            inbound_pps = 350.0 + random.uniform(-20, 30)
            outbound_pps = 320.0 + random.uniform(-15, 25)
            rtt_ms = 4.5 + random.uniform(0.1, 0.8)
            loss_pct = 0.02
            cpu_pct = 6.5 + random.uniform(0.5, 1.5)
            mem_pct = 22.0 + random.uniform(0.1, 0.3)
            syn_backlog = 2.0
            active_conns = 45
            ebpf_drop = 0.0

        elif phase == "SYN_FLOOD":
            # High-rate TCP SYN Flood
            intensity = min(1.0, t_in_phase / 3.0)
            raw_pps = 48000.0 * intensity + random.uniform(-1500, 2000)

            if is_mitigated:
                # Blue team XDP/eBPF drops almost all attack packets at wire-speed (< 100ns per packet)
                inbound_pps = raw_pps
                ebpf_drop = raw_pps * 0.985
                cpu_pct = 14.5 + random.uniform(0.5, 2.0)  # CPU stays low due to XDP drop
                syn_backlog = 8.0 + random.uniform(1.0, 3.0)
                rtt_ms = 5.2 + random.uniform(0.2, 0.9)
                loss_pct = 0.05
                active_conns = 60
                outbound_pps = 380.0
            else:
                # Unmitigated: Kernel TCP stack overwhelmed
                inbound_pps = raw_pps
                ebpf_drop = 0.0
                cpu_pct = min(98.5, 35.0 + intensity * 60.0 + random.uniform(-2, 4))
                syn_backlog = min(100.0, 15.0 + intensity * 82.0)
                rtt_ms = 12.0 + intensity * 180.0
                loss_pct = min(45.0, intensity * 40.0)
                active_conns = int(50 + intensity * 850)
                outbound_pps = 120.0

            mem_pct = 24.0 + intensity * 8.0

        elif phase == "SLOWLORIS":
            # Low-and-slow HTTP header starvation attack
            intensity = min(1.0, t_in_phase / 4.0)
            inbound_pps = 450.0 + intensity * 120.0  # PPS is deceivingly low
            outbound_pps = 280.0
            ebpf_drop = 0.0

            if is_mitigated:
                # Blue team closes slow connections & rate-limits source
                active_conns = 55
                cpu_pct = 8.0 + random.uniform(0.2, 1.0)
                syn_backlog = 3.0
                rtt_ms = 6.0 + random.uniform(0.1, 0.5)
                loss_pct = 0.01
            else:
                active_conns = int(50 + intensity * 450) # Connection pool exhausted
                cpu_pct = 15.0 + intensity * 18.0
                syn_backlog = 12.0 + intensity * 35.0
                rtt_ms = 8.0 + intensity * 95.0
                loss_pct = intensity * 5.0

            mem_pct = 25.0 + intensity * 15.0

        elif phase == "WAN_TURBULENCE":
            # WAN Network Turbulence with tc-netem: 150ms delay, 10% packet loss
            inbound_pps = 2800.0 + random.uniform(-200, 300)
            outbound_pps = 2600.0 + random.uniform(-180, 250)
            rtt_ms = 150.0 + random.uniform(-8.0, 15.0)  # Emulated 150ms WAN latency
            loss_pct = 10.0 + random.uniform(-0.8, 1.2)   # Emulated 10% loss
            cpu_pct = 18.5 + random.uniform(1.0, 3.0)
            mem_pct = 28.0 + random.uniform(0.2, 0.5)
            syn_backlog = 10.0
            active_conns = 120
            ebpf_drop = 450.0 if is_mitigated else 0.0

        else: # RECOVERY / COOLDOWN
            inbound_pps = 380.0 + random.uniform(-20, 20)
            outbound_pps = 350.0 + random.uniform(-15, 20)
            rtt_ms = 4.8 + random.uniform(0.1, 0.4)
            loss_pct = 0.01
            cpu_pct = 7.0 + random.uniform(0.2, 0.8)
            mem_pct = 22.5
            syn_backlog = 2.0
            active_conns = 48
            ebpf_drop = 0.0

        return {
            "attacker_ip": self.attacker_ip,
            "target_ip": self.target_ip,
            "inbound_pps": max(10.0, inbound_pps),
            "outbound_pps": max(10.0, outbound_pps),
            "rtt_ms": max(1.0, rtt_ms),
            "packet_loss_pct": max(0.0, loss_pct),
            "cpu_load_pct": max(1.0, cpu_pct),
            "mem_load_pct": max(5.0, mem_pct),
            "syn_backlog_pct": max(0.0, syn_backlog),
            "active_connections": active_conns,
            "ebpf_dropped_pps": ebpf_drop
        }
