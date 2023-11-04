import os
import pandas as pd


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
    print(df.head())
    print(df.shape)

    df = pd.read_feather(inat_path)
    print(df.head())
    print(df.shape)

    df = pd.read_feather(sabap2_path)
    print(df.head())
    print(df.shape)
#     # total_observations = 

#     # df_inat = pd.read_feather(inat_path)
#     # df_sabap2 = pd.read_feather(sabap2_path)