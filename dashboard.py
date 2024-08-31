import pandas as pd
import streamlit as st
import altair as alt
import geopandas as gpd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('cyber_incidents.csv')
features = df.drop(columns=['Date', 'Impact']).columns.to_list()
india_map = gpd.read_file('map/Indian_states.shp')

# Dashboard Title
st.markdown("""
    <style>div.block-container {
        padding-bottom: 10px;
        padding-top: 30px;
    }
    h2 {
        margin-top: -40px;
        margin-bottom: 0px;
        text-align: center;
    }
    </style>
    <h1 style='text-align: center;'>Cyber Incident Dashboard</h1>       
""", unsafe_allow_html=True)

@st.dialog("Top Incidents")
def show_top5(filtered_df, n):
    st.table(filtered_df.nlargest(n, 'Impact'))

# Sidebar for Global Filters
with st.sidebar:
    st.header("Global Filters")
    date_range = st.date_input("Date Range", [], min_value=pd.to_datetime(df['Date']).min(), max_value=pd.to_datetime(df['Date']).max(), format="DD-MM-YYYY")
    impact_filter = st.slider("Impact Range", int(df['Impact'].min()), int(df['Impact'].max()), (int(df['Impact'].min()), int(df['Impact'].max())))
    # Show mean, median, max, min for selected date range and impact range
    st.markdown("### Summary Statistics")
    col1, col2 = st.columns(2)
    filtered_df = df.copy()
    if date_range and len(date_range) == 2:
        filtered_df = df[(pd.to_datetime(df['Date']) >= pd.to_datetime(date_range[0])) & (pd.to_datetime(df['Date']) <= pd.to_datetime(date_range[1]))]
    filtered_df = filtered_df[(filtered_df['Impact'] >= impact_filter[0]) & (filtered_df['Impact'] <= impact_filter[1])]
    # Create a dialog box to show the top 5 incidents per drill-down basis
    st.sidebar.subheader("Customize View")
    show_top_incidents = st.slider("Show Top N Incidents", min_value=1, max_value=10, value=5)
    if st.button(f"View Top {show_top_incidents} incidents"):
        show_top5(filtered_df=filtered_df, n=show_top_incidents)
    col1.metric("Mean Impact", round(filtered_df['Impact'].mean(), 2))
    col2.metric("Median Impact", round(filtered_df['Impact'].median(), 2))
    col1.metric("Max Impact", filtered_df['Impact'].max())
    col2.metric("Min Impact", filtered_df['Impact'].min())
    # Show top 5 incidents for selected date range and impact range in a dialog box

# Define tab names and their associated content
tab_names = ['Month', 'State', 'Sector', 'Attack Type']

# Create tabs
tabs = st.tabs(tab_names)

# Create a dictionary to map tab titles to DataFrame columns
tab_column_mapping = {
    'Month': 'Month',
    'State': 'State',
    'Sector': 'Sector',
    'Attack Type': 'Attack_Type'
}

