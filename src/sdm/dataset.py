import os
import pandas as pd
import numpy as np


def generate_training(
    target_species_id: str,
    input_data_path: str,
    observations_file: str,
    covariates_file: str,
    absence_observations: int = 10,
) -> pd.core.frame.DataFrame:
    """
    Generate a training dataset for the given species. The returned dataset
    will have the following columns:
    - pentad
    - covariates: All of the scaled covariate columns
    - latitude, longitude
    - target_observations: Total number of target species observations
    - total_observations: Total number of observation records of all species
    - target

    target =
    1 if target_species_count > 0
    0 if target_species_count == 0 and total_observations > threshold
    -1 otherwise
    """

    observations_path = os.path.join(input_data_path, observations_file)
    covariates_path = os.path.join(input_data_path, covariates_file)

    # Read the Feather files
    observations_df = pd.read_feather(observations_path)
    covariates_df = pd.read_feather(covariates_path)

    # Sum all columns for total observations except 'pentad', 'latitude', and 'longitude'
    columns_to_sum = observations_df.columns.difference(
        ["pentad", "latitude", "longitude"]
    )
    observations_df["total_observations"] = observations_df[columns_to_sum].sum(axis=1)

    # Select the target species column for 'target_observations'
    target_species_total_column = (
        target_species_id  # Assuming the column name is the species ID
    )
    observations_df["target_observations"] = observations_df[
        target_species_total_column
    ]

    # Add the 'target' column
    observations_df["target"] = np.where(
        observations_df[target_species_total_column] > 0,
        1,
        np.where(
            np.bitwise_and(
                observations_df[target_species_total_column] == 0,
                observations_df["total_observations"] >= absence_observations,
            ),
            0,
            -1,
        ),
    )

    # Left join with the covariates DataFrame
    merged_df = covariates_df.merge(observations_df, on="pentad", how="left")

    # Fill missing values with 0
    merged_df[["total_observations", "target_observations"]] = merged_df[
        ["total_observations", "target_observations"]
    ].fillna(0)

    # Select only the necessary columns for return
    required_columns = covariates_df.columns.to_list() + [
        "total_observations",
        "target_observations",
        "target",
    ]

    return merged_df[required_columns]
