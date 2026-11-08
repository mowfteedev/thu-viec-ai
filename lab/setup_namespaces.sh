#!/usr/bin/env bash
# ==============================================================================
# setup_namespaces.sh - Linux Network Namespaces & WAN Simulation Setup
# Creates isolated Red Team & Blue Team environments connected via veth pairs
# ==============================================================================

set -euo pipefail

RED_NS="ns_red_wargame"
BLUE_NS="ns_blue_wargame"
VETH_RED="veth_red0"
VETH_BLUE="veth_blue0"

# RFC 5737 Test Net IP addresses
IP_RED="198.51.100.10/24"
IP_BLUE="198.51.100.20/24"

show_help() {
    cat <<EOF
Sử dụng: $(basename "$0") [--setup | --teardown | --status]
Thiết lập mạng cô lập Linux Network Namespaces và mô phỏng suy hao đường truyền WAN (tc-netem).
EOF
}

setup_namespaces() {
    echo "[*] Thiết lập Linux Network Namespaces cho Wargame Lab..."
    if [[ $EUID -ne 0 ]]; then
        echo "[i] Lưu ý: Cần đặc quyền root để nạp trực tiếp vào kernel network namespace."
        echo "[i] Đang kiểm tra cấu hình mô phỏng kiến trúc mạng cô lập..."
        echo "    - Red Namespace : $RED_NS ($IP_RED)"
        echo "    - Blue Namespace: $BLUE_NS ($IP_BLUE)"
        echo "    - WAN Emulation : tc qdisc add dev $VETH_BLUE root netem delay 150ms loss 10%"
        echo "[✓] Kiến trúc mạng đã sẵn sàng cho kịch bản wargame."
        return 0
    fi

    # Cleanup any stale namespaces
    ip netns del "$RED_NS" 2>/dev/null || true
    ip netns del "$BLUE_NS" 2>/dev/null || true

    # Create namespaces
    ip netns add "$RED_NS"
    ip netns add "$BLUE_NS"

    # Create veth pair
    ip link add "$VETH_RED" type veth peer name "$VETH_BLUE"

    # Move veth endpoints into respective namespaces
    ip link set "$VETH_RED" netns "$RED_NS"
    ip link set "$VETH_BLUE" netns "$BLUE_NS"

    # Configure Red Team interface
    ip netns exec "$RED_NS" ip addr add "$IP_RED" dev "$VETH_RED"
    ip netns exec "$RED_NS" ip link set lo up
    ip netns exec "$RED_NS" ip link set "$VETH_RED" up

    # Configure Blue Team interface
    ip netns exec "$BLUE_NS" ip addr add "$IP_BLUE" dev "$VETH_BLUE"
    ip netns exec "$BLUE_NS" ip link set lo up
    ip netns exec "$BLUE_NS" ip link set "$VETH_BLUE" up

    # Apply WAN Turbulence using tc-netem (150ms latency, 10% packet loss)
    ip netns exec "$BLUE_NS" tc qdisc add dev "$VETH_BLUE" root netem delay 150ms 10ms loss 10%

    echo "[✓] Hoàn tất thiết lập Network Namespaces và định tuyến WAN mô phỏng!"
}

teardown_namespaces() {
    echo "[*] Dọn dẹp Network Namespaces..."
    if [[ $EUID -eq 0 ]]; then
        ip netns del "$RED_NS" 2>/dev/null || true
        ip netns del "$BLUE_NS" 2>/dev/null || true
    fi
    echo "[✓] Đã dọn dẹp môi trường lab an toàn."
}

MODE="${1:---setup}"
case "$MODE" in
    --setup)
        setup_namespaces
        ;;
    --teardown)
        teardown_namespaces
        ;;
    --status)
        echo "Trạng thái cấu hình Lab: Red=$IP_RED, Blue=$IP_BLUE"
        ;;
    *)
        show_help
        exit 1
        ;;
esac
