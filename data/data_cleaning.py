#!/usr/bin/env python3
import csv
import argparse
import re

NA_STRINGS = {"", "na", "n/a", "none", "null", "-", "--"}
_int_re = re.compile(r"-?\d+(\.\d+)?")

def parse_num(x):
    """Parse dollars/ints/floats like '$300,000', '300k' (grabs leading number), returns float or None."""
    if x is None:
        return None
    s = str(x).strip().lower().replace("$", "").replace(",", "")
    if s in NA_STRINGS:
        return None
    # easy path
    try:
        return float(s)
    except:
        pass
    # fallback: first numeric substring
    m = _int_re.search(s)
    if m:
        try:
            return float(m.group(0))
        except:
            return None
    return None

def main():
    ap = argparse.ArgumentParser(description="Fill missing sale prices using land+building estimates.")
    ap.add_argument("--in", dest="inp", required=True, help="Input CSV path")
    ap.add_argument("--out", dest="out", required=True, help="Output CSV path")
    ap.add_argument("--sale-col", default="Sale Price", help="Column name for sale price")
    ap.add_argument("--land-col", default="Prior Tax Year Market Value Estimate (Land)", help="Column name for land value")
    ap.add_argument("--bldg-col", default="Prior Tax Year Market Value Estimate (Building)", help="Column name for building value")
    ap.add_argument("--alpha", type=float, default=1.0, help="Multiplier for estimate: (land+building)*alpha")
    ap.add_argument("--overwrite", action="store_true", help="Also write back normalized numeric values into existing columns")
    args = ap.parse_args()

    # Pass 1: read header & rows
    with open(args.inp, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        if args.sale_col not in headers:
            print(f"[WARN] Sale column '{args.sale_col}' not found; will create it.")
            headers.append(args.sale_col)
        for needed in (args.land_col, args.bldg_col):
            if needed not in headers:
                print(f"[ERROR] Missing column: {needed}")
                return

        # New columns to add
        add_cols = ["Sale Price Clean", "Price Source", "Value Estimate"]
        for c in add_cols:
            if c not in headers:
                headers.append(c)

        # Counters
        n_rows = 0
        n_sale_ok = 0
        n_estimated = 0
        n_none = 0

        rows_out = []

        for row in reader:
            n_rows += 1
            sale_raw = row.get(args.sale_col)
            land_raw = row.get(args.land_col)
            bldg_raw = row.get(args.bldg_col)

            sale = parse_num(sale_raw)
            land = parse_num(land_raw)
            bldg = parse_num(bldg_raw)

            value_est = land + bldg if (land is not None and bldg is not None) else None

            if sale is not None and sale >= 0:
                # Keep sale, mark source
                row["Sale Price Clean"] = f"{sale:.2f}"
                row["Price Source"] = "SALE"
                n_sale_ok += 1
            elif value_est is not None and value_est >= 0:
                est = value_est * args.alpha
                row["Sale Price Clean"] = f"{est:.2f}"
                row["Price Source"] = "ESTIMATE"
                n_estimated += 1
            else:
                row["Sale Price Clean"] = ""
                row["Price Source"] = "NONE"
                n_none += 1

            row["Value Estimate"] = f"{value_est:.2f}" if value_est is not None else ""

            # Optional: normalize original numeric columns (safer for downstream)
            if args.overwrite:
                row[args.sale_col] = f"{sale:.2f}" if sale is not None else ""
                row[args.land_col] = f"{land:.2f}" if land is not None else ""
                row[args.bldg_col] = f"{bldg:.2f}" if bldg is not None else ""

            rows_out.append(row)

    # Write output
    with open(args.out, "w", newline="", encoding="utf-8") as g:
        writer = csv.DictWriter(g, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_out)

    print("=== Data Cleaning Summary ===")
    print(f"Rows processed:          {n_rows:,}")
    print(f"Kept sale price:         {n_sale_ok:,}")
    print(f"Estimated from values:   {n_estimated:,}  (alpha={args.alpha})")
    print(f"No price available:      {n_none:,}")
    print(f"Output written to:       {args.out}")

if __name__ == "__main__":
    main()
