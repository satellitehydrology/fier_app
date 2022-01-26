import ee
import os
import datetime
import folium
import streamlit as st
import geemap.colormaps as cm
import geemap.foliumap as geemap
import restee as ree
import matplotlib.pyplot as plt
from create_imagecollection import *
import json
from our_fierpy import *
import fierpy
import xarray as xr

# Page Configuration
st.set_page_config(layout="wide")


# Title and Description
st.title("Forecasting Inundation Extents using REOF Analysis (FIER)-Mekong")

row1_col1, row1_col2 = st.columns([2, 1])
# Set up Geemap
with row1_col1:
    m = geemap.Map(
        basemap="HYBRID",
        zoom=5,
        center=(13,103),
    )
    crs = "epsg:4326"

    m.add_basemap("ROADMAP")


with row1_col2:
    # Form
    with st.form("Determine Area of Interest"):
        # lAT / LONG
        st.subheader('Determine Area of Interest')
        lat = st.number_input("Latitude:", value = 11.58)
        long = st.number_input("Longitude:", value = 104.93)

        # Submit Button
        submitted = st.form_submit_button("Submit")
        if submitted:
            # Change map based on chosen lat long
            ee_pin = ee.Geometry.Point(long, lat)

            aoi = (
            ee.FeatureCollection("WWF/HydroSHEDS/v1/Basins/hybas_6")
            .filterBounds(ee_pin)
        )
            m.set_center(float(long), float(lat), 8)
            m.addLayer(aoi, {}, 'AOI (WWF HydroSHEDS)')


    with st.form("Run FIER"):
        st.subheader('Download Google Earth Enginge Images And Run FIER')

        # Start/End Date
        start_date = st.date_input(
         "Start Date",
         datetime.date(2017, 1, 1))

        end_date = st.date_input(
        "End Date",
        datetime.date(2017, 6, 1))

        # Upload Json File
        uploaded_file = st.file_uploader("Update Cloud Project Json File:")

        submitted_2 = st.form_submit_button("Submit")
        if submitted_2:
            # Change map based on chosen lat long
            ee_pin = ee.Geometry.Point(long, lat)

            aoi = (
            ee.FeatureCollection("WWF/HydroSHEDS/v1/Basins/hybas_6")
            .filterBounds(ee_pin)
        )
            m.set_center(float(long), float(lat), 8)
            m.addLayer(aoi, {}, 'AOI (WWF HydroSHEDS)')

            # If uploaded json file for RESTEE
            if uploaded_file is not None:
                # Write upload_file into a path
                if not os.path.exists(uploaded_file.name):
                    with open(os.path.join(uploaded_file.name),"wb") as f:
                        f.write(uploaded_file.getbuffer())

                with open(os.path.join(uploaded_file.name),"r") as f:
                    credential = str(json.load(f)["project_id"])


                # Set up restee


                # Generate image collection

                S1_ImgCol = output_collection(aoi, str(start_date), str(end_date))
                m.addLayer(S1_ImgCol.first().geometry(), {}, 'Image Collection Geometry')
                session = ree.EESession(credential,uploaded_file.name)
                domain = ree.Domain.from_ee_geometry(session, S1_ImgCol.first().geometry(), resolution = 0.005)


                img_stack = ree.imgcollection_to_xarray(session, domain, S1_ImgCol, bands = ['VV'])
                img_stack = img_stack.transpose("time", "lat", "lon")
                a, b = reof(img_stack.VV, n_modes = 4)
                for i in range(a.mode.shape[0]):
                    fig = plt.figure(figsize = (12,10))
                    plt.imshow(a.spatial_modes.isel(mode = i).values)
                    st.pyplot(fig = fig)
                    fig = plt.figure(figsize = (12,10))
                    plt.plot(a.time, a.temporal_modes.isel(mode = i).values ,'--bo')
                    st.pyplot(fig = fig)


            else:
                st.warning('File Missing')




with row1_col1:
    m.to_streamlit(height=600)
    st.markdown(
    """
    Reference: Chang, C. H., Lee, H., Kim, D., Hwang, E., Hossain, F., Chishtie, F., ... & Basnayake, S. (2020). Hindcast and forecast of daily inundation extents using satellite SAR and altimetry data with rotated empirical orthogonal function analysis: Case study in Tonle Sap Lake Floodplain. Remote Sensing of Environment, 241, 111732.
    """
    )
