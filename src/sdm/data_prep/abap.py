import os
import csv
import pandas as pd
import requests

from tqdm import tqdm
from .utils import make_dir_if_not_exists


def download_saba2_species(
    sabap2_id: int, sabap2_data_dir: str, species_url: str, overwrite=False
):
    file_path = f"{sabap2_data_dir}/{sabap2_id}.csv"

    if not overwrite and os.path.exists(file_path):
        print(
            f"File for sabap2_id {sabap2_id} already exists. Skipping download.",
            flush=True,
        )
        return

    download_url = species_url.format(sabap2_id)

    try:
        response = requests.get(download_url)

        if len(response.content) == 0:
            print(f"Downloaded empty file for {sabap2_id}", flush=True)
        else:
            with open(file_path, "wb") as out_file:
                out_file.write(response.content)
    except Exception as e:
        print(f"Error downloading file for {sabap2_id}", e, flush=True)


def download_all(bird_list: str, overwrite=False):
    with open(bird_list, "r") as file:
        reader = csv.DictReader(file)

        for idx, row in enumerate(reader, 1):
            sabap2_id = row["SABAP2_number"]
            download_saba2_species(sabap2_id, overwrite)
            print(f"Download for {sabap2_id} complete.")

    print("Download process complete!")


def combine(
    sabap2_data_dir: str,
    pentad_list_path: str,
    aggregate_dir: str,
    output_file: str,
):
    all_files = [f for f in os.listdir(sabap2_data_dir) if f.endswith(".csv")]

    # Load the reference pentad list
    reference_df = pd.read_csv(pentad_list_path)[["pentad"]]

    for file in tqdm(all_files, desc="Processing files"):
        species_id = int(file.split(".")[0])

        # Read the file
        file_path = os.path.join(sabap2_data_dir, file)
        observations = pd.read_csv(file_path)

        # Filter and processing
        observations.rename(columns={"Pentad": "pentad"}, inplace=True)
        observations["observed"] = observations["Taxonomic_name"].apply(
            lambda x: 0 if x == "-" else 1
        )
        observations["pentad"] = observations["pentad"].str.lower()

        # Group by pentad
        grouped = (
            observations.groupby("pentad")
            .agg({"observed": "sum"})  # Summing up the observations
            .reset_index()
        )

        # Add this species_id observation to a new column
        grouped[str(species_id)] = grouped["observed"].astype(int)

        # Merging the data with the reference dataframe
        reference_df = pd.merge(
            reference_df, grouped[["pentad", str(species_id)]], on="pentad", how="left"
        )
        reference_df[str(species_id)] = (
            reference_df[str(species_id)].fillna(0).astype(int)
        )

    make_dir_if_not_exists(aggregate_dir)
    output_path = os.path.join(aggregate_dir, output_file)
    reference_df.to_feather(output_path)
