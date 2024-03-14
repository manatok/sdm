import os
from tqdm import tqdm
import pandas as pd

from .two_km_grid import add_two_km_pentad_from_lat_long


def combine_birdlasser_files(
    birdlasser_dir: str, pentad_list_path: str, aggregate_dir: str, output_file: str
):
    all_files = [f for f in os.listdir(birdlasser_dir) if f.endswith(".csv")]

    # Load the reference pentad list
    reference_df = pd.read_csv(pentad_list_path)[["pentad"]]

    grid_df = pd.read_csv('src/google_ee/assets/grid_2km.csv')

    for file in tqdm(all_files, desc="Processing files"):
        species_id = int(file.split(".")[0])
        # Read the file
        file_path = os.path.join(birdlasser_dir, file)
        observations = pd.read_csv(file_path)

        observations = observations[['locationLatitude', 'locationLongitude']]

        add_two_km_pentad_from_lat_long(
            observations,
            grid_df,
            lat_column_name="locationLatitude",
            lng_column_name="locationLongitude"
        )

        # Group and merge
        grouped = observations.groupby("pentad").size().reset_index(name='observed')
        grouped[species_id] = grouped["observed"].astype(int)
        reference_df = reference_df.merge(
            grouped[["pentad", species_id]], on="pentad", how="left"
        )
        reference_df[species_id] = reference_df[species_id].fillna(0).astype(int)

    # Save output
    output_path = os.path.join(aggregate_dir, output_file)
    reference_df.to_feather(output_path)
    print(reference_df.head())