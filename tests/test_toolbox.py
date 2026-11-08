#!/usr/bin/env python3
"""
test_toolbox.py - Verification Test Suite for Production Toolbox
Validates all 6 SecOps tools with strict assertion checks.
"""

import unittest
import os
import subprocess
import shutil

TOOLBOX_DIR = "/home/mowftee/thu-viec-ai/toolbox"

class TestProductionToolbox(unittest.TestCase):
    def test_01_xdp_shield_compilation(self):
        """Verify xdp_shield.c compiles cleanly to ELF64 BPF object with required sections."""
        c_file = os.path.join(TOOLBOX_DIR, "xdp_shield.c")
        o_file = os.path.join(TOOLBOX_DIR, "xdp_shield.o")
        self.assertTrue(os.path.exists(c_file), "xdp_shield.c must exist")

        # Compile
        res = subprocess.run(
            ["clang", "-O2", "-target", "bpf", "-c", c_file, "-o", o_file],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0, f"Compilation failed: {res.stderr}")
        self.assertTrue(os.path.exists(o_file), "xdp_shield.o must exist")

        # Check ELF sections with llvm-objdump or readelf
        res_dump = subprocess.run(["llvm-objdump", "-h", o_file], capture_output=True, text=True)
        self.assertEqual(res_dump.returncode, 0)
        self.assertIn("xdp", res_dump.stdout, "ELF must have 'xdp' section")
        self.assertIn(".maps", res_dump.stdout, "ELF must have '.maps' section")
        self.assertIn("license", res_dump.stdout, "ELF must have 'license' section")

    def test_02_harden_linux_50_params(self):
        """Verify harden-linux.sh defines exactly 50 CIS Benchmark Level 2 kernel parameters."""
        script = os.path.join(TOOLBOX_DIR, "harden-linux.sh")
        self.assertTrue(os.path.exists(script), "harden-linux.sh must exist")

        # Run dry-run
        res = subprocess.run([script, "--dry-run"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Dry-run failed: {res.stderr}")
        self.assertIn("Tổng cộng: 50 thông số", res.stdout, "Must define exactly 50 parameters")

        # Run export to tmp
        tmp_conf = "/tmp/test_cis_verify.conf"
        res_exp = subprocess.run([script, "--export", tmp_conf], capture_output=True, text=True)
        self.assertEqual(res_exp.returncode, 0)
        self.assertTrue(os.path.exists(tmp_conf))
        with open(tmp_conf) as f:
            content = f.read()
        self.assertIn("net.ipv4.ip_forward = 0", content)
        self.assertIn("kernel.randomize_va_space = 2", content)
        self.assertIn("net.ipv4.tcp_syncookies = 1", content)
        os.remove(tmp_conf)

    def test_03_enable_bbr(self):
        """Verify enable-bbr.sh checks kernel version and congestion control algorithms."""
        script = os.path.join(TOOLBOX_DIR, "enable-bbr.sh")
        self.assertTrue(os.path.exists(script), "enable-bbr.sh must exist")

        res = subprocess.run([script, "--check"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Check failed: {res.stderr}")
        self.assertIn("Kernel Release", res.stdout)
        self.assertIn("TCP BBR CHECK", res.stdout)

    def test_04_socket_sentinel(self):
        """Verify socket-sentinel.py parses sockets, decodes hex IP/ports and evaluates rogue listeners."""
        script = os.path.join(TOOLBOX_DIR, "socket-sentinel.py")
        self.assertTrue(os.path.exists(script), "socket-sentinel.py must exist")

        # Run scan mode
        python_bin = "/home/mowftee/thu-viec-ai/.venv/bin/python3"
        res = subprocess.run([python_bin, script, "--scan"], capture_output=True, text=True)
        self.assertIn(res.returncode, [0, 1], "Return code must be 0 (clean) or 1 (alert)")
        self.assertIn("SOCKET SENTINEL", res.stdout)

        # Test hex decoding unit logic
        import importlib.util
        spec = importlib.util.spec_from_file_location("sentinel", script)
        sentinel = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sentinel)
        self.assertEqual(sentinel.decode_ipv4("0100007F"), "127.0.0.1")
        self.assertEqual(sentinel.decode_ipv4("00000000"), "0.0.0.0")
        self.assertEqual(sentinel.decode_port("0016"), 22)
        self.assertEqual(sentinel.decode_port("0050"), 80)
        self.assertEqual(sentinel.decode_port("CA6C"), 51820)

    def test_05_db_vacuum_optimizer(self):
        """Verify db-vacuum-optimizer.sh generates valid recommendations and SQL diagnostics."""
        script = os.path.join(TOOLBOX_DIR, "db-vacuum-optimizer.sh")
        self.assertTrue(os.path.exists(script), "db-vacuum-optimizer.sh must exist")

        # Test recommend mode
        res_rec = subprocess.run([script, "--recommend"], capture_output=True, text=True)
        self.assertEqual(res_rec.returncode, 0)
        self.assertIn("autovacuum_max_workers", res_rec.stdout)
        self.assertIn("autovacuum_vacuum_cost_limit", res_rec.stdout)

        # Test SQL bloat queries
        res_sql = subprocess.run([script, "--check-bloat"], capture_output=True, text=True)
        self.assertEqual(res_sql.returncode, 0)
        self.assertIn("pg_stat_user_tables", res_sql.stdout)
        self.assertIn("dead_tuples", res_sql.stdout)

    def test_06_terminal_monitor(self):
        """Verify terminal-monitor.py renders unicode sparkline dashboard."""
        script = os.path.join(TOOLBOX_DIR, "terminal-monitor.py")
        self.assertTrue(os.path.exists(script), "terminal-monitor.py must exist")

        python_bin = "/home/mowftee/thu-viec-ai/.venv/bin/python3"
        res = subprocess.run([python_bin, script, "--snapshot"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("LINUX SECOPS REAL-TIME WARGAME MONITOR", res.stdout)
        self.assertIn("CPU Load", res.stdout)
        self.assertIn("XDP Drop Rate", res.stdout)

if __name__ == "__main__":
    unittest.main()
