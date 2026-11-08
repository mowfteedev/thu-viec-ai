#!/usr/bin/env bash
# ==============================================================================
# harden-linux.sh - 50 Kernel Parameters Hardening per CIS Benchmark Level 2
# Designed for Zero-Trust Production Linux SecOps Environments
# ==============================================================================

set -euo pipefail

CONF_FILE="/etc/sysctl.d/99-cis-hardening.conf"
SCRIPT_NAME=$(basename "$0")

declare -A PARAMETERS=(
    # --- Network Stack: IPv4 Packet Forwarding & Routing ---
    ["net.ipv4.ip_forward"]="0|Vô hiệu hóa chuyển tiếp gói IPv4 tránh biến server thành router ngoài ý muốn"
    ["net.ipv4.conf.all.send_redirects"]="0|Không gửi ICMP redirects ngăn chặn kẻ tấn công định tuyến lại traffic"
    ["net.ipv4.conf.default.send_redirects"]="0|Không gửi ICMP redirects trên các interface mặc định mới tạo"
    ["net.ipv4.conf.all.accept_source_route"]="0|Từ chối gói tin Source Routing (IP loose/strict source route)"
    ["net.ipv4.conf.default.accept_source_route"]="0|Từ chối Source Routing trên default interfaces"
    ["net.ipv4.conf.all.accept_redirects"]="0|Từ chối ICMP redirects ngăn chặn tấn công giả mạo gateway (MITM)"
    ["net.ipv4.conf.default.accept_redirects"]="0|Từ chối ICMP redirects trên default interfaces"
    ["net.ipv4.conf.all.secure_redirects"]="0|Từ chối secure ICMP redirects từ gateway không xác thực"
    ["net.ipv4.conf.default.secure_redirects"]="0|Từ chối secure ICMP redirects trên default interfaces"
    ["net.ipv4.conf.all.log_martians"]="1|Ghi log các gói tin có địa chỉ nguồn giả mạo hoặc bất khả thi (martians)"
    ["net.ipv4.conf.default.log_martians"]="1|Ghi log martians trên default interfaces"
    ["net.ipv4.icmp_echo_ignore_broadcasts"]="1|Bỏ qua ICMP echo broadcast chống tấn công Smurf Amplification"
    ["net.ipv4.icmp_ignore_bogus_error_responses"]="1|Bỏ qua các phản hồi lỗi ICMP giả mạo (bogus error responses)"
    ["net.ipv4.conf.all.rp_filter"]="1|Bật Strict Reverse Path Filtering chống IP spoofing"
    ["net.ipv4.conf.default.rp_filter"]="1|Bật Strict Reverse Path Filtering trên default interfaces"
    ["net.ipv4.tcp_syncookies"]="1|Kích hoạt TCP SYN Cookies bảo vệ kernel khi bị tấn công SYN Flood"
    ["net.ipv4.tcp_rfc1337"]="1|Tuân thủ RFC 1337 chống TIME-WAIT Assassination Hazard trong TCP"
    ["net.ipv4.tcp_timestamps"]="0|Tắt TCP timestamps hạn chế suy đoán uptime hệ thống và rò rỉ clock"

    # --- Network Stack: IPv6 Router Advertisements & Redirection ---
    ["net.ipv6.conf.all.forwarding"]="0|Tắt chuyển tiếp gói tin IPv6 trên tất cả card mạng"
    ["net.ipv6.conf.all.accept_ra"]="0|Từ chối IPv6 Router Advertisements ngăn ngừa rogue RA chiếm default route"
    ["net.ipv6.conf.default.accept_ra"]="0|Từ chối IPv6 Router Advertisements trên default interfaces"
    ["net.ipv6.conf.all.accept_redirects"]="0|Từ chối ICMPv6 redirects ngăn chặn chỉnh sửa bảng routing"
    ["net.ipv6.conf.default.accept_redirects"]="0|Từ chối ICMPv6 redirects trên default interfaces"
    ["net.ipv6.conf.all.accept_source_route"]="0|Từ chối IPv6 source routed packets"
    ["net.ipv6.conf.default.accept_source_route"]="0|Từ chối IPv6 source routed packets trên default interfaces"

    # --- Memory Protection & ASLR ---
    ["kernel.randomize_va_space"]="2|Bật toàn diện ASLR (Address Space Layout Randomization: Stack, VDSO, Heap)"
    ["kernel.kptr_restrict"]="2|Ẩn con trỏ kernel /proc/kallsyms đối với mọi người dùng kể cả root"
    ["kernel.dmesg_restrict"]="1|Giới hạn quyền đọc dmesg/klogctl chỉ dành cho CAP_SYSLOG"
    ["kernel.yama.ptrace_scope"]="2|Hạn chế ptrace: chỉ tiến trình quản trị viên CAP_SYS_PTRACE mới được attach"
    ["kernel.kexec_load_disabled"]="1|Vô hiệu hóa kexec_load ngăn nạp kernel mới trực tiếp từ userland"
    ["kernel.sysrq"]="0|Vô hiệu hóa phím ma thuật Magic SysRq ngăn can thiệp console vật lý"
    ["kernel.unprivileged_bpf_disabled"]="1|Chặn người dùng không có đặc quyền nạp chương trình eBPF"
    ["net.core.bpf_jit_harden"]="2|Gia cố JIT compiler của eBPF (constant blinding) chống JIT Spraying"

    # --- File System Links & Core Dumps ---
    ["fs.protected_hardlinks"]="1|Ngăn chặn tạo hardlink tới file không thuộc sở hữu (chống TOCTOU)"
    ["fs.protected_symlinks"]="1|Ngăn chặn theo vết symlink trong thư mục sticky world-writable (/tmp)"
    ["fs.protected_fifos"]="2|Chặn ghi/mở FIFO trong sticky directory nếu không cùng owner"
    ["fs.protected_regular"]="2|Chặn ghi/mở regular file trong sticky directory nếu không cùng owner"
    ["fs.suid_dumpable"]="0|Ngăn dump core các tiến trình setuid/setgid tránh rò rỉ khóa riêng và mật khẩu"
    ["kernel.core_uses_pid"]="1|Đính kèm PID vào tên tệp core dump để phân tích chính xác sự cố"

    # --- Kernel Panic & Resilience ---
    ["kernel.panic"]="60|Tự động reboot sau 60 giây khi kernel rơi vào trạng thái panic"
    ["kernel.panic_on_oops"]="60|Chuyển trạng thái Oops nghiêm trọng thành Panic và tự reboot sau 60s"

    # --- TCP Stack Hardening & DoS Resilience ---
    ["net.ipv4.tcp_max_syn_backlog"]="4096|Tăng hàng đợi SYN backlog để tiếp nhận kết nối an toàn khi tải cao"
    ["net.core.somaxconn"]="4096|Nâng ngưỡng socket listen backlog cho các service then chốt"
    ["net.ipv4.tcp_fin_timeout"]="15|Giảm thời gian giữ kết nối FIN-WAIT-2 xuống 15s thu hồi socket nhanh"
    ["net.ipv4.tcp_keepalive_time"]="300|Gửi keepalive probe sau 300 giây phát hiện dead connection"
    ["net.ipv4.tcp_keepalive_probes"]="5|Giới hạn tối đa 5 lần thăm dò TCP keepalive"
    ["net.ipv4.tcp_keepalive_intvl"]="15|Khoảng cách giữa các probe keepalive là 15 giây"
    ["vm.mmap_min_addr"]="65536|Thiết lập địa chỉ ảo mmap tối thiểu 64KB chống tấn công Null Pointer Dereference"
    ["kernel.perf_event_paranoid"]="3|Chặn người dùng thường sử dụng perf_event profiling hệ thống"
    ["net.ipv4.conf.all.shared_media"]="0|Tắt gửi chuyển tiếp redirect RFC1620 cho các máy chia sẻ cùng broadcast media"
)

