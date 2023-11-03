import os
import pandas as pd

from .utils import make_dir_if_not_exists, add_pentad_from_lat_long


def aggregate_by_pentad_and_sabap_ids(
    input_data_path: str, 
    input_csv_file: str,
    output_csv_file: str,
    bird_list_file: str,
    pentad_list_file: str,
    aggregate_dir: str,
    join_column: str,
    overwrite = False
):
    bird_list_df = pd.read_csv(bird_list_file, dtype={'SABAP2_number': str})
    
    # Initialize an empty DataFrame to store grouped results
    all_grouped_data = pd.DataFrame()

    filepath = f"{input_data_path}/{input_csv_file}"
    chunksize = 1e6  # Adjust based on memory
    chunk_count = 1

    for chunk in pd.read_csv(filepath, sep='\t', chunksize=chunksize):
        print(f"Processing chunk: {chunk_count}", flush=True)
        chunk_count += 1
        
        # Merge the chunk with the bird list
        chunk = chunk.merge(bird_list_df[[join_column, 'SABAP2_number']], left_on='species', right_on=join_column, how='left')
        chunk.drop(columns=[join_column], inplace=True)
        # All the unmapped SABAP should be put in their own bucket of "0"
        chunk['SABAP2_number'] = chunk['SABAP2_number'].fillna("0")

        # Add pentad data
        add_pentad_from_lat_long(chunk, lat_column_name='decimalLatitude', lng_column_name='decimalLongitude')
        
        # Group by pentad and SABAP2_number within this chunk
        grouped_chunk = chunk.groupby(['pentad', 'SABAP2_number']).size().reset_index(name='count')
        # Concatenate this chunk's grouped data with the main storage DataFrame
        all_grouped_data = pd.concat([all_grouped_data, grouped_chunk])

    # Group the combined data one more time across chunks
    final_grouped = all_grouped_data.groupby(['pentad', 'SABAP2_number'])['count'].sum().reset_index()

    pentad_df = pd.read_csv(pentad_list_file)
    merged_df = pd.merge(pentad_df, final_grouped, on='pentad', how='left')

    final_df = merged_df.pivot(index='pentad', columns='SABAP2_number', values='count')
    final_df.reset_index(inplace=True)
    
    all_sabap2_numbers = bird_list_df['SABAP2_number'].unique().astype(str)
    for sabap2_number in all_sabap2_numbers:
        if sabap2_number not in final_df.columns:
            final_df[sabap2_number] = 0

    final_df = final_df[['pentad'] + list(all_sabap2_numbers) + ["0"]]
    final_df.fillna(0, inplace=True)
    final_df = final_df.astype({col: 'int' for col in final_df.columns[1:]})  # Convert columns to int

    make_dir_if_not_exists(aggregate_dir)
    final_df.to_csv(f"{aggregate_dir}/{output_csv_file}", index=False)


def combine_all(
    input_data_path: str,
    ebirds_file: str, 
    inat_file: str, 
    sabap2_file: str, 
    output_file: str
):
    # Load the three CSV files into Pandas DataFrames
    ebirds_path = os.path.join(input_data_path, ebirds_file)
    inat_path = os.path.join(input_data_path, inat_file)
    sabap2_path = os.path.join(input_data_path, sabap2_file)

    chunksize = 100000  # Adjust this depending on your available memory
    
    # Initialize an empty DataFrame to store the final result
    final_df = pd.DataFrame()
    
    # Function to process each chunk
    def process_chunk(df):
        nonlocal final_df
        final_df = final_df.add(df, fill_value=0).astype(int)

    # Iterate over each file and each chunk in the file
    for file in [ebirds_path, inat_path, sabap2_path]:
        print(f"Processing file: {file}", flush=True)

        for chunk in pd.read_csv(file, chunksize=chunksize):
            print("Processing chunk", flush=True)
            # Ensure 'pentad' is the index
            if 'pentad' in chunk.columns:
                chunk.set_index('pentad', inplace=True)
            
            process_chunk(chunk)

    # Write the final dataframe to a Feather file
    output_path = os.path.join(input_data_path, output_file)
    final_df.reset_index().to_feather(output_path)
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
    column_name = dataset_prefix + '_name'

    # Read the bird list
    bird_list_df = pd.read_csv(bird_list_file)
    bird_list_df = bird_list_df[['SABAP2_number', 'SA_name', 'Scientific_name']]
    bird_list_df[column_name] = ''  # Initialize with empty strings
    
    # Extract unique species names from dataset
    species_df = pd.read_csv(csv_path, sep='\t', usecols=['species'])
    unique_species = species_df['species'].unique()

    print(f"Total species in {dataset_prefix}s: {len(unique_species)}", flush=True)
    print(f"Total species in SABAP: {len(bird_list_df)}", flush=True)

    # Identify which SABAP species names match species names
    matched_species = set(bird_list_df['Scientific_name']) & set(unique_species)

    # Fill the name column for matched species
    bird_list_df.loc[bird_list_df['Scientific_name'].isin(matched_species), column_name] = bird_list_df['Scientific_name']
    
    # Identify unmatched species and write them to the unmapped file
    unmatched_species = set(bird_list_df['Scientific_name']) - matched_species
    if unmatched_species:
        unmatched_df = bird_list_df[bird_list_df['Scientific_name'].isin(unmatched_species)]
        unmatched_df[['Scientific_name', 'SA_name']].to_csv(unmapped_path, index=False)
        print(f"Found {len(unmatched_species)} unmatched species. Written to {unmapped_path}.")
    else:
        print("All species in dataset are matched!")

    # Save the mapping file
    bird_list_df.to_csv(mapping_path, index=False)