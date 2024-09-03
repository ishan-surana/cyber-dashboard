import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from flask import Flask, jsonify, request, render_template
import altair as alt

plt.switch_backend('Agg')
app = Flask(__name__)
df = pd.read_csv('data/cyber_incidents.csv')
india_map = gpd.read_file('data/map/Indian_states.shp')

@app.route('/')
def index():
    return render_template('index.html', tabs=df.drop(columns=['Date', 'Impact']).columns.tolist())

@app.route('/get_options')
def get_options():
    tab = request.args.get('tab').replace(' ', '_')
    return jsonify({'options': df[tab].unique().tolist()})

@app.route('/stats')
def get_stats():
    start_date, end_date = request.args.get('start_date'), request.args.get('end_date')
    if start_date == '' or end_date == '':
        filtered_df = df
    else:
        filtered_df = df[(pd.to_datetime(df['Date']) >= pd.to_datetime(start_date)) & (pd.to_datetime(df['Date']) <= pd.to_datetime(end_date))]
    mean_impact = filtered_df['Impact'].mean()
    median_impact = filtered_df['Impact'].median()
    max_impact = float(filtered_df['Impact'].max())
    min_impact = float(filtered_df['Impact'].min())
    stats = {'mean_impact': mean_impact, 'median_impact': median_impact, 'max_impact': max_impact, 'min_impact': min_impact}
    return jsonify(stats)

@app.route('/get_incidents')
def get_incidents():
    n = int(request.args.get('n'))
    start_date, end_date = request.args.get('start_date'), request.args.get('end_date')
    if start_date == '' or end_date == '':
        data = df[['Date', 'State', 'Sector', 'Impact', 'Attack_Type']]
    else:
        data = df[(pd.to_datetime(df['Date']) >= pd.to_datetime(start_date)) & (pd.to_datetime(df['Date']) <= pd.to_datetime(end_date))]
    data = data[['Date', 'State', 'Sector', 'Impact', 'Attack_Type']].sort_values('Impact', ascending=False).head(n)
    data['Date'] = pd.to_datetime(data['Date']).dt.strftime('%Y-%m-%d')
    return jsonify(data.to_dict(orient='records'))

@app.route('/get_heatmap')
def get_heatmap():
    start_date, end_date = pd.to_datetime(request.args.get('start_date')), pd.to_datetime(request.args.get('end_date'))
    tab, option = request.args.get('tab').replace(' ', '_'), request.args.get('option').replace(' ', '_')
    if str(start_date) == 'NaT' or str(end_date) == 'NaT' or start_date == '' or end_date == '':
        filtered_df = df
    else:
        filtered_df = df[(pd.to_datetime(df['Date']) >= pd.to_datetime(start_date)) & (pd.to_datetime(df['Date']) <= pd.to_datetime(end_date))]
    heatmap_data = filtered_df.groupby([tab, option])['Impact'].mean().reset_index()
    heatmap = alt.Chart(heatmap_data).mark_rect().encode(
            x=alt.X(tab + ':O', axis=alt.Axis(labelColor='white', titleColor='white', tickColor='white', domainColor='white')),
            y=alt.Y(option + ':O', axis=alt.Axis(labelColor='white', titleColor='white', tickColor='white', domainColor='white')),
            color='Impact:Q',
            tooltip=[tab, option, 'Impact']
        ).properties(width=650, height=400
        ).configure(background='black'
        ).configure_legend(labelColor='white', titleColor='white')
    img = io.BytesIO()
    heatmap.save('heatmap.png')
    with open('heatmap.png', 'rb') as f:
        img.write(f.read())
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    img.close()
    return jsonify({'plot_url': f'data:image/png;base64,{plot_url}'})
    
@app.route('/map')
def map():
    tab = request.args.get('tab').replace(' ', '_')
    start_date, end_date = pd.to_datetime(request.args.get('start_date')), pd.to_datetime(request.args.get('end_date'))
    if str(start_date) == 'NaT' or str(end_date) == 'NaT' or start_date == '' or end_date == '':
        filtered_df = df
    else:
        filtered_df = df[(pd.to_datetime(df['Date']) >= pd.to_datetime(start_date)) & (pd.to_datetime(df['Date']) <= pd.to_datetime(end_date))]
    if tab == 'State':
        states = request.args.get('options')
        states = states.split(',')
        filtered_df = filtered_df[filtered_df['State'].isin(states)]

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
            print(e)
            # Print line number of error
            india_map.plot(ax=ax, color='gray', facecolor='none')

        fig.set_facecolor('None')
        ax.set_axis_off()

        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', transparent=True)
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        return jsonify({'plot_url': f'data:image/png;base64,{plot_url}'})
    
    if tab == 'Sector':
        sectors = request.args.get('options')
        sectors = sectors.split(',')
        filtered_df = filtered_df[filtered_df['Sector'].isin(sectors)].groupby(tab).size().reset_index(name='Counts')
        chart = alt.Chart(filtered_df).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Counts", type="quantitative"),
            color=alt.Color(field="Sector", type="nominal"),
            tooltip=['Sector', 'Counts:Q'])
    elif tab == 'Month':
        months = request.args.get('options')
        months = [int(month) for month in months.split(',')] if months else []
        filtered_df = filtered_df[filtered_df['Month'].isin(months)].groupby(tab).size().reset_index(name='Counts')
        chart = alt.Chart(filtered_df).mark_line(point=True).encode(
            x=alt.X('Month:N', sort=['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'], axis=alt.Axis(labelColor='white', titleColor='white', tickColor='white', domainColor='white')),
            y=alt.Y('Counts:Q', axis=alt.Axis(labelColor='white', titleColor='white', tickColor='white', domainColor='white')),
            tooltip=['Month', 'Counts:Q'])
    elif tab == 'Year':
        years = request.args.get('options')
        print("Years: ", years)
        years = [int(year) for year in years.split(',')] if years else []
        filtered_df = filtered_df[filtered_df['Year'].isin(years)].groupby(tab).size().reset_index(name='Counts')
        chart = alt.Chart(filtered_df).mark_line(point=True).encode(
            x=alt.X('Year:N', sort='-x', axis=alt.Axis(labelColor='white', titleColor='white', tickColor='white', domainColor='white')),
            y=alt.Y('Counts:Q', axis=alt.Axis(labelColor='white', titleColor='white', tickColor='white', domainColor='white')),
            tooltip=['Year', 'Counts:Q'])
    elif tab == 'Attack_Type':
        attack_types = request.args.get('options')
        attack_types = attack_types.split(',')
        filtered_df = filtered_df[filtered_df['Attack_Type'].isin(attack_types)].groupby(tab).size().reset_index(name='Counts')
        chart = alt.Chart(filtered_df).mark_bar().encode(
            x=alt.X('Counts:Q', axis=alt.Axis(labelColor='white', titleColor='white', tickColor='white', domainColor='white')),
            y=alt.Y('Attack_Type:N', sort='-x', axis=alt.Axis(labelColor='white', titleColor='white', tickColor='white', domainColor='white')),
            color=alt.Color('Counts:Q', scale=alt.Scale(scheme='viridis')),
            tooltip=['Attack_Type', 'Counts:Q'])

    chart = chart.properties(width=700, height=300
        ).configure(background='black'
        ).configure_legend(labelColor='white', titleColor='white')

    img = io.BytesIO()
    chart.save('chart.png')
    with open('chart.png', 'rb') as f:
        img.write(f.read())
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    img.close()
    return jsonify({'plot_url': f'data:image/png;base64,{plot_url}'})

if __name__ == '__main__':
    app.run(debug=True)