show_help() {
    cat <<EOF
Sử dụng: $SCRIPT_NAME [OPTIONS]
Script kiểm tra và siết 50 thông số kernel Linux theo chuẩn CIS Benchmark Level 2.

Tùy chọn:
  --check        Kiểm tra và đánh giá trạng thái 50 thông số hiện tại của hệ thống.
  --dry-run      Mô phỏng áp dụng, hiển thị chi tiết 50 thông số và giá trị mục tiêu.
  --export FILE  Xuất cấu hình ra tệp sysctl (mặc định: $CONF_FILE hoặc đường dẫn chỉ định).
  --apply        Ghi cấu hình vào hệ thống và nạp sysctl --system (yêu cầu quyền root).
  --help         Hiển thị trợ giúp này.
EOF
}

cmd_dry_run() {
    echo "================================================================================"
    echo " [CIS BENCHMARK LEVEL 2] - DANH SÁCH 50 THÔNG SỐ KERNEL SIẾT CHẶT"
    echo "================================================================================"
    local count=1
    for key in $(printf "%s\n" "${!PARAMETERS[@]}" | sort); do
        local val_desc="${PARAMETERS[$key]}"
        local target_val="${val_desc%%|*}"
        local desc="${val_desc#*|}"
        printf "[%02d] %-42s = %-6s # %s\n" "$count" "$key" "$target_val" "$desc"
        count=$((count + 1))
    done
    echo "--------------------------------------------------------------------------------"
    echo "Tổng cộng: $((count - 1)) thông số đã được định nghĩa đầy đủ."
}

