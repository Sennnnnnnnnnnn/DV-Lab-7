import streamlit as st
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

st.set_page_config(page_title="Interactive Map Visualization", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
SHAPEFILE = BASE_DIR / "ne_110m_admin_0_countries" / "ne_110m_admin_0_countries.shp"

PROJECTION_OPTIONS = {
    "WGS 84 (Longitude/Latitude)": "EPSG:4326",
    "Mercator": "EPSG:3395",
    "Robinson": "+proj=robin +lon_0=0 +datum=WGS84 +units=m +no_defs",
    "Mollweide": "+proj=moll +lon_0=0 +datum=WGS84 +units=m +no_defs",
}

@st.cache_data
def load_data(shapefile_path):
    gdf = gpd.read_file(shapefile_path)
    if "pop_est" not in gdf.columns:
        np.random.seed(0)
        gdf["pop_est"] = np.random.randint(1_000_000, 1_000_000_001, size=len(gdf))

    if "name" in gdf.columns:
        country_col = "name"
    elif "NAME" in gdf.columns:
        country_col = "NAME"
    elif "ADMIN" in gdf.columns:
        country_col = "ADMIN"
    else:
        raise ValueError(f"Country-name column not found. Available columns: {list(gdf.columns)}")
    return gdf, country_col

st.title("Interactive Map Visualization Examples")
st.write(
    "Explore map cosmetics, visual hierarchy, choropleth maps, and map projections. "
    "If population estimates are missing, random sample values are generated for demonstration."
)

st.sidebar.header("Choose a Map Type")
map_type = st.sidebar.radio(
    "Select Map Type",
    ["Map Cosmetics", "Map Visual Hierarchy", "Choropleth Map", "Geo Projection"],
)

if not SHAPEFILE.is_file():
    st.error(f"Shapefile not found: {SHAPEFILE}")
    st.markdown("Download and extract the Natural Earth 110m Admin 0 – Countries shapefile.")
    st.code(
        "Your Lab 7 folder/\\n"
        "├── map_visualization.py\\n"
        "└── ne_110m_admin_0_countries/\\n"
        "    ├── ne_110m_admin_0_countries.shp\\n"
        "    ├── ne_110m_admin_0_countries.shx\\n"
        "    ├── ne_110m_admin_0_countries.dbf\\n"
        "    └── ne_110m_admin_0_countries.prj"
    )
    st.stop()

try:
    gdf, country_col = load_data(str(SHAPEFILE))

    if map_type == "Map Cosmetics":
        st.subheader("Map Cosmetics")
        fig, ax = plt.subplots(figsize=(12, 7))
        gdf.plot(ax=ax, color="skyblue", edgecolor="black", linewidth=0.5)
        ax.set_title("Styled Map Example", fontsize=15, fontweight="bold")
        ax.set_facecolor("lightgrey")
        ax.set_axis_off()
        st.pyplot(fig)
        plt.close(fig)

    elif map_type == "Map Visual Hierarchy":
        st.subheader("Map Visual Hierarchy")
        defaults_requested = ["Brazil", "India", "China", "Australia", "South Africa", "Russia"]
        countries = gdf[country_col].dropna().astype(str).tolist()
        defaults = [name for name in defaults_requested if name in countries]
        highlighted = st.multiselect(
            "Select countries to highlight in red",
            options=sorted(countries),
            default=defaults,
        )
        fig, ax = plt.subplots(figsize=(12, 7))
        gdf[~gdf[country_col].isin(highlighted)].plot(
            ax=ax, color="skyblue", edgecolor="black", linewidth=0.4
        )
        selected = gdf[gdf[country_col].isin(highlighted)]
        if not selected.empty:
            selected.plot(ax=ax, color="red", edgecolor="black", linewidth=0.6)
        ax.set_title("Selected Countries Highlighted in Red")
        ax.set_axis_off()
        st.pyplot(fig)
        plt.close(fig)

    elif map_type in ["Choropleth Map", "Geo Projection"]:
        st.subheader(map_type)
        color_choice = st.selectbox(
            "Choose Color Scheme", ["OrRd", "YlGn", "Blues", "Purples", "Greens"], index=0
        )
        use_log_scale = st.checkbox(
            "Use Log Transformation" if map_type == "Choropleth Map"
            else "Use Log Transformation for Population Density",
            value=True,
        )

        # Calculate area in an equal-area CRS rather than using square degrees.
        area_gdf = gdf.to_crs("EPSG:6933")
        area = area_gdf.geometry.area.replace(0, np.nan)
        density = area_gdf["pop_est"] / area
        if use_log_scale:
            density = np.log1p(density.clip(lower=0))

        plot_gdf = gdf.copy()
        plot_gdf["pop_density"] = density.to_numpy()

        if map_type == "Geo Projection":
            proj_choice = st.selectbox("Select a Projection", list(PROJECTION_OPTIONS.keys()))
            plot_gdf = plot_gdf.to_crs(PROJECTION_OPTIONS[proj_choice])
            title = f"Population Density by Country — {proj_choice}"
        else:
            title = f"Population Density by Country (Color Scheme: {color_choice})"

        fig, ax = plt.subplots(figsize=(12, 7))
        plot_gdf.plot(
            column="pop_density",
            cmap=color_choice,
            edgecolor="black",
            linewidth=0.4,
            legend=True,
            ax=ax,
            missing_kwds={"color": "lightgrey", "label": "No data"},
        )
        ax.set_title(title)
        ax.set_axis_off()
        st.pyplot(fig)
        plt.close(fig)

except Exception as error:
    st.error(f"An error occurred while loading or plotting the map: {error}")
    st.info("Ensure the shapefile components (.shp, .shx, .dbf, .prj) are all extracted in the dataset folder.")
