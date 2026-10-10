"""Optimal-parse LZ4 block compressor (small inputs, e.g. sign models).

Dynamic programming over positions (like smallz4): for every position the cheapest way to
encode the rest of the data, choosing between a literal and a match (every useful length of
the matches found via hash chains). Costs follow the LZ4 block format, so the result is
usually a little smaller than LZ4-HC level 12, which gives headroom for fixed-size slots.
"""
import lz4.block

MIN_MATCH, LAST_LITERALS, MFLIMIT, MAX_OFFSET = 4, 5, 12, 65535


def _ext(n):
    """Extra bytes needed to store a length field value n (after the 4-bit nibble)."""
    return 0 if n < 15 else 1 + (n - 15) // 255


def compress(data, max_chain=256):
    n = len(data)
    if n < MFLIMIT + 1:
        return lz4.block.compress(data, store_size=False)
    # --- match finder: for each position, (length, offset) candidates
    head, prev = {}, [-1] * n
    matches = [None] * n
    limit = n - LAST_LITERALS
    for i in range(n - 3):
        key = data[i:i + 4]
        j = head.get(key, -1)
        prev[i] = j
        head[key] = i
        if i > n - MFLIMIT:
            continue
        found = []
        best = MIN_MATCH - 1
        chain = 0
        while j >= 0 and i - j <= MAX_OFFSET and chain < max_chain:
            L = 4
            while i + L < limit and data[j + L] == data[i + L]:
                L += 1
            if L > best:
                best = L
                found.append((L, i - j))
            j = prev[j]
            chain += 1
        matches[i] = found
    # --- DP from the end: cost[i] = bytes to encode data[i:], counting literal runs exactly
    INF = float("inf")
    cost = [INF] * (n + 1)
    choice = [None] * (n + 1)
    lit_run = [0] * (n + 1)  # literal run length starting at i in the chosen path
    cost[n] = 0
    for i in range(n - 1, -1, -1):
        # literal: extends the following literal run by one
        run = lit_run[i + 1] + 1 if choice[i + 1] in (None, "lit") else 1
        c_lit = cost[i + 1] + 1 + _ext(run) - (_ext(run - 1) if choice[i + 1] in (None, "lit") else 0)
        if choice[i + 1] not in (None, "lit"):
            c_lit += 0  # a new literal run attaches to the next sequence's token: no extra token
        best_c, best_ch, best_run = c_lit, "lit", run
        if matches[i]:
            prev_len = MIN_MATCH - 1
            for L, off in matches[i]:
                for l in range(prev_len + 1, L + 1):
                    if i + l > n - LAST_LITERALS:
                        break
                    c = cost[i + l] + 1 + 2 + _ext(l - MIN_MATCH)
                    if c < best_c:
                        best_c, best_ch, best_run = c, (l, off), 0
                prev_len = L
        cost[i], choice[i], lit_run[i] = best_c, best_ch, best_run
    # --- emit
    out = bytearray()
    i, lit_start = 0, 0
    while i < n:
        ch = choice[i]
        if ch == "lit" or ch is None:
            i += 1
            continue
        l, off = ch
        lits = data[lit_start:i]
        _emit(out, lits, l, off)
        i += l
        lit_start = i
    lits = data[lit_start:]
    out.append(min(len(lits), 15) << 4)
    if len(lits) >= 15:
        r = len(lits) - 15
        out += bytes([255]) * (r // 255) + bytes([r % 255])
    out += lits
    return bytes(out)


def _emit(out, lits, mlen, off):
    ll, ml = len(lits), mlen - MIN_MATCH
    out.append((min(ll, 15) << 4) | min(ml, 15))
    if ll >= 15:
        r = ll - 15
        out += bytes([255]) * (r // 255) + bytes([r % 255])
    out += lits
    out += bytes([off & 255, off >> 8])
    if ml >= 15:
        r = ml - 15
        out += bytes([255]) * (r // 255) + bytes([r % 255])


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    import install
    lookup = install.chunk_lookup()
    for want in ("sgn_gbl_shop_hrzntl_6m_01_a_cluster000", "sgn_gbl_shop_vinyl_3m_01_a_cluster000",
                 "sgn_gbl_shops_vinyl_6m_01_a_cluster000", "sgn_gbl_shop_square_01_a_cluster000"):
        name = next(k for k in lookup if k.startswith(want))
        d = install.original_entry(*lookup[name])
        hc = len(lz4.block.compress(d, store_size=False, mode="high_compression", compression=12))
        opt = compress(d)
        assert lz4.block.decompress(opt, uncompressed_size=len(d)) == d
        print(f"{want[:34]:34} raw {len(d)}  HC12 {hc}  optimal {len(opt)}  saves {hc - len(opt)}")
