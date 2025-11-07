#!/usr/bin/env python3
import csv
import re
import argparse
from typing import List, Set
import sys
import os

# Add the directory containing hash_table.py to the path
sys.path.insert(0, os.path.dirname(os.path.abspath("backend-ngin/hash_table.py")))
from hash_table import DefaultHashTable

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

def intersect_sets(sets: List[Set[int]]) -> List[int]:
    """
    Intersect multiple sets and return sorted list.
    Uses set intersection operations for O(1) membership testing.
    
    Args:
        sets: List of sets to intersect
        
    Returns:
        Sorted list of elements in all sets
    """
    if not sets:
        return []
    
    # Filter out empty sets
    filtered = [s for s in sets if s]
    if not filtered:
        return []
    
    # Start with the smallest set for efficiency
    filtered.sort(key=len)
    result = filtered[0].copy()
    
    # Intersect with remaining sets
    for s in filtered[1:]:
        result &= s  # Set intersection
        if not result:  # Early exit if empty
            return []
    
    return sorted(list(result))


class SetPostingIndex:
    """
    Posting index using hash sets for O(1) membership testing.
    Uses custom hash table implementation to map attribute values to sets of property IDs.
    """
    
    def __init__(self, price_bin: int):
        """
        Initialize the set-based posting index.
        
        Args:
            price_bin: Size of price bins for range queries
        """
        self.price_bin = price_bin
        # Use custom hash table with set factory
        self.postings = DefaultHashTable(default_factory=set)
        self.max_fullbaths = 0
        self.max_bedrooms = 0
        self.num_rows = 0
        self.c_bed = 0
        self.c_bath = 0
        self.c_price = 0
        self.prices: List[float] = []

    def _key_bed(self, v: int) -> str:
        """Generate key for bedroom count"""
        return f"Bedrooms={v}"

    def _key_baths(self, v: int) -> str:
        """Generate key for bathroom count"""
        return f"FullBaths={v}"

    def _key_pricebin(self, b: int) -> str:
        """Generate key for price bin"""
        lo = b * self.price_bin
        hi = lo + self.price_bin
        return f"PriceBin=[{lo},{hi})"

    def add_row(self, pid: int, bedrooms, fullbaths, price):
        """
        Add a property row to the index.
        
        Args:
            pid: Property ID
            bedrooms: Number of bedrooms
            fullbaths: Number of full bathrooms
            price: Property price
        """
        b = parse_int_like(bedrooms)
        if b is not None and b >= 0:
            self.postings[self._key_bed(b)].add(pid)
            self.c_bed += 1
            if b > self.max_bedrooms:
                self.max_bedrooms = b

        fb = parse_int_like(fullbaths)
        if fb is not None and fb >= 0:
            self.postings[self._key_baths(fb)].add(pid)
            self.c_bath += 1
            if fb > self.max_fullbaths:
                self.max_fullbaths = fb

        p = parse_price_like(price)
        if p is not None and p >= 0:
            bin_id = int(p // self.price_bin)
            self.postings[self._key_pricebin(bin_id)].add(pid)
            self.c_price += 1
            if pid >= len(self.prices):
                self.prices.extend([float("nan")] * (pid + 1 - len(self.prices)))
            self.prices[pid] = p

    def q_bedrooms_eq(self, v: int) -> Set[int]:
        """
        Query for properties with exactly v bedrooms.
        
        Args:
            v: Number of bedrooms
            
        Returns:
            Set of property IDs
        """
        result = self.postings.get(self._key_bed(v), set())
        # Return a copy to avoid external modification
        return result.copy() if result else set()

    def q_fullbaths_ge(self, v: int) -> Set[int]:
        """
        Query for properties with at least v full bathrooms.
        Uses set union for combining multiple bathroom counts.
        
        Args:
            v: Minimum number of full bathrooms
            
        Returns:
            Set of property IDs
        """
        result = set()
        k = v
        while k <= self.max_fullbaths:
            key = self._key_baths(k)
            s = self.postings.get(key, set())
            if s:
                result |= s  # Set union
            k += 1
        return result

    def q_price_range_bins(self, lo: int, hi: int) -> Set[int]:
        """
        Query for properties in price range using binned approach.
        Uses set union to combine multiple price bins.
        
        Args:
            lo: Minimum price
            hi: Maximum price
            
        Returns:
            Set of property IDs
        """
        b_lo = lo // self.price_bin
        b_hi_excl = (hi + (self.price_bin - 1)) // self.price_bin
        result = set()
        b = b_lo
        while b < b_hi_excl:
            key = self._key_pricebin(b)
            s = self.postings.get(key, set())
            if s:
                result |= s  # Set union
            b += 1
        return result

    def post_filter_price_exact(self, pids: List[int], lo: int, hi: int) -> List[int]:
        """
        Post-filter properties to exact price range.
        Needed because bin-based query may include properties outside exact range.
        
        Args:
            pids: List of property IDs to filter
            lo: Minimum price
            hi: Maximum price
            
        Returns:
            Filtered list of property IDs
        """
        out = []
        for pid in pids:
            if 0 <= pid < len(self.prices):
                p = self.prices[pid]
                if p == p and lo <= p <= hi:  # p == p checks for NaN
                    out.append(pid)
        return out


def build_index(csv_path, bedrooms_col, fullbaths_col, price_col, price_bin):
    """
    Build a set-based posting index from CSV file.
    
    Args:
        csv_path: Path to CSV file
        bedrooms_col: Name of bedrooms column
        fullbaths_col: Name of full bathrooms column
        price_col: Name of price column
        price_bin: Size of price bins
        
    Returns:
        SetPostingIndex instance
    """
    idx = SetPostingIndex(price_bin=price_bin)
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
    print(f"Parsed rows with Bedrooms: {idx.c_bed} / {idx.num_rows}")
    print(f"Parsed rows with FullBaths: {idx.c_bath} / {idx.num_rows}")
    print(f"Parsed rows with Price:     {idx.c_price} / {idx.num_rows}")
    return idx


def main():
    ap = argparse.ArgumentParser(description="Hash-set posting lists for property filters.")
    ap.add_argument("--csv", required=True)
    ap.add_argument("--bedrooms-col", default="Bedrooms")
    ap.add_argument("--fullbaths-col", default="Full Baths")
    ap.add_argument("--price-col", default="Sale Price")
    ap.add_argument("--price-bin", type=int, default=50000)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--exact-price", action="store_true")
    args = ap.parse_args()

    print("Building index (hash-set posting lists)…")
    idx = build_index(args.csv, args.bedrooms_col, args.fullbaths_col, args.price_col, args.price_bin)
    print(f"Indexed {idx.num_rows} rows")
    print(f"Max Bedrooms seen: {idx.max_bedrooms}, Max FullBaths seen: {idx.max_fullbaths}")
    print(f"Posting keys: {len(idx.postings)}\n")

    if args.demo:
        lo = 200_000
        hi = 300_000
        print(f"Running demo: Bedrooms=4 AND FullBaths>=3 AND Price∈[{lo},{hi}] …")
        s_bed = idx.q_bedrooms_eq(4)
        s_bath = idx.q_fullbaths_ge(3)
        s_price = idx.q_price_range_bins(lo, hi)
        results = intersect_sets([s_bed, s_bath, s_price])
        if args.exact_price:
            results = idx.post_filter_price_exact(results, lo, hi)
        print(f"Matches: {len(results)} properties")
        print("First 20 pids:", results[:20])


if __name__ == "__main__":
    main()