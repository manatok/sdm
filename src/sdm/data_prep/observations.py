import os
import pandas as pd

from .utils import (
    add_pentad_from_lat_long,
)


def aggregate_by_pentad_and_sabap_ids(
    input_data_path: str,
    input_csv_file: str,
    output_file: str,
    bird_list_file: str,
    pentad_list_file: str,
    aggregate_dir: str,
    join_column: str,
    overwrite=False,
):
    bird_list_df = pd.read_csv(bird_list_file, dtype={"SABAP2_number": str})
    bird_list_df[join_column] = bird_list_df[join_column].fillna("No Match Placeholder")

    # Initialize an empty DataFrame to store grouped results
    all_grouped_data = pd.DataFrame()

    filepath = os.path.join(input_data_path, input_csv_file)
    chunksize = 1e6  # Adjust based on memory
    chunk_count = 1

    for chunk in pd.read_csv(filepath, sep="\t", chunksize=chunksize):
        print(f"Processing chunk: {chunk_count}", flush=True)
        chunk_count += 1
        chunk = chunk.merge(
            bird_list_df[[join_column, "SABAP2_number"]],
            left_on="species",
            right_on=join_column,
            how="left",
        )
        chunk.drop(columns=[join_column], inplace=True)
        chunk["SABAP2_number"] = chunk["SABAP2_number"].fillna("0")

        add_pentad_from_lat_long(
            chunk, lat_column_name="decimalLatitude", lng_column_name="decimalLongitude"
        )

        grouped_chunk = (
            chunk.groupby(["pentad", "SABAP2_number"]).size().reset_index(name="count")
        )

        all_grouped_data = pd.concat([all_grouped_data, grouped_chunk])

    final_grouped = (
        all_grouped_data.groupby(["pentad", "SABAP2_number"])["count"]
        .sum()
        .reset_index()
    )

    pentad_df = pd.read_csv(pentad_list_file)
    merged_df = pd.merge(pentad_df, final_grouped, on="pentad", how="left")

    # After the pivot
    final_df = merged_df.pivot(index="pentad", columns="SABAP2_number", values="count")

    # Reset the index to turn 'pentad' back into a column
    final_df.reset_index(inplace=True)

    # Remove the name of the new column (which is now 'index' after resetting)
    final_df.columns.name = None

    # Ensure all SABAP2 numbers are present as columns
    all_sabap2_numbers = sorted(
        bird_list_df["SABAP2_number"].unique().astype(int).astype(str)
    )

    # Identify missing columns
    missing_columns = list(set(all_sabap2_numbers) - set(final_df.columns))

    # Create a DataFrame with zeros for all missing columns
    missing_df = pd.DataFrame(0, index=final_df.index, columns=missing_columns)

    # Concatenate the original DataFrame with the missing columns DataFrame
    final_df = pd.concat([final_df, missing_df], axis=1)

    # Ensure the columns are in the correct order
    final_df = final_df[["pentad"] + all_sabap2_numbers + ["0"]]

    # Replace NaN with 0 and convert to integers
    final_df.fillna(0, inplace=True)
    final_df = final_df.astype(
        {col: "int" for col in final_df.columns if col != "pentad"}
    )

    # Now save the DataFrame
    final_df.to_feather(f"{aggregate_dir}/{output_file}")


