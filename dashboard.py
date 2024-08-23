import pandas as pd
import streamlit as st
import altair as alt

# Load data
df = pd.read_csv('cyber_incidents.csv')
# Make the streamlit element title in the center
st.markdown("""
    <style>
    div.row-widget.stRadio > div {
        flex-direction: row;
        justify-content: center;
    }
    .stRadio > label {
        text-align: center;
        justify-content: center;
        margin-top: 0px;
    }
    .stRadio label {
        margin-right: 10px;
    }
    .reportview-container .main .block-container {
        margin-bottom: 0;
    }
    div.block-container {
        padding-bottom: 10px;
        padding-top: 10px;
    }
    h1 {
        text-align: center;
    }
    summary {
        padding: 0px;
    }
    </style>
    """, unsafe_allow_html=True)

# Title
st.title("Cyber Incident Dashboard")

# Toggle Option for Drill-Down Basis
features = df.drop(columns=['Date', 'Impact']).columns.to_list()

drill_down_basis = st.radio(
    "Choose Drill-Down Basis:",
    ('Month', 'State', 'Sector', 'Attack_Type')
)

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
        x='Month:T',
        y='Counts:Q'
    ).properties(width=700, height=300)
else:
    chart = alt.Chart(incidents_by_drill_down).mark_bar().encode(
        x='Counts:Q',
        y=alt.Y(drill_down_basis + ':N', sort='-x')
    ).properties(width=700, height=300)
st.altair_chart(chart)

# Visualization: Impact Heatmap based on Drill-Down Basis with other filters. DIalog, framgementer
with st.expander("Visualise Impact Heatmap based on Drill-Down Basis"):
    second_feature = st.selectbox("Select Second Feature:", [f for f in features if f!=drill_down_basis])
    heatmap_data = filtered_df.groupby([drill_down_basis, second_feature])['Impact'].mean().reset_index()
    chart2 = alt.Chart(heatmap_data).mark_rect().encode(
        x=drill_down_basis + ':O',
        y=second_feature + ':O',
        color='Impact:Q'
    ).properties(width=650, height=400)
    st.altair_chart(chart2)

# st.subheader("Impact of Incidents by State and Sector")
# heatmap_data = filtered_df.groupby([drill_down_basis, 'Sector'])['Impact'].mean().reset_index()
# chart = alt.Chart(heatmap_data).mark_rect().encode(
#     x='Sector:O',
#     y=drill_down_basis + ':O',
#     color='Impact:Q'
# ).properties(width=700, height=400)
