import pandas as pd
import streamlit as st
import altair as alt

# Load data
df = pd.read_csv('cyber_incidents.csv')
# Make the streamlit element title in the center
st.markdown("""
    <style>
    div.block-container {
        padding-bottom: 10px;
        padding-top: 15px;
    }
    h1 {
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# Title
st.title("Cyber Incident Dashboard")

# Toggle Option for Drill-Down Basis
features = df.drop(columns=['Date', 'Impact']).columns.to_list()

# Define tab names and their associated content
tab_names = ['Month', 'State', 'Sector', 'Attack_Type']

# Create tabs
tabs = st.tabs(tab_names)

# Create a dictionary to map tab titles to DataFrame columns
tab_column_mapping = {
    'Month': 'Month',
    'State': 'State',
    'Sector': 'Sector',
    'Attack_Type': 'Attack_Type'
}

# Iterate over tabs to handle different drill-down bases
for tab, tab_name in zip(tabs, tab_names):
    with tab:
        drill_down_basis = tab_name
        
        state_filter = st.multiselect(f"Select {drill_down_basis}(s)", options=df[drill_down_basis].unique(), default=df[drill_down_basis].unique())
        filtered_df = df[df[drill_down_basis].isin(state_filter)]
        st.subheader(f"Incidents by {drill_down_basis}")
        incidents_by_drill_down = filtered_df.groupby(drill_down_basis).size().reset_index(name='Counts')
        
        if drill_down_basis == 'Sector':
            chart = alt.Chart(incidents_by_drill_down).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="Counts", type="quantitative"),
                color=alt.Color(field="Sector", type="nominal")
            ).properties(width=700, height=300)
        elif drill_down_basis == 'Month':
            chart = alt.Chart(incidents_by_drill_down).mark_line(point=True).encode(
                x='Month:N',
                y='Counts:Q'
            ).properties(width=700, height=300)
        else:
            chart = alt.Chart(incidents_by_drill_down).mark_bar().encode(
                x='Counts:Q',
                y=alt.Y(drill_down_basis + ':N', sort='-x')
            ).properties(width=700, height=300)
        
        st.altair_chart(chart)

        # Visualization: Impact Heatmap based on Drill-Down Basis with other filters. DIalog, framgementer
        with st.expander("Visualise Impact Heatmap based on Drill-Down Basis [" + drill_down_basis + "] with other filters"):
            second_feature = st.selectbox("Select Second Feature:", [f for f in features if f!=drill_down_basis])
            heatmap_data = filtered_df.groupby([drill_down_basis, second_feature])['Impact'].mean().reset_index()
            chart2 = alt.Chart(heatmap_data).mark_rect().encode(
                x=drill_down_basis + ':O',
                y=second_feature + ':O',
                color='Impact:Q'
            ).properties(width=650, height=400)
            st.altair_chart(chart2)
