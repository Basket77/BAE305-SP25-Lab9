import pandas as pd
import folium
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates

def filter_data_by_criteria(df, characteristics, start_date=None, end_date=None, value_ranges=None):
    """
    Filters the merged DataFrame based on selected characteristics, date range, and value ranges.

    Args:
        df (pd.DataFrame): The merged DataFrame containing measurement data.
        characteristics (list): A list of characteristic names to filter by.
        start_date (str or datetime, optional): Start date for filtering (e.g., 'YYYY-MM-DD').
        end_date (str or datetime, optional): End date for filtering (e.g., 'YYYY-MM-DD').
        value_ranges (dict, optional): A dictionary where keys are characteristic names
                                      and values are tuples (min_value, max_value).

    Returns:
        pd.DataFrame: A filtered DataFrame.
    """
    filtered_df = df.copy()

    if characteristics:
        filtered_df = filtered_df[filtered_df['CharacteristicName'].isin(characteristics)]

    if start_date:
        filtered_df = filtered_df[filtered_df['ActivityStartDate'] >= pd.to_datetime(start_date)]
    if end_date:
        filtered_df = filtered_df[filtered_df['ActivityStartDate'] <= pd.to_datetime(end_date)]

    if value_ranges:
        for char, (min_val, max_val) in value_ranges.items():
            # Apply value range filter only for the specific characteristic
            char_mask = (filtered_df['CharacteristicName'] == char)
            value_mask = (filtered_df['ResultMeasureValue'] >= min_val) & \
                         (filtered_df['ResultMeasureValue'] <= max_val)
            filtered_df = filtered_df[~char_mask | (char_mask & value_mask)]

    return filtered_df

def generate_filtered_map(station_df, filtered_data):
    """
    Generates an interactive Folium map showing only the stations present in the filtered_data.

    Args:
        station_df (pd.DataFrame): The original station DataFrame.
        filtered_data (pd.DataFrame): The DataFrame resulting from filtering, containing
                                      'MonitoringLocationIdentifier', 'LatitudeMeasure',
                                      and 'LongitudeMeasure' for the relevant stations.

    Returns:
        folium.Map: An interactive Folium map.
    """
    if filtered_data.empty:
        print("No data to display on the map after filtering.")
        # Return a default map or handle as appropriate
        return folium.Map(location=[0, 0], zoom_start=2)

    # Get unique station identifiers from the filtered data
    unique_filtered_station_ids = filtered_data['MonitoringLocationIdentifier'].unique()

    # Filter the original station_df to get details for only these stations
    map_stations_df = station_df[
        station_df['MonitoringLocationIdentifier'].isin(unique_filtered_station_ids)
    ].drop_duplicates(subset=['MonitoringLocationIdentifier'])

    if map_stations_df.empty:
        print("No stations found in the original station_df matching the filtered data.")
        return folium.Map(location=[0, 0], zoom_start=2)

    # Identify latitude, longitude, and display name columns
    lat_col_name = 'LatitudeMeasure'
    lon_col_name = 'LongitudeMeasure'
    display_name_col = 'MonitoringLocationName'

    # Calculate map center from filtered stations
    center_lat = map_stations_df[lat_col_name].mean()
    center_lon = map_stations_df[lon_col_name].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=6)

    # Add markers for each filtered station
    for index, row in map_stations_df.iterrows():
        station_name = row[display_name_col] if display_name_col in row else row['MonitoringLocationIdentifier']
        if pd.notna(row[lat_col_name]) and pd.notna(row[lon_col_name]):
            folium.Marker(
                location=[row[lat_col_name], row[lon_col_name]],
                popup=f"<b>Station:</b> {station_name}<br><b>Lat:</b> {row[lat_col_name]:.2f}<br><b>Lon:</b> {row[lon_col_name]:.2f}",
                tooltip=station_name
            ).add_to(m)
    return m

def plot_filtered_trends(filtered_data, characteristics):
    """
    Plots water quality characteristic trends over time for filtered data.

    Args:
        filtered_data (pd.DataFrame): The filtered DataFrame.
        characteristics (list): A list of characteristic names that were filtered for.
    """
    if filtered_data.empty:
        print("No data to plot after filtering.")
        return

    for char_name in characteristics:
        char_df = filtered_data[filtered_data['CharacteristicName'] == char_name].copy()

        if char_df.empty:
            print(f"No data found for characteristic '{char_name}' in the filtered set.")
            continue

        plt.figure(figsize=(18, 8))
        sns.lineplot(
            data=char_df.sort_values(by='ActivityStartDate'),
            x='ActivityStartDate',
            y='ResultMeasureValue',
            hue='MonitoringLocationName',
            marker='o',
            linewidth=1,
            alpha=0.8
        )
        plt.title(f'Filtered Water Quality Trend: {char_name} Over Time by Monitoring Site')
        plt.xlabel('Date')
        plt.ylabel(f'{char_name} Value')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend(title='Monitoring Site', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xticks(rotation=45, ha='right')
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.tight_layout()
        plt.show()
