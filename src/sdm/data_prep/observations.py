import os
import pandas as pd

from .utils import add_lat_long_from_pentad, make_dir_if_not_exists, add_pentad_from_lat_long


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
    bird_list_df[join_column] = bird_list_df[join_column].fillna('No Match Placeholder')

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
            how="left"
        )
        chunk.drop(columns=[join_column], inplace=True)
        chunk["SABAP2_number"] = chunk["SABAP2_number"].fillna("0")

        add_pentad_from_lat_long(chunk, lat_column_name="decimalLatitude", lng_column_name="decimalLongitude")

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
    all_sabap2_numbers = sorted(bird_list_df["SABAP2_number"].unique().astype(int).astype(str))

    # Identify missing columns
    missing_columns = list(set(all_sabap2_numbers) - set(final_df.columns))

    # Create a DataFrame with zeros for all missing columns
    missing_df = pd.DataFrame(0, index=final_df.index, columns=missing_columns)

    # Concatenate the original DataFrame with the missing columns DataFrame
    final_df = pd.concat([final_df, missing_df], axis=1)

    # Ensure the columns are in the correct order
    final_df = final_df[['pentad'] + all_sabap2_numbers + ['0']]

    # Replace NaN with 0 and convert to integers
    final_df.fillna(0, inplace=True)
    final_df = final_df.astype({col: 'int' for col in final_df.columns if col != 'pentad'})

    # Now save the DataFrame
    final_df.to_feather(f"{aggregate_dir}/{output_file}")


def combine_all(
    input_data_path: str,
    ebirds_file: str,
    inat_file: str,
    sabap2_file: str,
    output_file: str,
):
    # Load the three Feather files into Pandas DataFrames
    ebirds_path = os.path.join(input_data_path, ebirds_file)
    inat_path = os.path.join(input_data_path, inat_file)
    sabap2_path = os.path.join(input_data_path, sabap2_file)

    # Read the Feather files
    df_ebirds = pd.read_feather(ebirds_path)
    df_inat = pd.read_feather(inat_path)
    df_sabap2 = pd.read_feather(sabap2_path)

    # Ensure 'pentad' is the index for each dataframe
    df_ebirds.set_index("pentad", inplace=True)
    df_inat.set_index("pentad", inplace=True)
    df_sabap2.set_index("pentad", inplace=True)

    # Combine all dataframes by adding them
    final_df = df_ebirds.add(df_inat, fill_value=0)
    final_df = final_df.add(df_sabap2, fill_value=0).astype(int)

    final_df.reset_index(inplace=True)
    final_df = add_lat_long_from_pentad(final_df)

    # Write the final dataframe to a Feather file
    output_path = os.path.join(input_data_path, output_file)
    final_df.to_feather(output_path)
    print("Processing complete. Output saved to:", output_path)


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
