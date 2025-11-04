import streamlit as st
import requests
st.title("Welcome to HomeFinder 🏠")
st.header("Select your criteria")

yearBuilt = st.selectbox("Year Built?", ["After 2020", "2010-2020", "2000-2009", "1990-1999", "Before 1990"])
col1, col2 = st.columns(2)
with col1:
    room = st.selectbox(
    "Bedrooms", ["1", "2", "3", "4", "5+" ]
    )

with col2:
    bathrooms = st.selectbox(
    "Bathrooms", ["1", "2", "3", "4", "5+" ]
    )


price = st.slider("Select price range($)", 0, 5000000, 250000, step = 20000)

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


if st.button("Search"):
    try:
        response = requests.get("http://127.0.0.1:5000/api/homes")
        if response.status_code == 200:
            homes = response.json()
            st.success(f"Found {len(homes)} homes!")
            for home in homes:
                st.write(f"{home['bedrooms']} BR, {home['bathrooms']} BA - ${home['price']:,}")
        else:
            st.error(f"Backend error")
    except Exception as e:
        st.error("Cant connect backend: ", e)