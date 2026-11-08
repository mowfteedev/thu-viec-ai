#!/usr/bin/env bash
# ==============================================================================
# db-vacuum-optimizer.sh - PostgreSQL Autovacuum & I/O Throttling Optimizer
# Prevents Table Bloat, Wraparound Freeze & Storage I/O Spikes
# ==============================================================================

set -euo pipefail

SCRIPT_NAME=$(basename "$0")

detect_hardware() {
    CPU_CORES=$(nproc 2>/dev/null || echo 4)
    TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}' || echo 8388608)
    TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1024 / 1024))
}

calc_recommendations() {
    detect_hardware

    # Calculate optimal autovacuum workers: min(8, max(3, CPU / 2))
    WORKERS=$((CPU_CORES / 2))
    if [[ "$WORKERS" -lt 3 ]]; then WORKERS=3; fi
    if [[ "$WORKERS" -gt 8 ]]; then WORKERS=8; fi

    # Maintenance work mem: 5% - 10% of RAM, capped at 2GB
    MAINT_MEM_MB=$((TOTAL_RAM_GB * 1024 * 7 / 100))
    if [[ "$MAINT_MEM_MB" -lt 256 ]]; then MAINT_MEM_MB=256; fi
    if [[ "$MAINT_MEM_MB" -gt 2048 ]]; then MAINT_MEM_MB=2048; fi

    # Cost limit: SSD/NVMe can handle 1000 - 3000 cost points per delay cycle
    COST_LIMIT=$((1000 + (CPU_CORES * 200)))
    if [[ "$COST_LIMIT" -gt 3000 ]]; then COST_LIMIT=3000; fi
}

show_recommend() {
    calc_recommendations
    cat <<EOF
================================================================================
 [POSTGRESQL AUTOVACUUM OPTIMIZER] - CẤU HÌNH ĐỀ XUẤT THEO PHẦN CỨNG
================================================================================
Phát hiện phần cứng:
  - CPU Cores : $CPU_CORES
  - Dung lượng RAM: ~${TOTAL_RAM_GB} GB
--------------------------------------------------------------------------------
Thêm các dòng sau vào postgresql.conf để triệt tiêu tình trạng nghẽn I/O & Bloat:

# --- 1. Autovacuum Concurrency & Workers ---
autovacuum = on
autovacuum_max_workers = $WORKERS
autovacuum_naptime = 15s

# --- 2. Cost Throttling (Chống bão đọc/ghi Disk I/O) ---
# Tăng cost_limit cho NVMe/SSD thay vì mặc định 200 gây kéo dài vacuum lê thê
autovacuum_vacuum_cost_limit = $COST_LIMIT
autovacuum_vacuum_cost_delay = 2ms

# --- 3. Dynamic Thresholds (Kích hoạt sớm trước khi bảng phình to) ---
# Mặc định scale_factor = 0.2 (20%) quá cao cho bảng hàng chục triệu dòng
autovacuum_vacuum_scale_factor = 0.05
autovacuum_vacuum_threshold = 50
autovacuum_analyze_scale_factor = 0.02
autovacuum_analyze_threshold = 50

# --- 4. Bộ nhớ bảo trì và chống Transaction ID Wraparound ---
maintenance_work_mem = ${MAINT_MEM_MB}MB
autovacuum_freeze_max_age = 200000000
vacuum_failsafe_age = 1600000000

# --- 5. Giám sát & Logging tiến trình ---
log_autovacuum_min_duration = 500ms
================================================================================
EOF
}

show_bloat_sql() {
    cat <<'EOF'
-- =============================================================================
-- SQL TRUY VẤN GIÁM SÁT DEAD TUPLES VÀ TỈ LỆ BLOAT TRÊN POSTGRESQL
-- =============================================================================
SELECT
    schemaname,
    relname AS table_name,
    n_live_tup AS live_tuples,
    n_dead_tup AS dead_tuples,
    ROUND(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_tuple_pct,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC
LIMIT 20;

-- Truy vấn chi tiết kích thước bảng và chỉ mục (Physical Disk Footprint)
SELECT
    relname AS object_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
    pg_size_pretty(pg_relation_size(relid)) AS data_size,
    pg_size_pretty(pg_indexes_size(relid)) AS index_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 15;
EOF
}

generate_maintenance_script() {
    cat <<'EOF'
-- Kịch bản Vacuum chủ động an toàn cho các bảng quan trọng (Zero Lock Contention)
SET maintenance_work_mem = '1GB';
SET vacuum_cost_limit = 2000;
SET vacuum_cost_delay = 1;

-- Chạy vacuum analyze song song (Parallel Vacuum trên PostgreSQL 13+)
VACUUM (VERBOSE, ANALYZE, PARALLEL 4);
EOF
}

MODE="${1:---recommend}"
case "$MODE" in
    --recommend)
        show_recommend
        ;;
    --check-bloat)
        show_bloat_sql
        ;;
    --generate-sql)
        generate_maintenance_script
        ;;
    *)
        echo "Sử dụng: $SCRIPT_NAME [--recommend | --check-bloat | --generate-sql]"
        exit 1
        ;;
esac
