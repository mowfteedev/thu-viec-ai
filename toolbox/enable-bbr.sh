#!/usr/bin/env bash
# ==============================================================================
# enable-bbr.sh - Enable TCP BBR Congestion Control & FQ Pacing
# Designed for High-Throughput, Low-Latency Linux Zero-Trust Operations
# ==============================================================================

set -euo pipefail

SYSCTL_BBR_CONF="/etc/sysctl.d/98-tcp-bbr.conf"
SCRIPT_NAME=$(basename "$0")

show_help() {
    cat <<EOF
Sử dụng: $SCRIPT_NAME [OPTIONS]
Script kiểm tra, nạp module kernel và kích hoạt thuật toán TCP BBR (Bottleneck Bandwidth and RTT).

Tùy chọn:
  --check      Kiểm tra hỗ trợ BBR, module kernel và trạng thái TCP hiện tại.
  --verify     Kiểm tra chi tiết thông số sysctl và socket pacing qua ss.
  --apply      Áp dụng BBR và lưu cố định vào $SYSCTL_BBR_CONF (yêu cầu root).
  --help       Hiển thị trợ giúp này.
EOF
}

check_kernel_support() {
    local kver
    kver=$(uname -r | cut -d. -f1,2)
    local kmajor=${kver%.*}
    local kminor=${kver#*.}

    if [[ "$kmajor" -lt 4 ]] || [[ "$kmajor" -eq 4 && "$kminor" -lt 9 ]]; then
        echo "[!] Cảnh báo: Kernel hiện tại $(uname -r) < 4.9. BBR yêu cầu kernel >= 4.9."
        return 1
    fi
    return 0
}

cmd_check() {
    echo "================================================================================"
    echo " [TCP BBR CHECK] - KIỂM TRA TRẠNG THÁI HỆ THỐNG VÀ THUẬT TOÁN TẮC NGHẼN"
    echo "================================================================================"
    echo "Kernel Release: $(uname -r)"
    if check_kernel_support; then
        echo "[✓] Phiên bản Kernel đạt yêu cầu (>= 4.9)."
    fi

    local current_qdisc current_cc available_cc
    current_qdisc=$(sysctl -n net.core.default_qdisc 2>/dev/null || echo "unknown")
    current_cc=$(sysctl -n net.ipv4.tcp_congestion_control 2>/dev/null || echo "unknown")
    available_cc=$(sysctl -n net.ipv4.tcp_available_congestion_control 2>/dev/null || echo "unknown")

    echo "Default Queue Discipline (net.core.default_qdisc): $current_qdisc"
    echo "Current Congestion Control (net.ipv4.tcp_congestion_control): $current_cc"
    echo "Available Congestion Control algorithms: $available_cc"

    if lsmod 2>/dev/null | grep -q "tcp_bbr"; then
        echo "[✓] Module kernel tcp_bbr: ĐÃ NẠP (loaded)"
    elif grep -q "bbr" /lib/modules/"$(uname -r)"/modules.builtin 2>/dev/null; then
        echo "[✓] Module kernel tcp_bbr: BUILT-IN TRONG KERNEL"
    else
        echo "[-] Module kernel tcp_bbr: Chưa nạp hoặc chưa kiểm tra được"
    fi

    if [[ "$current_cc" == "bbr" ]]; then
        echo "[★] TRẠNG THÁI: TCP BBR ĐANG HOẠT ĐỘNG HOÀN HẢO!"
    else
        echo "[i] TRẠNG THÁI: BBR chưa được kích hoạt làm thuật toán mặc định."
    fi
}

cmd_verify() {
    cmd_check
    echo "--------------------------------------------------------------------------------"
    echo "Kiểm tra socket TCP thực tế (ss -tin summary):"
    if command -v ss &>/dev/null; then
        ss -tin | head -n 15 || true
    fi
}

cmd_apply() {
    if [[ $EUID -ne 0 ]]; then
        echo "[!] Lỗi: Bạn cần có đặc quyền root để thay đổi cấu hình sysctl."
        exit 1
    fi

    echo "[*] Nạp module tcp_bbr..."
    modprobe tcp_bbr 2>/dev/null || true

    echo "[*] Ghi cấu hình BBR cố định vào $SYSCTL_BBR_CONF..."
    cat <<EOF > "$SYSCTL_BBR_CONF"
# TCP BBR Congestion Control & Fair Queueing
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
EOF

    echo "[*] Nạp lại sysctl..."
    sysctl -p "$SYSCTL_BBR_CONF"

    echo "[✓] Áp dụng TCP BBR thành công!"
    cmd_verify
}

MODE="${1:---check}"
case "$MODE" in
    --check)
        cmd_check
        ;;
    --verify)
        cmd_verify
        ;;
    --apply)
        cmd_apply
        ;;
    --help|-h)
        show_help
        ;;
    *)
        echo "[!] Tùy chọn không hợp lệ: $MODE"
        show_help
        exit 1
        ;;
esac
