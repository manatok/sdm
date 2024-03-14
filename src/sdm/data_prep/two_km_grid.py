import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point

def generate_bounding_box(file):
    df = pd.read_csv(file)

    df[['x', 'y']] = df['IDENTIFIER'].str.split('_', expand=True)
    df['x'] = df['x'].astype(float) / 100
    df['y'] = -df['y'].astype(float) / 100

    unique_x = sorted(df['x'].unique())
    unique_y = sorted(df['y'].unique(), reverse=True)  # Reverse because y decreases going down

    def create_next_value_mapping_with_delta(sorted_list):
        mapping = {}
        # Calculate the delta for the last two values
        last_delta = sorted_list[-1] - sorted_list[-2]

        for i, value in enumerate(sorted_list):
            if i + 1 < len(sorted_list):
                mapping[value] = sorted_list[i + 1]
            else:
                # Apply the last delta for the edge case
                mapping[value] = value + last_delta
        return mapping

    # Creating mappings with deltas for 'x' and 'y'
    x_mapping_delta = create_next_value_mapping_with_delta(unique_x)
    # For 'y', since we're working with reverse sorted values, we apply the negative delta
    y_mapping_delta = create_next_value_mapping_with_delta(unique_y)

    # Applying the new mappings to 'df'
    df['x_max'] = df['x'].map(x_mapping_delta)
    # Adjusting for 'y_min' considering 'y' values are sorted in reverse for mapping
    df['y_min'] = df['y'].map(y_mapping_delta)

    # Updating the DataFrame to include only the necessary columns and renaming for clarity
    final_df_grid_delta = df[['IDENTIFIER', 'x', 'x_max', 'y', 'y_min']]
    final_df_grid_delta.columns = ['pentad', 'x_min', 'x_max', 'y_max', 'y_min']

    final_df_grid_delta.to_csv('src/data/two_km_grid/google_ee/grid.csv')

    print(final_df_grid_delta.shape)
    print(final_df_grid_delta.head())

    # plot_map(final_df_grid_delta)


def find_2km_pentad(x, y, grid_df):
    filtered_df = grid_df[(grid_df['x_min'] <= x) & (grid_df['x_max'] >= x) & (grid_df['y_min'] <= y) & (grid_df['y_max'] >= y)]
    if len(filtered_df) > 0:
        return filtered_df["pentad"].iloc[0]
    return None

def add_two_km_pentad_from_lat_long(
    df: pd.core.frame.DataFrame,
    grid_df,
    lat_column_name: str = "decimalLatitude",
    lng_column_name: str = "decimalLongitude",
    pentad_column_name: str = "pentad",
) -> pd.core.frame.DataFrame:
    # Create the pentad column based on latitude and longitude values
    df[pentad_column_name] = df.apply(
        lambda row: find_2km_pentad(row[lng_column_name], row[lat_column_name], grid_df), axis=1
    )
    return df

def add_lat_long_from_two_km_pentad(
    df: pd.core.frame.DataFrame,
    lat_column_name: str = "latitude",
    lng_column_name: str = "longitude",
    pentad_column_name: str = "pentad",
) -> pd.core.frame.DataFrame:
    """
    Add a latitude and longitude column to the dataframe based on the pentad
    """
    df[[lng_column_name, lat_column_name]] = df[pentad_column_name].str.split('_', expand=True)
    df[lng_column_name] = df[lng_column_name].astype(float) / 100
    df[lat_column_name] = -df[lat_column_name].astype(float) / 100

    return df


def plot_map_2km(df, total_column):
    map = gpd.GeoSeries([Point(v) for v in df[["longitude", "latitude"]].values])

    # Define plot configurations
    config = {
        "title": "Pentad - Scaled View",
        "xlim": [15.5, 33.5],
        "ylim": [-36, -20.5],
        "s": 2,
    }

    # Configure plots
    fig, ax = plt.subplots(figsize=(15, 8))

    map.plot(color="lightgrey", ax=ax)

    x = df["longitude"]
    y = df["latitude"]
    z = df[total_column]

    sc = ax.scatter(x, y, c=z, s=config["s"], marker="s")
    fig.colorbar(sc, ax=ax, label='foo')

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(config["title"])
    ax.set_xlim(config["xlim"])
    ax.set_ylim(config["ylim"])

    plt.show()