def sum_observations(
    input_data_path: str,
    verified_observations_files: list[str],
    unverified_observations_files: list[str],
    verified_observations_output_file: str,
    unverified_observations_output_file: str,
):
    """
    This method replaces the combine_all method by keeping verified and unverified
    observations separate. We trust the observations from SABAP2 and iNat, but not
    from eBirds, so we keep eBirds separate. We will only use eBirds when calculating
    the pseudo-absence

    :param input_data_path: The path to the input data folder
    :param verified_observations_files: A list of Feather file names (SABAP2 + iNat)
        for datasets where the observations were verified.
    :param unverified_observations_files: A list of Feather file names (eBirds)
        for datasets where the observations were not verified.
    :param verified_observations_output_file: The name of the Feather file
        containing the verified observations
    :param unverified_observations_output_file: The name of the Feather file
        containing the unverified observations
    """

    print("Verified files:", verified_observations_files)
    print("Unverified files:", unverified_observations_files)

    verified_observations_dfs = [
        pd.read_feather(os.path.join(input_data_path, f)).set_index("pentad")
        for f in verified_observations_files
    ]

    unverified_observations_dfs = [
        pd.read_feather(os.path.join(input_data_path, f)).set_index("pentad")
        for f in unverified_observations_files
    ]

    # Add up all of the observations per pentad
    total_verified_observations_df = (
        pd.concat(verified_observations_dfs)
        .groupby(level=0)
        .sum(min_count=1)
        .fillna(0)
        .astype(int)
    )

    total_unverified_observations_df = (
        pd.concat(unverified_observations_dfs)
        .groupby(level=0)
        .sum(min_count=1)
        .fillna(0)
        .astype(int)
    )

    # Count all observations for each pentad
    total_verified_observations = total_verified_observations_df.sum(axis=1)
    total_unverified_observations = total_unverified_observations_df.sum(axis=1)

    # Join the new column with the original DataFrame
    total_verified_observations_df = pd.concat(
        [
            total_verified_observations_df,
            total_verified_observations.rename("total_pentad_observations"),
        ],
        axis=1,
    )
    total_unverified_observations_df = pd.concat(
        [
            total_unverified_observations_df,
            total_unverified_observations.rename("total_pentad_observations"),
        ],
        axis=1,
    )

    total_verified_observations_df.reset_index(inplace=True)
    total_unverified_observations_df.reset_index(inplace=True)

    # Saving to Feather files
    total_verified_observations_df.to_feather(
        os.path.join(input_data_path, verified_observations_output_file)
    )
    total_unverified_observations_df.to_feather(
        os.path.join(input_data_path, unverified_observations_output_file)
    )


def generate_sabap_species_diff(
    input_data_path: str,
    input_csv_file: str,
    bird_list_file: str,
    dataset_prefix: str,
):
    # Paths
    csv_path = f"{input_data_path}/{input_csv_file}"
    mapping_path = f"{input_data_path}/{dataset_prefix}_SABAP_mapping.csv"
    unmapped_path = f"{input_data_path}/unmapped_{dataset_prefix}.csv"
    column_name = dataset_prefix + "_name"

    # Read the bird list
    bird_list_df = pd.read_csv(bird_list_file)
    bird_list_df = bird_list_df[["SABAP2_number", "SA_name", "Scientific_name"]]
    bird_list_df[column_name] = ""  # Initialize with empty strings

    # Extract unique species names from dataset
    species_df = pd.read_csv(csv_path, sep="\t", usecols=["species"])
    unique_species = species_df["species"].unique()

    print(f"Total species in {dataset_prefix}s: {len(unique_species)}", flush=True)
    print(f"Total species in SABAP: {len(bird_list_df)}", flush=True)

    # Identify which SABAP species names match species names
    matched_species = set(bird_list_df["Scientific_name"]) & set(unique_species)

    # Fill the name column for matched species
    bird_list_df.loc[
        bird_list_df["Scientific_name"].isin(matched_species), column_name
    ] = bird_list_df["Scientific_name"]

    # Identify unmatched species and write them to the unmapped file
    unmatched_species = set(bird_list_df["Scientific_name"]) - matched_species
    if unmatched_species:
        unmatched_df = bird_list_df[
            bird_list_df["Scientific_name"].isin(unmatched_species)
        ]
        unmatched_df[["Scientific_name", "SA_name"]].to_csv(unmapped_path, index=False)
        print(
            f"Found {len(unmatched_species)} unmatched species. Written to {unmapped_path}."
        )
    else:
        print("All species in dataset are matched!")

    # Save the mapping file
    bird_list_df.to_csv(mapping_path, index=False)
