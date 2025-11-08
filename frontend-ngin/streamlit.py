import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="HomeFinder", layout="wide")

# Initialize session state
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'last_search_params' not in st.session_state:
    st.session_state.last_search_params = None

st.title("Welcome to HomeFinder")
st.markdown("Compare the performance of **Hash-Set** vs **Posting-List** indexing methods")

# Sidebar
st.sidebar.header("Algorithm Selection")
method = st.sidebar.radio(
    "Choose indexing method:",
    ["both", "hashset", "posting"],
    format_func=lambda x: {
        "both": "Compare Both",
        "hashset": "Hash-Set Only",
        "posting": "Posting-List Only"
    }[x]
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
### About the Methods
**Hash-Set Index:**
- Uses Python sets for fast membership testing
- Set intersection for query operations

**Posting-List Index:**
- Uses sorted lists for space efficiency
- Merge-based intersection algorithm
""")

# Filters
st.header("Select your criteria")

yearBuilt = st.selectbox(
    "Year Built?",
    ["", "After 2020", "2010-2020", "2000-2009", "1990-1999", "Before 1990"]
)

col1, col2 = st.columns(2)
with col1:
    room = st.selectbox("Bedrooms", ["Any", "1", "2", "3", "4", "5+"])
with col2:
    bathrooms = st.selectbox("Bathrooms", ["Any", "1", "2", "3", "4", "5+"])

price = st.slider(
    "Select price range ($)",
    0, 5000000, (0, 500000),
    step=20000,
    format="$%d"
)

st.subheader("Additional Features")
col3, col4 = st.columns(2)
with col3:
    basement = st.checkbox("Basement?")
with col4:
    fireplace = st.checkbox("Fireplace?")

col5, col6 = st.columns(2)
with col5:
    attic = st.checkbox("Attic?")
with col6:
    garage = st.checkbox("Garage?")

# Search
if st.button("Search", type="primary", use_container_width=True):
    params = {
        "method": method,
        "price_min": price[0],
        "price_max": price[1],
    }

    if room != "Any":
        params["bedrooms"] = 5 if room == "5+" else int(room)

    if bathrooms != "Any":
        params["bathrooms"] = 5 if bathrooms == "5+" else int(bathrooms)

    if yearBuilt:
        params["year_built"] = yearBuilt

    if basement:
        params["basement"] = "true"
    if fireplace:
        params["fireplace"] = "true"
    if attic:
        params["attic"] = "true"
    if garage:
        params["garage"] = "true"

    with st.spinner("Searching properties..."):
        try:
            response = requests.get(
                "http://127.0.0.1:5000/api/homes",
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                st.session_state.search_results = response.json()
                st.session_state.last_search_params = params
            else:
                st.error(f"Backend error: {response.status_code}")
                st.code(response.text)
                st.session_state.search_results = None

        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to backend. Make sure the Flask server is running.")
            st.info("Run: `python backend_api.py <path_to_csv>`")
            st.session_state.search_results = None
        except requests.exceptions.Timeout:
            st.error("Request timed out. The dataset might be too large.")
            st.session_state.search_results = None
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.session_state.search_results = None

# Display results if they exist in session state
if st.session_state.search_results is not None:
    data = st.session_state.search_results
    homes = data.get("homes", [])
    performance = data.get("performance", {})
    query_info = data.get("query", {})

    data = st.session_state.search_results
    homes = data.get("homes", [])
    performance = data.get("performance", {})
    query_info = data.get("query", {})

    st.success(f"Found {len(homes)} properties.")

    if method == "both" and "hashset" in performance and "posting" in performance:
        st.subheader("Performance Comparison")

        perf_col1, perf_col2, perf_col3 = st.columns(3)
        with perf_col1:
            st.metric(
                "Hash-Set Index",
                f"{performance['hashset']['time_ms']:.2f} ms",
                f"{performance['hashset']['count']} results"
            )
        with perf_col2:
            st.metric(
                "Posting-List Index",
                f"{performance['posting']['time_ms']:.2f} ms",
                f"{performance['posting']['count']} results"
            )
        with perf_col3:
            hashset_time = performance["hashset"]["time_ms"]
            posting_time = performance["posting"]["time_ms"]
            if hashset_time < posting_time:
                speedup = posting_time / hashset_time
                st.metric("Winner", "Hash-Set", f"{speedup:.2f}x faster", delta_color="normal")
            else:
                speedup = hashset_time / posting_time
                st.metric("Winner", "Posting-List", f"{speedup:.2f}x faster", delta_color="normal")

    elif "hashset" in performance:
        st.info(f"Query executed in {performance['hashset']['time_ms']:.2f} ms using Hash-Set index")
    elif "posting" in performance:
        st.info(f"Query executed in {performance['posting']['time_ms']:.2f} ms using Posting-List index")

    if homes:
        st.subheader("Matching Properties")

        with st.expander("Query Details", expanded=False):
            st.json(query_info)

        # Create map if we have properties with valid coordinates
        homes_with_coords = [h for h in homes if h.get('latitude') and h.get('longitude')]
        
        if homes_with_coords:
            st.subheader("📍 Property Locations")
            
            # Calculate center of map (average of all coordinates)
            avg_lat = sum(h['latitude'] for h in homes_with_coords) / len(homes_with_coords)
            avg_lon = sum(h['longitude'] for h in homes_with_coords) / len(homes_with_coords)
            
            # Create folium map
            m = folium.Map(
                location=[avg_lat, avg_lon],
                zoom_start=11,
                tiles="OpenStreetMap"
            )
            
            # Add markers for each property
            for idx, home in enumerate(homes_with_coords, 1):
                lat = home['latitude']
                lon = home['longitude']
                
                # Create popup content
                price_str = f"${home['price']:,.0f}" if home.get('price') and home['price'] == home['price'] else "N/A"
                popup_html = f"""
                <div style="font-family: Arial; width: 200px;">
                    <b>Property #{idx}</b><br>
                    <b>Price:</b> {price_str}<br>
                    <b>Beds:</b> {home.get('bedrooms', 'N/A')}<br>
                    <b>Baths:</b> {home.get('bathrooms', 'N/A')}<br>
                    <b>Year:</b> {home.get('year_built', 'N/A')}<br>
                    <hr style="margin: 5px 0;">
                    <small>{home.get('address', 'Address N/A')}</small>
                </div>
                """
                
                # Determine marker color based on price
                if home.get('price') and home['price'] == home['price']:
                    if home['price'] < 200000:
                        color = 'green'
                    elif home['price'] < 400000:
                        color = 'blue'
                    elif home['price'] < 600000:
                        color = 'orange'
                    else:
                        color = 'red'
                else:
                    color = 'gray'
                
                # Add marker
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=f"Property #{idx}: {price_str}",
                    icon=folium.Icon(color=color, icon='home', prefix='fa')
                ).add_to(m)
            
            # Display map
            col_map1, col_map2, col_map3 = st.columns([1, 10, 1])
            with col_map2:
                st_folium(m, width=None, height=500, use_container_width=True)
            
            # Add legend
            st.markdown("""
            <div style='background-color: rgba(255, 255, 255, 0.9); padding: 12px; border-radius: 8px; text-align: center; border: 1px solid #ddd; max-width: 700px; margin: 10px auto;'>
                <span style='color: #28a745; font-size: 20px;'>●</span> <span style='color: #333;'>Under $200k</span> &nbsp;&nbsp;|&nbsp;&nbsp; 
                <span style='color: #007bff; font-size: 20px;'>●</span> <span style='color: #333;'>$200k-$400k</span> &nbsp;&nbsp;|&nbsp;&nbsp; 
                <span style='color: #fd7e14; font-size: 20px;'>●</span> <span style='color: #333;'>$400k-$600k</span> &nbsp;&nbsp;|&nbsp;&nbsp; 
                <span style='color: #dc3545; font-size: 20px;'>●</span> <span style='color: #333;'>Over $600k</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("📍 Map unavailable: No properties have location coordinates")

        st.subheader("Property Details")

        for i, home in enumerate(homes, 1):
            with st.container():
                col_a, col_b = st.columns([3, 1])

                with col_a:
                    st.markdown(f"**Property #{i}** - ID: {home['id']}")
                    st.markdown(home.get("address", "Address not available"))

                    year_info = home.get("year_built", "N/A")
                    age_info = home.get("age", "N/A")
                    sqft_info = home.get("building_sqft", "N/A")

                    st.markdown(
                        f"Bedrooms: {home['bedrooms']} | "
                        f"Bathrooms: {home['bathrooms']} | "
                        f"Built: {year_info} (Age: {age_info}) | "
                        f"Size: {sqft_info} sq ft"
                    )

                with col_b:
                    price_val = home.get("price")
                    if price_val and price_val == price_val:  # not NaN
                        st.markdown(f"### ${price_val:,.0f}")
                    else:
                        st.markdown("### Price N/A")

                st.divider()
    else:
        st.warning("No properties match your criteria. Try adjusting your filters.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>HomeFinder - Data Structures & Algorithms Project</p>
    <p>Comparing Hash-Set vs Posting-List indexing methods for property search</p>
</div>
""", unsafe_allow_html=True)