cmd_check() {
    echo "================================================================================"
    echo " [CIS BENCHMARK LEVEL 2] - KIỂM TRA TRẠNG THÁI HIỆN TẠI TRÊN HỆ THỐNG"
    echo "================================================================================"
    local count=1
    local passed=0
    local failed=0
    for key in $(printf "%s\n" "${!PARAMETERS[@]}" | sort); do
        local val_desc="${PARAMETERS[$key]}"
        local target_val="${val_desc%%|*}"
        local current_val
        current_val=$(sysctl -n "$key" 2>/dev/null || echo "N/A")
        
        local status="FAIL"
        if [[ "$current_val" == "$target_val" ]]; then
            status="PASS"
            passed=$((passed + 1))
        else
            failed=$((failed + 1))
        fi
        printf "[%02d] %-40s | Mục tiêu: %-5s | Hiện tại: %-5s | [%s]\n" "$count" "$key" "$target_val" "$current_val" "$status"
        count=$((count + 1))
    done
    echo "--------------------------------------------------------------------------------"
    echo "Kết quả kiểm tra: PASS: $passed / $((count - 1)) | Cần siết: $failed"
}

cmd_export() {
    local target_path="${1:-$CONF_FILE}"
    echo "# Cấu hình 50 thông số Kernel Linux - CIS Benchmark Level 2" > "$target_path"
    echo "# Tự động sinh bởi harden-linux.sh - $(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> "$target_path"
    for key in $(printf "%s\n" "${!PARAMETERS[@]}" | sort); do
        local val_desc="${PARAMETERS[$key]}"
        local target_val="${val_desc%%|*}"
        local desc="${val_desc#*|}"
        echo "# $desc" >> "$target_path"
        echo "$key = $target_val" >> "$target_path"
    done
    echo "[✓] Đã xuất thành công 50 thông số ra: $target_path"
}

cmd_apply() {
    if [[ $EUID -ne 0 ]]; then
        echo "[!] Lỗi: Bạn cần có đặc quyền root để áp dụng sysctl vào hệ thống."
        exit 1
    fi
    cmd_export "$CONF_FILE"
    sysctl --system
    echo "[✓] Đã áp dụng toàn bộ 50 thông số kernel CIS Benchmark Level 2 thành công!"
}

MODE="${1:---dry-run}"
case "$MODE" in
    --dry-run)
        cmd_dry_run
        ;;
    --check)
        cmd_check
        ;;
    --export)
        cmd_export "${2:-/tmp/99-cis-hardening.conf}"
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
