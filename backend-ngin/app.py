from flask import Flask, request, jsonify
from flask_cors import CORS

try:
    from posting_hashsets import build_index
except Exception:
    try:
        from posting_lists import build_index
    except Exception:
        from data_fetching import build_index

app = Flask(__name__)
CORS(app)
idx = build_index(
    "C:/Users/escal/Documents/DSA/Homefinder/data/chicago_data_cleaned.csv",
    bedrooms_col="Bedrooms",
    fullbaths_col="Full Baths",
    price_col="Sale Price",
    price_bin=50000
)

@app.route("/api/properties")
def get_properties():
    bed = request.args.get("bedrooms", type=int)
    bath = request.args.get("bathrooms", type=int)
    lo = request.args.get("price_min", type=int, default=0)
    hi = request.args.get("price_max", type=int, default=10_000_000)
    results = []
    if bed is not None:
        p_bed = idx.q_bedrooms_eq(bed)
        p_bath = idx.q_fullbaths_ge(bath or 0)
        p_price = idx.q_price_range_bins(lo, hi)
        ids = idx.post_filter_price_exact(
            idx.q_price_range_bins(lo, hi), lo, hi
        )
        results = ids[:50]  

    return jsonify({"count": len(results), "ids": results})

if __name__ == "__main__":
    app.run(port=5000, debug=True)