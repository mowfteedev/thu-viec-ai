# Thư Viện AI - Linux SecOps & Bộ Toàn Thư Kỹ Thuật

Dự án nghiên cứu, thực nghiệm và xuất bản tài liệu chuyên sâu về **Linux Kernel, An ninh mạng (SecOps), eBPF XDP, PostgreSQL và Kiến trúc Hệ thống Phân tán**.

## Mục Lục Dự Án
1. **Toolbox Hệ Thống (`toolbox/`)**:
   - `xdp_shield.c`: Bộ lọc gói tin eBPF XDP chặn DoS/DDoS và rate-limit UDP WireGuard port 51820 wire-speed.
   - `harden-linux.sh`: Script siết 50 thông số kernel theo chuẩn CIS Benchmark Level 2.
   - `enable-bbr.sh`: Script kích hoạt thuật toán điều khiển tắc nghẽn TCP BBR (Bottleneck Bandwidth and RTT).
   - `socket-sentinel.py`: Daemon giám sát `/proc/net/tcp` phát hiện và cảnh báo port lạ mở trên `0.0.0.0`.
   - `db-vacuum-optimizer.sh`: Script tối ưu hóa PostgreSQL Autovacuum chống phình bảng và nghẽn I/O.
   - `terminal-monitor.py`: TUI Dashboard hiển thị sparkline trạng thái lab trên console.

2. **Lab Chiến Tranh Mạng (`lab/`)**:
   - Cụm lab mạng cô lập (Linux Network Namespaces).
   - Kịch bản Red Team: TCP SYN Flood, Slowloris, mô phỏng mạng WAN (tc-netem 150ms delay, 10% packet loss).
   - Kịch bản Blue Team: Tự động phân tích telemetry, cập nhật eBPF Map và sinh luật nftables thời gian thực (< 1s).
   - Bộ telemetry JSON/CSV và hơn 50 biểu đồ trực quan hóa 300 DPI lưu tại `figures/`.

3. **Bộ Toàn Thư 700 Trang PDF Chuyên Sâu**:
   - **Tập 1 (350 Trang)**: *Linux Kernel Internals, Netfilter, eBPF XDP, Curve25519 & WireGuard Noise_IK*.
   - **Tập 2 (350 Trang)**: *PostgreSQL 3NF/BRIN, WebSSH PTY, Tác Chiến Red-Blue Team & SRE Khôi Phục Thảm Họa*.

---
*Tác quyền & Quản lý*: Mowftee Guild | Antigravity Engine
