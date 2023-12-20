import os
import numpy as np
import pandas as pd
import pyarrow.feather as feather
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm


def scale_covariates(covariates_df: pd.core.frame.DataFrame) -> pd.core.frame.DataFrame:
    scaler = StandardScaler()
    X = covariates_df.drop("pentad", axis=1)
    X_scaled = scaler.fit_transform(X)

    df_scaled = pd.DataFrame(X_scaled, columns=X.columns)

    # Add the 'pentad' column back to the scaled DataFrame
    return pd.concat([covariates_df["pentad"], df_scaled], axis=1)


def combine_and_scale_all_covariates(
    combined_google_ee_file: str,
    combined_bioclim_file: str,
    output_dir: str,
    output_file_name: str,
    force_reload=True,
) -> pd.core.frame.DataFrame:
    """
    Combine the Google EE + Bioclim data
    """
    # first check if the processed version of the file exists

    feather_path = output_dir + "/" + output_file_name

    combined_google_ee_feather_path = output_dir + "/" + combined_google_ee_file
    combined_bioclim_feather_path = output_dir + "/" + combined_bioclim_file

    if os.path.exists(feather_path) and not force_reload:
        print("Cached scaled covariates file already exists...")
        return
    else:
        # load and flatten all of the bioclim files
        df_covariates = feather.read_feather(combined_google_ee_feather_path)
        # load the covariates exported from Google EE
        df_google_ee_covariates = feather.read_feather(combined_bioclim_feather_path)

        df_final = pd.merge(
            df_covariates, df_google_ee_covariates, on="pentad", how="left"
        )

        # # Fill in any missing values with NaN
        df_final.fillna(value=np.nan, inplace=True)

        # # Scale the values
        df_scaled = scale_covariates(df_final)

        # # Make sure the letters in the pentad column are all lowercase
        df_scaled["pentad"] = df_scaled["pentad"].str.lower()

        mean_values = df_scaled.loc[:, df_scaled.columns != "pentad"].mean()

        # Fill NA with mean values for all columns except 'pentad'
        df_scaled.loc[:, df_scaled.columns != "pentad"] = df_scaled.loc[
            :, df_scaled.columns != "pentad"
        ].fillna(mean_values)

        # # We will read from this file next time
        feather.write_feather(df_scaled, feather_path)


def combine_bioclim(
    bioclim_dir: str, output_dir: str, output_file_name: str, force_reload=False
) -> pd.core.frame.DataFrame:
    feather_path = output_dir + "/" + output_file_name

    if os.path.exists(feather_path) and not force_reload:
        print("Found existing file...")
        return

    csv_files = [f for f in os.listdir(bioclim_dir) if f.endswith(".csv")]

    # Initialize an empty list to hold the DataFrames
    dfs = []

    # Iterate over all the CSV files and add them to the list
    for file in tqdm(csv_files, desc="Processing files"):
        file_path = os.path.join(bioclim_dir, file)
        # Read the CSV file into a DataFrame with the 'Name' column as the index
        df = pd.read_csv(file_path, usecols=["Name", "MEAN"], dtype=str)
        # Remove the '.csv' suffix from the filename
        col_name = file.split("/")[-1].rstrip(".csv").lower()
        # Rename the 'MEAN' column with the filename
        df.rename(columns={"MEAN": col_name, "Name": "pentad"}, inplace=True)
        # Add the DataFrame to the list
        dfs.append(df.set_index("pentad"))

    # Concatenate all the DataFrames along the columns axis (axis=1)
    df_final = pd.concat(dfs, axis=1, sort=False, join="outer")
    # Convert the pentad column into a regular column again
    df_final.reset_index(inplace=True)

    feather.write_feather(df_final, feather_path)


def combine_google_ee_covariates(
    google_ee_dir: str, output_dir: str, output_file_name: str, force_reload=False
) -> pd.core.frame.DataFrame:
    feather_path = output_dir + "/" + output_file_name

    if os.path.exists(feather_path) and not force_reload:
        print("Found existing file...")

    # Get a list of all CSV files in the folder
    csv_files = [f for f in os.listdir(google_ee_dir) if f.endswith(".csv")]

    # Initialize an empty DataFrame
    merged_df = None

    # Iterate over the CSV files
    for file in tqdm(csv_files, desc="Processing files"):
        file_path = os.path.join(google_ee_dir, file)
        # Read each CSV file into a DataFrame
        df = pd.read_csv(file_path)

        # Check if merged_df is empty (first iteration)
        if merged_df is None:
            # Set merged_df to the current DataFrame
            merged_df = df
        else:
            # Merge the current DataFrame with the existing merged_df based on the 'pentad' column
            merged_df = merged_df.merge(df, on="pentad", how="outer")

    # We will read from this file next time
    feather.write_feather(merged_df, feather_path)
