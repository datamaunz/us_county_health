from src.load_packages import *

@st.cache()
def read_data(file_path):
    df = pd.read_csv(file_path, dtype={"FIPS":str})
    if "incidence_rate" in df.columns:
        df = df[df.incidence_rate.isna() == False].copy()
    return df

@st.cache()
def get_all_state_names(df):
    return sorted(list(df["State"].unique()))

@st.cache()
def filter_dataframe(df, selected_items, column):
    return df[df[column].str.contains("|".join(selected_items))]

#@st.cache()
def keep_x_items_in_df(df, number_of_counties, best_or_worst):
    if best_or_worst == "best":
        return df.iloc[:number_of_counties]
    elif best_or_worst == "worst":
        return df.iloc[-1 * number_of_counties:]

def load_geo_json():
    with open('data_files/counties_geo_json.json') as f:
        counties = json.load(f)
    return counties

@st.cache(suppress_st_warning=True)
def plot_county_level_map(df, counties):
    
    fig = px.choropleth(df, 
                        geojson = counties, 
                        locations='FIPS', 
                        color='incidence_rate',
                        color_continuous_scale="rdylgn_r",
                        hover_data=["County", "State", "Recent Trend"],
                        scope="usa",
                        labels={'incidence_rate':'incidence rate'}
                        )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"r":0,"t":0,"l":0,"b":0}
        )
    
    return fig

@st.cache() 
def get_all_sectors(df):
    
    return sorted(list(set([l for sublist in [x.split(",") for x in list(df["Industry Type (sectors)"].unique())] for l in sublist])))

def read_in_datafiles():
    
    df = read_data("data_files/county_level_5_year_average_cleaned.csv")    
    facilities_1_df = read_data("data_files/facilities_1.csv")
    state_names = get_all_state_names(df)
    facilitiy_sectors = get_all_sectors(facilities_1_df)
    counties = load_geo_json()    
    return df, facilities_1_df, state_names, facilitiy_sectors, counties

def create_sidebar_filters(state_names, facilitiy_sectors):
    
    with st.sidebar:
        with st.form("Apply filter"):
            selected_states = st.multiselect("Select states (no selection shows all)", state_names)
            selected_sectors = st.multiselect("Select industrial sectors (no selection shows all)", facilitiy_sectors)
            filter_submission = st.form_submit_button("Apply filter")
            if filter_submission == True:
                selected_states = selected_states
                selected_sectors = selected_sectors
                
            
        show_facilities = st.checkbox("Show industrial facilities")
        col1, col2 = st.columns(2)
        best_or_worst = col1.selectbox("Best or worst counties?", ["best", "worst"], 0)
        number_of_counties = col2.number_input(f"{best_or_worst} X counties", 100)
    return selected_states, selected_sectors, show_facilities, number_of_counties, best_or_worst

def obtain_filtered_dataframes(df, selected_states, facilities_1_df, selected_sectors, number_of_counties, best_or_worst):
    
    
    filtered_df = filter_dataframe(df, selected_states, "State")
    filtered_facility_df = filter_dataframe(facilities_1_df, selected_sectors, "Industry Type (sectors)")
    filtered_reduced_df = keep_x_items_in_df(filtered_df, number_of_counties, best_or_worst)
    return filtered_df, filtered_facility_df, filtered_reduced_df