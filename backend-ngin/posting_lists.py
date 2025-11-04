#!/usr/bin/env python3
import csv
import re
import argparse
from collections import defaultdict
from typing import List, Dict

_int_re = re.compile(r"-?\d+")

def parse_int_like(x):
    if x is None:
        return None
    s = str(x).strip()
    if s == "":
        return None
    try:
        return int(s)
    except:
        pass
    try:
        f = float(s.replace(",", ""))
        if f.is_integer():
            return int(f)
    except:
        pass
    m = _int_re.search(s)
    if m:
        try:
            return int(m.group(0))
        except:
            return None
    return None

def parse_price_like(x):
    if x is None:
        return None
    s = str(x).strip().replace(",", "").replace("$", "")
    if s == "" or s.lower() in {"na", "n/a", "none", "null", "-"}:
        return None
    try:
        return float(s)
    except:
        try:
            m = _int_re.search(s)
            if m:
                return float(m.group(0))
            else:
                return None
        except:
            return None

def intersect_two(a: List[int], b: List[int]) -> List[int]:
    i = 0
    j = 0
    out = []
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            out.append(a[i])
            i += 1
            j += 1
        elif a[i] < b[j]:
            i += 1
        else:
            j += 1
    return out

def intersect_many(lists: List[List[int]]) -> List[int]:
    filtered = []
    for lst in lists:
        if lst:
            filtered.append(lst)
    if not filtered:
        return []
    filtered.sort(key=len)
    cur = filtered[0]
    for nxt in filtered[1:]:
        if not cur:
            return []
        cur = intersect_two(cur, nxt)
    return cur

def merge_union_two(a: List[int], b: List[int]) -> List[int]:
    i = 0
    j = 0
    out = []
    last = None
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            v = a[i]
            i += 1
            j += 1
        elif a[i] < b[j]:
            v = a[i]
            i += 1
        else:
            v = b[j]
            j += 1
        if last != v:
            out.append(v)
            last = v
    while i < len(a):
        v = a[i]
        i += 1
        if last != v:
            out.append(v)
            last = v
    while j < len(b):
        v = b[j]
        j += 1
        if last != v:
            out.append(v)
            last = v
    return out

def merge_union_many(lists: List[List[int]]) -> List[int]:
    out = []
    for lst in lists:
        if not lst:
            continue
        if out:
            out = merge_union_two(out, lst)
        else:
            out = lst
    return out

