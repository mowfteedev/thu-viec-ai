/*
 * xdp_shield.c - eBPF XDP Wire-Speed Packet Filter & Rate Limiter for WireGuard (UDP 51820)
 *
 * Designed for High-Performance Defense against UDP Floods, Handshake Amplification,
 * and DDoS attacks targeting Linux Zero-Trust Gateway endpoints.
 *
 * Compilation:
 *   clang -O2 -target bpf -c xdp_shield.c -o xdp_shield.o
 */

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/in.h>
#include <linux/udp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

#define TARGET_UDP_PORT 51820
#define RATE_LIMIT_WINDOW_NS 1000000000ULL // 1 second window
#define MAX_PACKETS_PER_SEC 2000          // 2000 PPS threshold per source IP
#define MAX_ENTRIES 65536

/* Client rate-limiting state */
struct client_rate_state {
    __u64 last_update_ns;
    __u32 packet_count;
};

/* Statistics counters */
struct stats_counter {
    __u64 rx_packets;
    __u64 rx_bytes;
    __u64 dropped_rate_limit;
    __u64 passed_wireguard;
    __u64 passed_other;
};

/* BPF Map: Rate Limiter State (LRU Hash) */
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, MAX_ENTRIES);
    __type(key, __u32);   // Source IPv4 Address
    __type(value, struct client_rate_state);
} rate_limit_map SEC(".maps");

/* BPF Map: Global Stats Counter (Per-CPU Array) */
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, struct stats_counter);
} stats_map SEC(".maps");

/* Blacklisted Source IPs */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 10000);
    __type(key, __u32);   // Blacklisted IPv4 Address
    __type(value, __u8);  // 1 = Blocked
} blacklist_map SEC(".maps");

SEC("xdp")
int xdp_shield_filter(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;

    __u32 stats_key = 0;
    struct stats_counter *stats = bpf_map_lookup_elem(&stats_map, &stats_key);

    /* 1. Parse Ethernet Header */
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return XDP_PASS;

    /* 2. Parse IPv4 Header */
    struct iphdr *iph = (void *)(eth + 1);
    if ((void *)(iph + 1) > data_end)
        return XDP_PASS;

    if (iph->protocol != IPPROTO_UDP) {
        if (stats) {
            stats->rx_packets++;
            stats->rx_bytes += (data_end - data);
            stats->passed_other++;
        }
        return XDP_PASS;
    }

    /* 3. Parse UDP Header with variable IP header length safety */
    __u32 ip_hlen = iph->ihl * 4;
    if (ip_hlen < sizeof(*iph))
        return XDP_DROP;

    struct udphdr *udph = (void *)iph + ip_hlen;
    if ((void *)(udph + 1) > data_end)
        return XDP_DROP;

    __u32 src_ip = iph->saddr;
    __u16 dst_port = bpf_ntohs(udph->dest);

    if (stats) {
        stats->rx_packets++;
        stats->rx_bytes += (data_end - data);
    }

    /* Check Blacklist Map */
    __u8 *blocked = bpf_map_lookup_elem(&blacklist_map, &src_ip);
    if (blocked && *blocked == 1) {
        if (stats)
            stats->dropped_rate_limit++;
        return XDP_DROP;
    }

    /* Filter for WireGuard Port (51820) */
    if (dst_port == TARGET_UDP_PORT) {
        __u64 now = bpf_ktime_get_ns();
        struct client_rate_state *state = bpf_map_lookup_elem(&rate_limit_map, &src_ip);

        if (!state) {
            struct client_rate_state new_state = {
                .last_update_ns = now,
                .packet_count = 1,
            };
            bpf_map_update_elem(&rate_limit_map, &src_ip, &new_state, BPF_ANY);
            if (stats)
                stats->passed_wireguard++;
            return XDP_PASS;
        }

        /* Check rate window */
        if (now - state->last_update_ns < RATE_LIMIT_WINDOW_NS) {
            if (state->packet_count >= MAX_PACKETS_PER_SEC) {
                if (stats)
                    stats->dropped_rate_limit++;
                return XDP_DROP; // Drop packet exceeding rate limit
            }
            state->packet_count++;
        } else {
            /* Reset window */
            state->last_update_ns = now;
            state->packet_count = 1;
        }

        if (stats)
            stats->passed_wireguard++;
        return XDP_PASS;
    }

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
