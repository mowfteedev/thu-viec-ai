#!/usr/bin/env python3
"""
socket-sentinel.py - Linux Kernel Socket Monitor & Wildcard Bind Alert Daemon
Audits /proc/net/tcp and /proc/net/tcp6 for rogue wildcard binds (0.0.0.0 / ::)
Part of Production Toolbox for Linux SecOps
"""

import sys
import os
import socket
import struct
import argparse
import json
import time
from typing import List, Dict, Optional, Tuple

TCP_STATES = {
    "01": "TCP_ESTABLISHED",
    "02": "TCP_SYN_SENT",
    "03": "TCP_SYN_RECV",
    "04": "TCP_FIN_WAIT1",
    "05": "TCP_FIN_WAIT2",
    "06": "TCP_TIME_WAIT",
    "07": "TCP_CLOSE",
    "08": "TCP_CLOSE_WAIT",
    "09": "TCP_LAST_ACK",
    "0A": "TCP_LISTEN",
    "0B": "TCP_CLOSING",
}

DEFAULT_WHITELIST_PORTS = {22, 53, 80, 443, 51820}

def decode_ipv4(hex_ip: str) -> str:
    """Decode Linux /proc/net/tcp hex string to standard dotted-decimal IPv4."""
    try:
        raw_bytes = bytes.fromhex(hex_ip)
        # /proc/net/tcp outputs %08X from __be32, reversing byte order on little-endian hosts
        return socket.inet_ntoa(raw_bytes[::-1])
    except Exception:
        return "unknown"

def decode_ipv6(hex_ip: str) -> str:
    """Decode hex string to IPv6 address."""
    try:
        raw_bytes = bytes.fromhex(hex_ip)
        # IPv6 in /proc/net/tcp6 is 4 32-bit words in network order
        words = struct.unpack("<4I", raw_bytes)
        packed = struct.pack(">4I", *words)
        return socket.inet_ntop(socket.AF_INET6, packed)
    except Exception:
        return "unknown"

def decode_port(hex_port: str) -> int:
    """Decode hex port to integer."""
    try:
        return int(hex_port, 16)
    except ValueError:
        return -1

def find_pid_by_inode(target_inode: str) -> Optional[Tuple[int, str]]:
    """Scan /proc/[pid]/fd to map socket inode to PID and process name."""
    if not os.path.exists("/proc"):
        return None
    target_link = f"socket:[{target_inode}]"
    try:
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            pid = int(entry)
            fd_dir = os.path.join("/proc", entry, "fd")
            if not os.path.isdir(fd_dir):
                continue
            try:
                for fd in os.listdir(fd_dir):
                    link_path = os.path.join(fd_dir, fd)
                    try:
                        resolved = os.readlink(link_path)
                        if resolved == target_link:
                            # Read process name
                            comm_path = os.path.join("/proc", entry, "comm")
                            proc_name = "unknown"
                            if os.path.exists(comm_path):
                                with open(comm_path, "r") as f:
                                    proc_name = f.read().strip()
                            return (pid, proc_name)
                    except (OSError, IOError):
                        continue
            except (PermissionError, FileNotFoundError):
                continue
    except Exception:
        pass
    return None

def parse_proc_net_tcp(file_path: str, is_ipv6: bool = False) -> List[Dict]:
    """Parse /proc/net/tcp or /proc/net/tcp6 format."""
    sockets = []
    if not os.path.exists(file_path):
        return sockets

    with open(file_path, "r") as f:
        lines = f.readlines()

    if not lines:
        return sockets

    # Header: sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode
    for line in lines[1:]:
        parts = line.strip().split()
        if len(parts) < 10:
            continue

        local_addr_part = parts[1]
        state_hex = parts[3]
        inode = parts[9]

        if ":" not in local_addr_part:
            continue

        hex_ip, hex_port = local_addr_part.split(":")
        ip = decode_ipv6(hex_ip) if is_ipv6 else decode_ipv4(hex_ip)
        port = decode_port(hex_port)
        state_name = TCP_STATES.get(state_hex, f"STATE_{state_hex}")

        sockets.append({
            "ip": ip,
            "port": port,
            "state": state_name,
            "inode": inode,
            "protocol": "tcp6" if is_ipv6 else "tcp",
        })

    return sockets