# Iterate over tabs to handle different drill-down bases
for tab, tab_name in zip(tabs, tab_names):
    with tab:
        drill_down_basis = tab_column_mapping[tab_name]

        # Key Metrics at the top
        st.markdown("### Key Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Incidents", len(df))
        col2.metric("Average Impact", round(df['Impact'].mean(), 2))
        if drill_down_basis == 'Attack_Type':
            col3.metric("Most Common Attack Type", df['Attack_Type'].mode()[0])
        elif drill_down_basis == 'Month':
            col3.metric("Most Affected Month", {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}[df['Month'].mode()[0]])
        else:
            col3.metric(f"Most Affected {drill_down_basis}", df[drill_down_basis].mode()[0])

        # Make a select all button
        if f"{drill_down_basis}_select_all" not in st.session_state:
            st.session_state[f"{drill_down_basis}_select_all"] = True
        if f"{drill_down_basis}_selected_options" not in st.session_state:
            st.session_state[f"{drill_down_basis}_selected_options"] = df[drill_down_basis].unique().tolist()

        if st.button(f"Toggle Select 'All {tab_name}s'"):
            if st.session_state[f"{drill_down_basis}_select_all"]:
                selected_options = df[drill_down_basis].unique().tolist()
                st.write("All selected toggled!")
            else:
                selected_options = []
                st.write("All deselected toggled!")
            st.session_state[f"{drill_down_basis}_selected_options"] = selected_options
            st.session_state[f"{drill_down_basis}_select_all"] = not st.session_state[f"{drill_down_basis}_select_all"]

        selected_options = st.multiselect(f"Select {drill_down_basis}(s)", options=df[drill_down_basis].unique(), default=st.session_state[f"{drill_down_basis}_selected_options"])

        filtered_df = df[df[drill_down_basis].isin(selected_options)]
        if date_range and len(date_range) == 2:
            filtered_df = filtered_df[(pd.to_datetime(filtered_df['Date']) >= pd.to_datetime(date_range[0])) & (pd.to_datetime(filtered_df['Date']) <= pd.to_datetime(date_range[1]))]
        filtered_df = filtered_df[(filtered_df['Impact'] >= impact_filter[0]) & (filtered_df['Impact'] <= impact_filter[1])]
        st.subheader(f"Incidents by {tab_name}")
        incidents_by_drill_down = filtered_df.groupby(drill_down_basis).size().reset_index(name='Counts')
        if drill_down_basis == 'Sector':
            chart = alt.Chart(incidents_by_drill_down).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="Counts", type="quantitative"),
                color=alt.Color(field="Sector", type="nominal"),
                tooltip=['Sector', 'Counts']
            ).properties(width=700, height=300)
        elif drill_down_basis == 'Month':
            chart = alt.Chart(incidents_by_drill_down).mark_line(point=True).encode(
                x=alt.X('Month:N', sort=['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']),
                y='Counts:Q',
                tooltip=['Month', 'Counts']
            ).properties(width=700, height=300)
        elif drill_down_basis == 'State':
            fig, ax = plt.subplots(1, 1, figsize=(10, 10))
            india_map.boundary.plot(ax=ax, color='black', facecolor='none')
            try:
                india_map.plot(ax=ax, color='white', facecolor='none')
                merged_map = india_map.merge(filtered_df.rename(columns={'State': 'state'}).groupby('state').size().reset_index(name='Impact'), on='state').plot(ax=ax, column='Impact', cmap='YlOrRd', legend=False)
                # Create a colorbar
                sm = plt.cm.ScalarMappable(cmap='YlOrRd', norm=plt.Normalize(vmin=df['Impact'].min(), vmax=df['Impact'].max()))
                sm.set_array([])
                cbar = plt.colorbar(sm, ax=ax, orientation='vertical', fraction=0.03, pad=0.04)
                # cbar.set_label('Impact')
                cbar.ax.tick_params(labelsize='small')
                # cbar.ax.yaxis.label.set_color('white')  # Set colorbar label color to white
                cbar.ax.yaxis.set_tick_params(color='white', labelcolor='white')  # Set colorbar ticks color to white
                cbar.outline.set_edgecolor('black')  # Set colorbar border color
                cbar.ax.set_facecolor('black')  # Set colorbar background color
                cbar.ax.patch.set_edgecolor('black')  # Set colorbar border color

                fig.subplots_adjust(right=0.85)  # Adjust the right side of the plot to make space for title
                cbar.ax.text(0.7, 1.05, 'Impact', ha='center', va='center', color='white', fontsize='13', fontweight='bold', transform=cbar.ax.transAxes)
            except Exception as e:
                india_map.plot(ax=ax, color='gray', facecolor='none')

            fig.set_facecolor('None')
            ax.set_axis_off()
        else:
            chart = alt.Chart(incidents_by_drill_down).mark_bar().encode(
                x='Counts:Q',
                y=alt.Y(drill_down_basis + ':N', sort='-x'),
                color=alt.Color('Counts:Q', scale=alt.Scale(scheme='viridis')),
                tooltip=[drill_down_basis, 'Counts']
            ).properties(width=700, height=300).interactive()
        
        if drill_down_basis == 'State':
            st.pyplot(fig)
        else:
            st.altair_chart(chart)

        # Visualization: Impact Heatmap based on Drill-Down Basis
        with st.expander("Visualise Impact Heatmap based on Drill-Down Basis"):
            second_feature = st.selectbox("Select Second Feature:", [f for f in features if f!=drill_down_basis])
            heatmap_data = filtered_df.groupby([drill_down_basis, second_feature])['Impact'].mean().reset_index()
            chart2 = alt.Chart(heatmap_data).mark_rect().encode(
                x=drill_down_basis + ':O',
                y=second_feature + ':O',
                color='Impact:Q',
                tooltip=[drill_down_basis, second_feature, 'Impact']
            ).properties(width=650, height=400)
            st.altair_chart(chart2)