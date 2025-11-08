#!/usr/bin/env python3
from flask import Flask, jsonify, request
from flask_cors import CORS
import csv
import time
import sys
import os
from posting_hashsets import SetPostingIndex, parse_int_like, parse_price_like, intersect_sets
from posting_lists import PostingIndex, intersect_many

app = Flask(__name__)
CORS(app)

hashset_index = None
posting_index = None
properties_data = []


def load_csv_data(path):
    data = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def initialize_indexes(csv_file, bedrooms_col="Bedrooms", fullbaths_col="Full Baths",
                       price_col="Sale Price Clean", price_bin=50000):
    global hashset_index, posting_index, properties_data

    print(f"Loading data from {csv_file}...")
    properties_data = load_csv_data(csv_file)
    print(f"Loaded {len(properties_data)} properties")

    print("Building hash-set index...")
    t0 = time.time()
    hashset_index = SetPostingIndex(price_bin=price_bin)
    for pid, row in enumerate(properties_data):
        hashset_index.add_row(pid, row.get(bedrooms_col), row.get(fullbaths_col), row.get(price_col))
    hashset_index.num_rows = len(properties_data)
    print(f"Hash-set index built in {time.time() - t0:.4f}s")

    print("Building posting-list index...")
    t0 = time.time()
    posting_index = PostingIndex(price_bin=price_bin)
    for pid, row in enumerate(properties_data):
        posting_index.add_row(pid, row.get(bedrooms_col), row.get(fullbaths_col), row.get(price_col))
    posting_index.num_rows = len(properties_data)
    posting_index.finalize()
    print(f"Posting-list index built in {time.time() - t0:.4f}s")


def query_hashset(bedrooms=None, bathrooms=None, price_min=0, price_max=5000000):
    query_sets = []
    if bedrooms is not None:
        query_sets.append(hashset_index.q_bedrooms_eq(bedrooms))
    if bathrooms is not None:
        query_sets.append(hashset_index.q_fullbaths_ge(bathrooms))
    query_sets.append(hashset_index.q_price_range_bins(price_min, price_max))
    pids = intersect_sets(query_sets)
    return hashset_index.post_filter_price_exact(pids, price_min, price_max)


def query_posting_lists(bedrooms=None, bathrooms=None, price_min=0, price_max=5000000):
    query_lists = []
    if bedrooms is not None:
        query_lists.append(posting_index.q_bedrooms_eq(bedrooms))
    if bathrooms is not None:
        query_lists.append(posting_index.q_fullbaths_ge(bathrooms))
    query_lists.append(posting_index.q_price_range_bins(price_min, price_max))
    pids = intersect_many(query_lists)
    return posting_index.post_filter_price_exact(pids, price_min, price_max)


def parse_year_built_range(year_str):
    # Age = 2018 - year_built (dataset year is 2018)
    if year_str == "After 2020":
        return (-10, 0)
    if year_str == "2010-2020":
        return (0, 8)
    if year_str == "2000-2009":
        return (9, 18)
    if year_str == "1990-1999":
        return (19, 28)
    if year_str == "Before 1990":
        return (29, 9999)
    return (0, 9999)


def filter_by_age(pids, age_range, age_col="Age"):
    min_age, max_age = age_range
    out = []
    for pid in pids:
        if 0 <= pid < len(properties_data):
            age = parse_int_like(properties_data[pid].get(age_col))
            if age is not None and min_age <= age <= max_age:
                out.append(pid)
    return out


def filter_by_features(pids, basement=False, fireplace=False, attic=False, garage=False):
    """
    Based on Chicago dataset columns:
    Basement: 1=None, 2+=Has
    Fireplaces: 0=None, 1+=Has
    Attic Type: 0=None, 1+=Has
    Garage indicator: 0=No, 1=Yes
    """
    out = []
    for pid in pids:
        if 0 <= pid < len(properties_data):
            prop = properties_data[pid]

            if basement:
                v = parse_int_like(prop.get("Basement"))
                if v is None or v <= 1:
                    continue

            if fireplace:
                v = parse_int_like(prop.get("Fireplaces"))
                if v is None or v == 0:
                    continue

            if attic:
                v = parse_int_like(prop.get("Attic Type"))
                if v is None or v == 0:
                    continue

            if garage:
                v = parse_int_like(prop.get("Garage indicator"))
                if v is None or v == 0:
                    continue

            out.append(pid)
    return out


