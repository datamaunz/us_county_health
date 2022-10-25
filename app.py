from src.load_packages import *
from src.helper_frunctions import *
from src.geo_distance_functions import *
import math

# for rivers see https://levelup.gitconnected.com/plotting-choropleth-maps-in-python-b74c53b8d0a6


ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/c/c4/Projet_bi%C3%A8re_logo_v2.png"

@st.cache()
def load_and_prepare_sites_df(address):
    
    df = pd.read_json('data_files/data_used_on_app/all_sites.json', orient ='split', compression = 'infer')
    df["distance"] = df.apply(lambda x: round(calculate_distance_in_km((x.LATITUDE, x.LONGITUDE), address), 2), axis=1)
    df["angle"] = df.apply(lambda x: round(angle_calc(address, (x.LATITUDE, x.LONGITUDE)), 2), axis=1)
    df = df.sort_values("distance")
    df = df.fillna("no entry")
    return df

@st.cache()
def load_and_prepare_cancer_df():
    cancer_df = pd.read_json("data_files/data_used_on_app/5_year_average_incidence_rates_with_coordinates.json")
    cancer_df["SITE_NAME"] = cancer_df["County"] + ", " + cancer_df["State"]
    cancer_df["elevation_value"] = 0
    cancer_df = cancer_df.rename(columns={"incidence_rate": "distance"})
    return cancer_df
    



@st.cache()
def filter_df_by_distance(df, max_dist):
    return df[df["distance"] <= max_dist]

@st.cache()
def compute_color_dict(df, colors):
    color_dict = {item:colors[i] for i, item in enumerate(sorted(df["DATASET"].unique()))}
    return color_dict

def main():
        
    st.set_page_config(
    layout="wide",
    page_title="County Analysis",
    page_icon = "💚"
    )
    
    
    
    
    
    
    
    with st.sidebar.form("Coordinates"):
        lat = st.number_input("Latitude", value=39.2594709)
        lon = st.number_input("Longitude", value=-77.5641585)
        max_dist = st.number_input("Radius for displayed sites in km", value=50)
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            address = (lat, lon)
            max_dist = max_dist
        else:
            address = (39.2594709,-77.5641585) # 12883 Furnace Mountain Rd, Lovettsville, VA 20180
            max_dist = 50
    
    
    title = f"#### Potentially polluting sites in a radius of {max_dist} km around your selected location"
    explainer_text = f'This app is meant to help display potentially polluting sites in a selected radius around a selected location.\
        The data is not complete and we do not claim that any of this is accurate. It is based on downloads from government websites.\
            Do not make this the basis of any of your decisions. Double check what you find here independently for yourself.'
    
    #info = f""            

    st.markdown(f"{title}")
    st.markdown(f"{explainer_text}")
    #"compare counties in the US by cancer incidence rates. The reported rates show age adjusted cases per 100,000 inhabitants.\
    #                The data is taken from the [National Cancer Institute](https://statecancerprofiles.cancer.gov/map/map.noimage.php) showing the average annual rate between 2014-2018.\
    #                Since cancer rates seem to be a proxy for pollution, the sidebar provides the option to display industrial facilities on the map.\
    #                At the moment, the only available facilities are those that report their emissions anually to the [EPA (2020)](https://www.epa.gov/ghgreporting/data-sets). Mining is not yet included.\
    #                To customize your analysis, use the available options on the sidebar.'
    
    cancer_rate_check_box = st.sidebar.checkbox("Visualize Cancer Rates")
    
    
    cancer_df = load_and_prepare_cancer_df()
    df = load_and_prepare_sites_df(address)
    color_dict = compute_color_dict(df, [[255, 0, 0], [0, 255, 0], [0, 0, 255]])
    
    
    
    
    #
    filtered_df = filter_df_by_distance(df, max_dist)
    final_filtered_df = filtered_df.copy()
    final_filtered_df["elevation_value"] = 100
    final_filtered_df["color"] = final_filtered_df["DATASET"].apply(lambda x: color_dict.get(x, x))
    
    cancer_filtered_df = cancer_df[cancer_df["State"].isin(final_filtered_df["STATE_LOCA"].unique())]
    
    tooltip = {"html": "<b>{SITE_NAME}</b><br/>{COMMODITY}<br/>{distance} km ({angle})"}

    
    icon_data = {
        # Icon from Wikimedia, used the Creative Commons Attribution-Share Alike 3.0
        # Unported, 2.5 Generic, 2.0 Generic and 1.0 Generic licenses
        "url": ICON_URL,
        "width": 242,
        "height": 242,
        "anchorY": 242,
    }
    
    icon_df = pd.DataFrame({"lon":[address[1]], "lat":[address[0]], "icon_data":[icon_data]})
    
    icon_layer = pdk.Layer(
        type="IconLayer",
        data=icon_df,
        get_icon="icon_data",
        get_size=4,
        size_scale=15,
        get_position=["lon", "lat"],
        pickable=True)
    
    sites_layer = pdk.Layer(
        'ColumnLayer',
        #id="geojson",
        data=final_filtered_df[['LONGITUDE', 'LATITUDE', "elevation_value", "color", 'SITE_NAME', 'COMMODITY', 'distance', 'angle']],
        get_position=['LONGITUDE', 'LATITUDE'],
        radius=2000,
        elevation_scale=10,
        pickable=True,
        #elevation_range=[0, 3000],
        elevation="elevation_value",
        get_color="color",
        extruded=True,
        opacity=0.4,
        coverage=1,
        )
    
    if cancer_rate_check_box == True:
        polygon_layer = pdk.Layer(
            "PolygonLayer",
            cancer_filtered_df, #.iloc[2:115],
            id="geojson",
            opacity=0.4,
            stroked=False,
            get_polygon="coordinates",
            filled=True,
            extruded=True,
            wireframe=True,
            get_elevation="elevation",
            get_fill_color="fill_color",
            get_line_color=[255, 255, 255],
            auto_highlight=True,
            pickable=True,
        )
        layers=[polygon_layer, icon_layer, sites_layer]
    else:
        layers=[icon_layer, sites_layer]
    
    # Add sunlight shadow to the polygons
    sunlight = {
        "@@type": "_SunLight",
        "timestamp": 1564696800000,  # Date.UTC(2019, 7, 1, 22),
        "color": [255, 255, 255],
        "intensity": 1.0,
        "_shadow": True,
    }

    ambient_light = {"@@type": "AmbientLight", "color": [255, 255, 255], "intensity": 1.0}

    lighting_effect = {
        "@@type": "LightingEffect",
        "shadowColor": [0, 0, 0, 0.5],
        "ambientLight": ambient_light,
        "directionalLights": [sunlight],
    }

    view_state = pdk.ViewState(
        **{"latitude": address[0], "longitude": address[1], "zoom": 10, "maxZoom": 16, "pitch": 45, "bearing": 0}
    )
    
    r = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        effects=[lighting_effect],
        map_style=pdk.map_styles.LIGHT,
        tooltip=tooltip,
    )
    
    
            
    st.pydeck_chart(r)
    
    
    

if __name__ == '__main__':
    main()
    