def inspect_wildcard_sockets(
    tcp_file: str = "/proc/net/tcp",
    tcp6_file: str = "/proc/net/tcp6",
    whitelist_ports: set = None
) -> Tuple[List[Dict], List[Dict]]:
    """Inspect sockets and categorize into authorized vs rogue wildcard listeners."""
    if whitelist_ports is None:
        whitelist_ports = DEFAULT_WHITELIST_PORTS

    all_sockets = parse_proc_net_tcp(tcp_file, is_ipv6=False)
    if os.path.exists(tcp6_file):
        all_sockets.extend(parse_proc_net_tcp(tcp6_file, is_ipv6=True))

    rogue_listeners = []
    authorized_listeners = []

    for sock in all_sockets:
        if sock["state"] == "TCP_LISTEN":
            is_wildcard = sock["ip"] in ("0.0.0.0", "::")
            if is_wildcard:
                pid_info = find_pid_by_inode(sock["inode"])
                if pid_info:
                    sock["pid"], sock["comm"] = pid_info
                else:
                    sock["pid"], sock["comm"] = None, "unprivileged/hidden"

                if sock["port"] not in whitelist_ports:
                    rogue_listeners.append(sock)
                else:
                    authorized_listeners.append(sock)

    return authorized_listeners, rogue_listeners

def run_scan(args) -> int:
    whitelist = set(map(int, args.whitelist.split(","))) if args.whitelist else DEFAULT_WHITELIST_PORTS
    auth, rogue = inspect_wildcard_sockets(args.tcp_path, args.tcp6_path, whitelist)

    print("=" * 80)
    print(" [SOCKET SENTINEL] - AUDIT BINDING WILDCARD PORT (0.0.0.0 / ::)")
    print("=" * 80)
    print(f"Cổng được phép (Whitelist): {sorted(list(whitelist))}")
    print("-" * 80)
    print(f"[*] Cổng Wildcard Hợp Lệ Đang Mở ({len(auth)}):")
    for s in auth:
        print(f"    - [{s['protocol'].upper()}] {s['ip']}:{s['port']} | Inode: {s['inode']} | PID: {s['pid']} ({s['comm']}) [PASS]")

    if rogue:
        print("-" * 80)
        print(f"[!] CẢNH BÁO NGUY HIỂM: PHÁT HIỆN {len(rogue)} CỔNG LẠ BIND VÀO 0.0.0.0 / :: !")
        for r in rogue:
            print(f"    [ALERT] [{r['protocol'].upper()}] {r['ip']}:{r['port']} | Inode: {r['inode']} | PID: {r['pid']} ({r['comm']})")
        print("=" * 80)
        return 1
    else:
        print("-" * 80)
        print("[✓] TRẠNG THÁI AN TOÀN: Không phát hiện cổng lạ lắng nghe trên 0.0.0.0 / ::")
        print("=" * 80)
        return 0

def run_daemon(args):
    whitelist = set(map(int, args.whitelist.split(","))) if args.whitelist else DEFAULT_WHITELIST_PORTS
    print(f"[+] Khởi động Socket Sentinel Daemon (chu kỳ kiểm tra: {args.interval}s)...")
    try:
        while True:
            _, rogue = inspect_wildcard_sockets(args.tcp_path, args.tcp6_path, whitelist)
            if rogue:
                alert_payload = {
                    "timestamp": time.time(),
                    "event": "ROGUE_WILDCARD_SOCKET_DETECTED",
                    "severity": "CRITICAL",
                    "sockets": rogue
                }
                print(f"[ALERT] {json.dumps(alert_payload)}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[+] Dừng daemon an toàn.")

def main():
    parser = argparse.ArgumentParser(description="Socket Sentinel - Linux SecOps Wildcard Socket Auditor")
    parser.add_argument("--scan", action="store_true", help="Chạy quét một lần và xuất báo cáo")
    parser.add_argument("--daemon", action="store_true", help="Chạy ở chế độ daemon nền")
    parser.add_argument("--interval", type=int, default=5, help="Chu kỳ quét của daemon (giây)")
    parser.add_argument("--whitelist", type=str, default="", help="Danh sách cổng hợp lệ, phân cách bằng dấu phẩy")
    parser.add_argument("--tcp-path", type=str, default="/proc/net/tcp", help="Đường dẫn tệp tcp (dùng cho test/audit)")
    parser.add_argument("--tcp6-path", type=str, default="/proc/net/tcp6", help="Đường dẫn tệp tcp6 (dùng cho test/audit)")
    args = parser.parse_args()

    if args.daemon:
        run_daemon(args)
    else:
        sys.exit(run_scan(args))

if __name__ == "__main__":
    main()