@app.route('/api/homes', methods=['GET'])
def search_homes():
    if hashset_index is None or posting_index is None:
        return jsonify({"error": "Indexes not initialized"}), 500

    bedrooms = request.args.get('bedrooms', type=int)
    bathrooms = request.args.get('bathrooms', type=int)
    price_max = request.args.get('price_max', default=5000000, type=int)
    price_min = request.args.get('price_min', default=0, type=int)
    year_built_str = request.args.get('year_built', default="")
    basement = request.args.get('basement', default='false').lower() == 'true'
    fireplace = request.args.get('fireplace', default='false').lower() == 'true'
    attic = request.args.get('attic', default='false').lower() == 'true'
    garage = request.args.get('garage', default='false').lower() == 'true'
    method = request.args.get('method', default='both')

    results = {}
    pids_hashset = []
    pids_posting = []

    if method in ['hashset', 'both']:
        t0 = time.time()
        pids_hashset = query_hashset(bedrooms, bathrooms, price_min, price_max)
        if year_built_str:
            pids_hashset = filter_by_age(pids_hashset, parse_year_built_range(year_built_str))
        if basement or fireplace or attic or garage:
            pids_hashset = filter_by_features(pids_hashset, basement, fireplace, attic, garage)
        results['hashset'] = {"count": len(pids_hashset), "time_ms": round((time.time() - t0) * 1000, 3)}

    if method in ['posting', 'both']:
        t0 = time.time()
        pids_posting = query_posting_lists(bedrooms, bathrooms, price_min, price_max)
        if year_built_str:
            pids_posting = filter_by_age(pids_posting, parse_year_built_range(year_built_str))
        if basement or fireplace or attic or garage:
            pids_posting = filter_by_features(pids_posting, basement, fireplace, attic, garage)
        results['posting'] = {"count": len(pids_posting), "time_ms": round((time.time() - t0) * 1000, 3)}

    if method in ['posting', 'both'] and pids_posting:
        primary_pids = pids_posting
    elif method in ['hashset', 'both'] and pids_hashset:
        primary_pids = pids_hashset
    else:
        primary_pids = []

    homes = []
    for pid in primary_pids[:50]:
        if 0 <= pid < len(properties_data):
            prop = properties_data[pid]
            price_val = parse_price_like(prop.get('Sale Price Clean'))
            age_val = parse_int_like(prop.get('Age'))
            year_built_val = 2018 - age_val if age_val is not None else 'N/A'
            
            # Extract latitude and longitude
            # Common column names: 'Latitude', 'Longitude', 'Location', etc.
            lat = None
            lon = None
            
            # Try common column name patterns
            for lat_col in ['Latitude', 'latitude', 'Lat', 'lat', 'LATITUDE']:
                if lat_col in prop:
                    try:
                        lat = float(prop[lat_col])
                        break
                    except (ValueError, TypeError):
                        pass
            
            for lon_col in ['Longitude', 'longitude', 'Lon', 'lon', 'Long', 'long', 'LONGITUDE']:
                if lon_col in prop:
                    try:
                        lon = float(prop[lon_col])
                        break
                    except (ValueError, TypeError):
                        pass
            
            # If there's a combined 'Location' column like "(41.234, -87.567)"
            if lat is None and lon is None and 'Location' in prop:
                try:
                    location_str = prop['Location'].strip('() ')
                    parts = location_str.split(',')
                    if len(parts) == 2:
                        lat = float(parts[0].strip())
                        lon = float(parts[1].strip())
                except (ValueError, TypeError, AttributeError):
                    pass
            
            homes.append({
                'id': pid,
                'bedrooms': prop.get('Bedrooms', 'N/A'),
                'bathrooms': prop.get('Full Baths', 'N/A'),
                'price': price_val,
                'age': age_val,
                'year_built': year_built_val,
                'address': prop.get('Property Address', 'N/A'),
                'building_sqft': prop.get('Building Square Feet', 'N/A'),
                'latitude': lat,
                'longitude': lon
            })

    return jsonify({
        'homes': homes,
        'performance': results,
        'query': {
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'price_range': [price_min, price_max],
            'year_built': year_built_str,
            'features': {
                'basement': basement,
                'fireplace': fireplace,
                'attic': attic,
                'garage': garage
            }
        }
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    if hashset_index is None or posting_index is None:
        return jsonify({"error": "Indexes not initialized"}), 500
    return jsonify({
        'total_properties': len(properties_data),
        'hashset_index': {
            'posting_keys': len(hashset_index.postings),
            'max_bedrooms': hashset_index.max_bedrooms,
            'max_bathrooms': hashset_index.max_fullbaths
        },
        'posting_index': {
            'posting_keys': len(posting_index.postings),
            'max_bedrooms': posting_index.max_bedrooms,
            'max_bathrooms': posting_index.max_fullbaths
        }
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'indexes_loaded': hashset_index is not None and posting_index is not None
    })


if __name__ == '__main__':
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "../data/chicago_data_cleaned_dup.csv"

    if not os.path.exists(csv_file):
        print(f"ERROR: CSV file not found at: {csv_file}")
        print("Pass the CSV path as an argument or update csv_file.")
        sys.exit(1)

    initialize_indexes(csv_file)

    print("Starting Flask server on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)