class PostingIndex:
    def __init__(self, price_bin: int):
        self.price_bin = price_bin
        self.postings: Dict[str, List[int]] = defaultdict(list)
        self.max_fullbaths = 0
        self.max_bedrooms = 0
        self.num_rows = 0
        self.c_bed = 0
        self.c_bath = 0
        self.c_price = 0
        self.prices: List[float] = []

    def _key_bed(self, v: int) -> str:
        return f"Bedrooms={v}"

    def _key_baths(self, v: int) -> str:
        return f"FullBaths={v}"

    def _key_pricebin(self, b: int) -> str:
        lo = b * self.price_bin
        hi = lo + self.price_bin
        return f"PriceBin=[{lo},{hi})"

    def add_row(self, pid: int, bedrooms, fullbaths, price):
        b = parse_int_like(bedrooms)
        if b is not None and b >= 0:
            self.postings[self._key_bed(b)].append(pid)
            self.c_bed += 1
            if b > self.max_bedrooms:
                self.max_bedrooms = b

        fb = parse_int_like(fullbaths)
        if fb is not None and fb >= 0:
            self.postings[self._key_baths(fb)].append(pid)
            self.c_bath += 1
            if fb > self.max_fullbaths:
                self.max_fullbaths = fb

        p = parse_price_like(price)
        if p is not None and p >= 0:
            bin_id = int(p // self.price_bin)
            self.postings[self._key_pricebin(bin_id)].append(pid)
            self.c_price += 1
            if pid >= len(self.prices):
                self.prices.extend([float("nan")] * (pid + 1 - len(self.prices)))
            self.prices[pid] = p

    def finalize(self):
        for key, lst in self.postings.items():
            lst.sort()
            w = 0
            for x in lst:
                if w == 0 or lst[w - 1] != x:
                    lst[w] = x
                    w += 1
            del lst[w:]
        return self

    def q_bedrooms_eq(self, v: int) -> List[int]:
        lst = self.postings.get(self._key_bed(v))
        if lst is None:
            return []
        return lst

    def q_fullbaths_ge(self, v: int) -> List[int]:
        lists = []
        k = v
        while k <= self.max_fullbaths:
            key = self._key_baths(k)
            lst = self.postings.get(key)
            if lst:
                lists.append(lst)
            k += 1
        return merge_union_many(lists)

    def q_price_range_bins(self, lo: int, hi: int) -> List[int]:
        b_lo = lo // self.price_bin
        b_hi_excl = (hi + (self.price_bin - 1)) // self.price_bin
        lists = []
        b = b_lo
        while b < b_hi_excl:
            key = self._key_pricebin(b)
            lst = self.postings.get(key)
            if lst:
                lists.append(lst)
            b += 1
        return merge_union_many(lists)

    def post_filter_price_exact(self, pids: List[int], lo: int, hi: int) -> List[int]:
        out = []
        for pid in pids:
            if 0 <= pid < len(self.prices):
                p = self.prices[pid]
                if p == p and lo <= p <= hi:
                    out.append(pid)
        return out

def build_index(csv_path, bedrooms_col, fullbaths_col, price_col, price_bin):
    idx = PostingIndex(price_bin=price_bin)
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        print("CSV columns:", reader.fieldnames)
        needed = [bedrooms_col, fullbaths_col, price_col]
        missing = []
        for c in needed:
            if c not in reader.fieldnames:
                missing.append(c)
        if missing:
            raise SystemExit(f"Missing columns in CSV: {missing}")
        pid = -1
        for pid, row in enumerate(reader):
            idx.add_row(
                pid,
                row.get(bedrooms_col),
                row.get(fullbaths_col),
                row.get(price_col),
            )
    if pid >= 0:
        idx.num_rows = pid + 1
    else:
        idx.num_rows = 0
    idx.finalize()
    print(f"Parsed rows with Bedrooms: {idx.c_bed} / {idx.num_rows}")
    print(f"Parsed rows with FullBaths: {idx.c_bath} / {idx.num_rows}")
    print(f"Parsed rows with Price:     {idx.c_price} / {idx.num_rows}")
    return idx

def main():
    ap = argparse.ArgumentParser(description="Sorted posting lists for property filters.")
    ap.add_argument("--csv", required=True)
    ap.add_argument("--bedrooms-col", default="Bedrooms")
    ap.add_argument("--fullbaths-col", default="Full Baths")
    ap.add_argument("--price-col", default="Sale Price")
    ap.add_argument("--price-bin", type=int, default=50000)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--exact-price", action="store_true")
    args = ap.parse_args()

    print("Building index (sorted posting lists)…")
    idx = build_index(args.csv, args.bedrooms_col, args.fullbaths_col, args.price_col, args.price_bin)
    print(f"Indexed {idx.num_rows} rows")
    print(f"Max Bedrooms seen: {idx.max_bedrooms}, Max FullBaths seen: {idx.max_fullbaths}")
    print(f"Posting keys: {len(idx.postings)}\n")

    if args.demo:
        lo = 200_000
        hi = 300_000
        print(f"Running demo: Bedrooms=4 AND FullBaths>=3 AND Price∈[{lo},{hi}] …")
        p_bed = idx.q_bedrooms_eq(4)
        p_bath = idx.q_fullbaths_ge(3)
        p_price = idx.q_price_range_bins(lo, hi)
        results = intersect_many([p_bed, p_bath, p_price])
        if args.exact_price:
            results = idx.post_filter_price_exact(results, lo, hi)
        print(f"Matches: {len(results)} properties")
        print("First 20 pids:", results[:20])

if __name__ == "__main__":
    main()