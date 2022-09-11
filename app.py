import streamlit as st
#import geopandas as gpd
import pandas as pd
import json
#import plotly.figure_factory as ff
#import plotly.graph_objs as go
import plotly.express as px


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
            selected_states = st.multiselect("Select states", state_names)
            selected_sectors = st.multiselect("Select industry sectors", facilitiy_sectors)
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

def main():
        
    st.set_page_config(
    layout="wide",
    page_title="County Analysis",
    page_icon = "💚"
    )
    
    df, facilities_1_df, state_names, facilitiy_sectors, counties = read_in_datafiles()
    selected_states, selected_sectors, show_facilities, number_of_counties, best_or_worst = create_sidebar_filters(state_names, facilitiy_sectors)
    filtered_df, filtered_facility_df, filtered_reduced_df = obtain_filtered_dataframes(df, selected_states, facilities_1_df, selected_sectors, number_of_counties, best_or_worst)
    
    
    title = f"### You're looking at the {len(filtered_reduced_df)} {best_or_worst} counties out of {len(filtered_df)} ({round(len(filtered_reduced_df) / len(filtered_df) *100)}%)"
    explainer_text = f'This app is meant to compare counties in the US by cancer incidence rates. The reported rates show age adjusted cases per 100,000 inhabitants. The data is taken from the [National Cancer Institute](https://statecancerprofiles.cancer.gov/map/map.noimage.php) showing sites between 2014-2018.\
        Since cancer rates seem to be a proxy for pollution, the sidebar provides the option to display industrial facilities on the map.\
            At the moment, only those facilities are available that report their emissions anually to the EPA. Mining is not yet included.'
            

    st.markdown(title)
    st.markdown(explainer_text)
    st.markdown("---")
    
    
    filtered_reduced_df['quantiles'], bins = pd.qcut(filtered_reduced_df["incidence_rate"], q=10, retbins=True, labels=range(1,11))
    filtered_reduced_df['quantiles'] = filtered_reduced_df['quantiles'].astype(int)
    legend_dict = {x:f'{round(bins[i])} - {round(bins[i+1])}' for i, x in enumerate(range(1,11))}
    filtered_reduced_df['bin'] = filtered_reduced_df['quantiles'].apply(lambda x: legend_dict.get(x))
    
    #quantiles = pd.qcut(filtered_reduced_df["incidence_rate"], q=10, retbins=False)
    #filtered_reduced_df["labels"] = labels
    
    
    fig = px.choropleth(filtered_reduced_df, 
                        geojson = counties, 
                        locations='FIPS', 
                        #color='incidence_rate',
                        color='quantiles',
                        #color='bin',
                        color_continuous_scale="rdylgn_r",
                        hover_data=["County", "State", "Recent Trend", "incidence_rate"],
                        scope="usa",
                        category_orders = legend_dict
                        #labels = legend_dict,
                        #labels={'incidence_rate':'incidence rate'}
                        )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"r":0,"t":0,"l":0,"b":0},
        
        )
    
    if show_facilities == True:
    
        fig2 = px.scatter_geo(filtered_facility_df[filtered_facility_df.State.str.contains("|".join(selected_states))], lat="Latitude", lon="Longitude", locationmode="ISO-3", hover_data=["Industry Type (sectors)", "Facility Name", "Total reported direct emissions", "emission_types"]) # , symbol="Industry Type (sectors)"
        fig.add_trace(fig2.data[0])
    
    #fig = plot_county_level_map(filtered_reduced_df, counties)
    st.plotly_chart(fig, use_container_width=True)
    
    quantile_legend_df = pd.DataFrame(legend_dict, index=["rates"])
    st.write(quantile_legend_df)
    
    
    
    with st.expander("Table view"):
        st.dataframe(filtered_reduced_df)
    
    
    
    #page_names_to_funcs = {
    #    "✍️ Create Writeup": display_submission_page,
    #    "💿 Load Writeup": display_load_submission_page,
    #    "🔭 Overview and bulk download": hypothesis_overview_page,
    #    "👩‍🔬 Update Hypotheses": display_update_db_page
    #    }
    #selected_page = st.sidebar.selectbox("What would you like to do?", page_names_to_funcs.keys())
    #page_names_to_funcs[selected_page]()
    
    
    #except:
    #    st.experimental_rerun()
    
    
    
    
if __name__ == '__main__':
    main()
    