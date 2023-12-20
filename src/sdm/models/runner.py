import os
import csv
import pandas as pd
import numpy as np
from ..utils import get_species_name

from ..data_prep.utils import add_lat_long_from_pentad
from .random_forest import train, predict


def train_and_predict_all(
    bird_list: str,
    input_data_path: str,
    verified_observations_file: str,
    unverified_observations_file: str,
    covariates_file: str,
):
    # Read the bird list into a DataFrame
    bird_df = pd.read_csv(bird_list)

    # Iterate through the DataFrame rows
    for index, row in bird_df.iterrows():
        print(f"Processing: {row['SA_name']}", flush=True)

        sabap2_id = str(row["SABAP2_number"])

        if row["inat_name"] == "":
            print("Skipping: No inat_name for:", sabap2_id, row["SA_name"], flush=True)
            continue

        train_and_predict(
            sabap2_id,
            input_data_path,
            verified_observations_file,
            unverified_observations_file,
            covariates_file,
        )


def train_and_predict(
    target_species_id: str,
    input_data_path: str,
    verified_observations_file: str,
    unverified_observations_file: str,
    covariates_file: str,
    absence_observations: int | None = None,
):
    # Read the Feather files
    verified_observations_df = pd.read_feather(
        os.path.join(input_data_path, verified_observations_file)
    )

    print(f"SUM: {sum(verified_observations_df[target_species_id])}")
    if sum(verified_observations_df[target_species_id]) < 30:
        print(
            f"Skipping - Not enough pentads with target species_id: {target_species_id} - Total: {sum(verified_observations_df[target_species_id])}"
        )
        return

    unverified_observations_df = pd.read_feather(
        os.path.join(input_data_path, unverified_observations_file)
    )
    covariates_df = pd.read_feather(os.path.join(input_data_path, covariates_file))
    covariates_df = add_lat_long_from_pentad(covariates_df)

    if not absence_observations:
        absence_observations = calculate_target_species_ratio(
            target_species_id, verified_observations_df
        )

    training_data_df = generate_training(
        target_species_id,
        verified_observations_df,
        unverified_observations_df,
        covariates_df,
        absence_observations,
    )

    positive_df = training_data_df.query("target == 1")
    print("Total pentads with target species: ", positive_df.shape[0])

    negative_df = training_data_df.query("target == 0")
    print("Total pseudo-absence: ", negative_df.shape[0])

    balanced_df = pd.concat([positive_df, negative_df])

    model, results = train(balanced_df)
    results_to_log = {
        "species_id": target_species_id,
        "species_name": get_species_name(target_species_id),
    }
    results_to_log.update(results)

    append_results_to_csv(results_to_log, "output/training_results.csv")

    pentad_probabilities = predict(
        model, training_data_df, positive_df, negative_df, target_species_id
    )

    pentad_probabilities_sorted = pentad_probabilities.sort_index()

    pentad_probabilities_sorted.to_csv(
        f"output/pentad_probabilities/{target_species_id}.csv", index=False
    )


def append_results_to_csv(dict_data, file_path):
    """
    Appends a dictionary to a CSV file. Creates the file if it doesn't exist.

    :param dict_data: Dictionary containing data to append. Keys are column headers.
    :param file_path: Path to the CSV file.
    """
    # Check if file exists and if it's empty
    file_exists = os.path.isfile(file_path)
    is_empty = not file_exists or os.stat(file_path).st_size == 0

    # Open the file in append mode ('a')
    with open(file_path, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=dict_data.keys())

        # Write the header only if the file is new or empty
        if is_empty:
            writer.writeheader()

        # Write the data row
        writer.writerow(dict_data)


def calculate_target_species_ratio(
    target_species_id: str, observations_df: pd.DataFrame
):
    """
    Calculate the ratio of the target species to the total number of observations
    per pentad, for pentads where the target species count is greater than 0.
    Then select the 10th percentile value of this and return the reciprocal.
    """
    # Filter rows where target species count is greater than 0
    filtered_df = observations_df[observations_df[target_species_id] > 0]

    # Calculate the ratio
    ratio = filtered_df[target_species_id] / filtered_df["total_pentad_observations"]

    # Calculate the 10th percentile of the ratio
    tenth_percentile = np.percentile(ratio, 10)

    # Return the reciprocal of the 10th percentile
    return 1 / tenth_percentile if tenth_percentile != 0 else None


def generate_training(
    target_species_id: str,
    verified_observations_df,
    unverified_observations_df,
    covariates_df,
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

    verified_observations_df["target"] = np.where(
        verified_observations_df[target_species_id] > 0,
        1,
        np.where(
            np.bitwise_and(
                verified_observations_df[target_species_id] == 0,
                np.bitwise_and(
                    verified_observations_df["total_pentad_observations"]
                    + unverified_observations_df["total_pentad_observations"]
                    > absence_observations,
                    unverified_observations_df[target_species_id] == 0,
                ),
            ),
            0,
            -1,
        ),
    )

    # Left join with the covariates DataFrame
    merged_df = covariates_df.merge(verified_observations_df, on="pentad", how="left")

    # Select only the necessary columns for return
    required_columns = covariates_df.columns.to_list() + ["target"]

    return merged_df[required_columns]
