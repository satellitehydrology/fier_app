import streamlit as st

# Page Configuration
st.set_page_config(layout="wide")


# Title and Description
st.title("Forecasting Inundation Extents using REOF Analysis (FIER) Demo Apps")

st.header("[FIER Demo App Over Bangladesh](https://share.streamlit.io/skd862/fier_bangladesh/main/demo.py)")

st.header("[FIER Demo App Over Mekong Area](https://share.streamlit.io/skd862/fier_mekong/main/demo.py)")

st.header("[FIER Demo App For VIIRS/ABI Water Fraction](https://share.streamlit.io/skd862/fier_noaa/main/demo.py)")

url = "https://www.sciencedirect.com/science/article/pii/S0034425720301024?casa_token=kOYlVMMWkBUAAAAA:fiFM4l6BUzJ8xTCksYUe7X4CcojddbO8ybzOSMe36f2cFWEXDa_aFHaGeEFlN8SuPGnDy7Ir8w"
st.write("Reference: [Chang, C. H., Lee, H., Kim, D., Hwang, E., Hossain, F., Chishtie, F., ... & Basnayake, S. (2020). Hindcast and forecast of daily inundation extents using satellite SAR and altimetry data with rotated empirical orthogonal function analysis: Case study in Tonle Sap Lake Floodplain. Remote Sensing of Environment, 241, 111732.](%s)" % url)
    