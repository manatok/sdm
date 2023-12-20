import os
import pandas as pd

from .data_prep.utils import add_lat_long_from_pentad
from .plot import plot_map


def get_total(df, species_id=None):
    if species_id is not None and species_id in df.columns:
        return df[species_id].sum()
    else:
        columns_to_sum = df.columns.difference(
            ["pentad", "latitude", "longitude", "total_pentad_observations"]
        )
        return df[columns_to_sum].sum().sum()


def plot_it(df, species_id=None):
    if species_id is not None and species_id in df.columns:
        df["total"] = df[species_id].apply(lambda x: 0 if x == 0 else 1)
    else:
        columns_to_sum = df.columns.difference(["pentad", "latitude", "longitude"])
        df["total"] = df[columns_to_sum].sum(axis=1)
        df["total"] = df["total"].apply(lambda x: 0 if x == 0 else 1)

    plot_map(df, "total", filename=f"{species_id}_preview", alongside=False)


def get_stats(
    aggregate_dir: str,
    ebirds_file: str,
    inat_file: str,
    sabap2_file: str,
    combined_file: str,
    species_id: str = None,
    plot: bool = True,
):
    ebirds_path = os.path.join(aggregate_dir, ebirds_file)
    inat_path = os.path.join(aggregate_dir, inat_file)
    sabap2_path = os.path.join(aggregate_dir, sabap2_file)
    combined_path = os.path.join(aggregate_dir, combined_file)

    df = pd.read_feather(ebirds_path)
    print(f"Total eBird observations: {get_total(df, species_id)}", flush=True)

    df = pd.read_feather(inat_path)
    print(f"Total iNat observations: {get_total(df, species_id)}", flush=True)

    df = pd.read_feather(sabap2_path)
    print(f"Total SABAP2 observations: {get_total(df, species_id)}", flush=True)

    df = pd.read_feather(combined_path)
    print(f"Total observations: {get_total(df, species_id)}", flush=True)

    if plot:
        df = add_lat_long_from_pentad(df)
        plot_it(df, species_id)
