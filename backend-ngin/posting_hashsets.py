#!/usr/bin/env python3
import csv
import re
import argparse
from collections import defaultdict

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
    if s == "" or s.lower() in {"na","n/a","none","null","-"}:
        return None
    try:
        return float(s)
    except:
        m = _int_re.search(s)
        if m:
            return float(m.group(0))
        else:
            return None

class SetPostingIndex:
    def __init__(self, price_bin):
        self.price_bin = price_bin
        self.postings = defaultdict(set)
        self.max_bedrooms = 0
        self.max_fullbaths = 0
        self.num_rows = 0
        self.c_bed = 0
        self.c_bath = 0
        self.c_price = 0
        self.prices = []

    def k_bed(self, v):
        return f"Bedrooms={v}"

    def k_bath(self, v):
        return f"FullBaths={v}"

    def k_price(self, b):
        lo = b * self.price_bin
        hi = lo + self.price_bin
        return f"PriceBin=[{lo},{hi})"

    def add_row(self, pid, bedrooms, fullbaths, price):
        if pid >= len(self.prices):
            self.prices.extend([float("nan")] * (pid + 1 - len(self.prices)))

        b = parse_int_like(bedrooms)
        if b is not None and b >= 0:
            self.postings[self.k_bed(b)].add(pid)
            self.c_bed += 1
            if b > self.max_bedrooms:
                self.max_bedrooms = b

        fb = parse_int_like(fullbaths)
        if fb is not None and fb >= 0:
            self.postings[self.k_bath(fb)].add(pid)
            self.c_bath += 1
            if fb > self.max_fullbaths:
                self.max_fullbaths = fb

        p = parse_price_like(price)
        if p is not None and p >= 0:
            bin_id = int(p // self.price_bin)
            self.postings[self.k_price(bin_id)].add(pid)
            self.c_price += 1
            self.prices[pid] = p

    def q_bedrooms_eq(self, v):
        s = self.postings.get(self.k_bed(v))
        if s is None:
            return set()
        return s

    def q_bedrooms_ge(self, v):
        out = set()
        for k in range(v, self.max_bedrooms + 1):
            s = self.postings.get(self.k_bed(k))
            if s is not None and len(s) > 0:
                out = out.union(s)
        return out

    def q_fullbaths_ge(self, v):
        out = set()
        for k in range(v, self.max_fullbaths + 1):
            s = self.postings.get(self.k_bath(k))
            if s is not None and len(s) > 0:
                out = out.union(s)
        return out

    def q_price_range_bins(self, lo, hi):
        b_lo = lo // self.price_bin
        b_hi_excl = (hi + (self.price_bin - 1)) // self.price_bin
        out = set()
        for b in range(b_lo, b_hi_excl):
            s = self.postings.get(self.k_price(b))
            if s is not None and len(s) > 0:
                out = out.union(s)
        return out

    def post_filter_price_exact(self, pids, lo, hi):
        out = []
        for pid in pids:
            if 0 <= pid < len(self.prices):
                p = self.prices[pid]
                if p == p and lo <= p <= hi:
                    out.append(pid)
        return out

def intersect_sets(sets_list):
    if not sets_list:
        return []
    non_empty = []
    for s in sets_list:
        if s:
            non_empty.append(s)
    if not non_empty:
        return []
    non_empty.sort(key=lambda x: len(x))
    base = non_empty[0]
    others = non_empty[1:]
    out = []
    for pid in base:
        ok = True
        for s in others:
            if pid not in s:
                ok = False
                break
        if ok:
            out.append(pid)
    out.sort()
    return out

def build_index(csv_path, bedrooms_col, fullbaths_col, price_col, price_bin):
    idx = SetPostingIndex(price_bin=price_bin)
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        print("CSV columns:", reader.fieldnames)
        need = [bedrooms_col, fullbaths_col, price_col]
        miss = [c for c in need if c not in reader.fieldnames]
        if miss:
            raise SystemExit(f"Missing columns in CSV: {miss}")
        pid = -1
        for pid, row in enumerate(reader):
            idx.add_row(
                pid,
                row.get(bedrooms_col),
                row.get(fullbaths_col),
                row.get(price_col),
            )
    idx.num_rows = pid + 1 if pid >= 0 else 0
    print(f"Parsed rows with Bedrooms: {idx.c_bed} / {idx.num_rows}")
    print(f"Parsed rows with FullBaths: {idx.c_bath} / {idx.num_rows}")
    print(f"Parsed rows with Price:     {idx.c_price} / {idx.num_rows}")
    return idx

def main():
    ap = argparse.ArgumentParser(description="Hash-set postings for property filters.")
    ap.add_argument("--csv", required=True)
    ap.add_argument("--bedrooms-col", default="Bedrooms")
    ap.add_argument("--fullbaths-col", default="Full Baths")
    ap.add_argument("--price-col", default="Sale Price Clean")
    ap.add_argument("--price-bin", type=int, default=50000)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--exact-price", action="store_true")
    args = ap.parse_args()

    print("Building hash-set postings…")
    idx = build_index(args.csv, args.bedrooms_col, args.fullbaths_col, args.price_col, args.price_bin)
    print(f"Indexed {idx.num_rows} rows")
    print(f"Max Bedrooms seen: {idx.max_bedrooms}, Max FullBaths seen: {idx.max_fullbaths}")
    print(f"Posting keys: {len(idx.postings)}\n")

    if args.demo:
        lo = 300_000
        hi = 400_000
        print(f"Demo: Bedrooms=4 AND FullBaths>=3 AND Price∈[{lo},{hi}] …")

        S_bed  = idx.q_bedrooms_eq(4)
        S_bath = idx.q_fullbaths_ge(3)
        S_pr   = idx.q_price_range_bins(lo, hi)

        ids = intersect_sets([S_bed, S_bath, S_pr])

        if args.exact_price:
            ids = idx.post_filter_price_exact(ids, lo, hi)

        print(f"Matches: {len(ids)}")
        print("First 20 pids:", ids[:20])

if __name__ == "__main__":
    main()