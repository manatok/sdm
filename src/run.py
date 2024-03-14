import click

from .sdm.data_prep.abap import download_saba2_species, download_all, combine
from .sdm.data_prep.two_km_grid import generate_bounding_box as _generate_bounding_box
from .sdm.data_prep.observations import (
    aggregate_by_pentad_and_sabap_ids,
    sum_observations as _sum_observations,
    generate_sabap_species_diff,
)
from .config import config
from .sdm.data_prep.covariates import (
    combine_bioclim as _combine_bioclim,
    combine_google_ee_covariates as _combine_google_ee_covariates,
    combine_and_scale_all_covariates,
)
from .sdm.data_prep.utils import (
    download_kaggle_dataset,
    make_dir_if_not_exists,
    download_csv,
)
from .sdm.stats import get_stats

from .sdm.models.runner import train_and_predict, train_and_predict_all
from .sdm.data_prep.birdlasser import combine_birdlasser_files


@click.group()
def cli():
    """Main entry point for the CLI."""
    pass


@cli.command()
@click.option(
    "--sabap2_id",
    required=False,
    help="Download a single species file. See BirdList.csv for sabap2_number",
)
def download_sabap2_species(sabap2_id: int):
    """Download a single species file into the abap2 data file"""
    make_dir_if_not_exists(config["SABAP2_DATA_DIR"])
    download_saba2_species(
        sabap2_id, config["SABAP2_DATA_DIR"], config["SABAP2_SPECIES_URL"]
    )


@cli.command()
@click.option(
    "--overwrite",
    required=False,
    help="Overwrite exisitng files if they already exist locally.",
)
@click.option(
    "--combine",
    required=False,
    help="Combine all files into a single file after downloading. This will need to happen at some point.",
)
def download_sabap2(overwrite: bool = False, combine: bool = True):
    """Method to download all species files from SABA2 and combine them into a single file"""
    make_dir_if_not_exists(config["SABAP2_DATA_DIR"])
    download_all(config["BIRD_LIST"], overwrite)

    if combine:
        combine(
            config["SABAP2_DATA_DIR"],
            config["PENTAD_LIST"],
            config["AGGREGATE_DIR"],
            config["SABAP2_COMBINED_FILE"],
        )


@cli.command()
def combine_sabap2():
    """Combine all of the datasets into observations per dataset"""
    combine(
        config["SABAP2_DATA_DIR"],
        config["PENTAD_LIST"],
        config["AGGREGATE_DIR"],
        config["SABAP2_COMBINED_FILE"],
    )

@cli.command()
def combine_birdlasser():
    """Combine all of the datasets into observations per dataset"""
    combine_birdlasser_files(
        config["BIRDLASSER_DATA_DIR"],
        config["PENTAD_LIST_2KM"],
        config["AGGREGATE_DIR_2KM"],
        config["BIRDLASSER_COMBINED_FILE"],
    )


@cli.command()
@click.option(
    "--overwrite",
    required=False,
    help="Overwrite exisitng files if they already exist locally.",
)
def download_ebirds_csv(overwrite: bool = False):
    """Download the eBirds CSV dataset from Kaggle"""
    download_csv(
        config["KAGGLE_EBIRDS_DATASET"],
        config["KAGGLE_EBIRDS_CSV"],
        config["EBIRDS_DIR"],
        overwrite,
    )


@cli.command()
def generate_sabap_ebirds_diff():
    """This will load up the reference bird list and join it to the
    eBirds dataset on species name so that we can find all of the
    missmatched names that will need to be manually filled in. Once
    this has run the EBIRDS_name column should be copied from the
    eBirds_SABAP_mappings.csv file into the BirdList.csv file and the
    empty cell filled in where possible."""
    generate_sabap_species_diff(
        config["EBIRDS_DIR"], config["KAGGLE_EBIRDS_CSV"], config["BIRD_LIST"], "ebirds"
    )


@cli.command()
@click.option("--use_2km_pentad", required=False, help="To rather use 2km pentad instead of 5' pentad.")
def aggregate_ebirds(use_2km_pentad: bool = False):
    """Once the BirdList.csv file has been populated with the EBIRDS_name
    column this method can be run to generate a pentad x SABAP2_species_id
    file"""

    ebirds_aggregate_file = config["EBIRDS_AGGREGATE_FILE"]
    pentad_list = config["PENTAD_LIST"]
    aggregate_dir = config["AGGREGATE_DIR"]

    if use_2km_pentad:
        print("Using 2km pentad instead of 5' pentad")
        ebirds_aggregate_file = config["EBIRDS_AGGREGATE_FILE_2KM"]
        pentad_list = config["PENTAD_LIST_2KM"]
        aggregate_dir = config["AGGREGATE_DIR_2KM"]

    aggregate_by_pentad_and_sabap_ids(
        config["EBIRDS_DIR"],
        config["KAGGLE_EBIRDS_CSV"],
        ebirds_aggregate_file,
        config["BIRD_LIST"],
        pentad_list,
        aggregate_dir,
        "ebirds_name",
        use_2km_pentad
    )


@cli.command()
@click.option(
    "--overwrite",
    required=False,
    help="Overwrite exisitng files if they already exist locally.",
)
def download_inat_csv(overwrite: bool = False):
    """Download the iNaturalist CSV dataset from Kaggle"""
    download_csv(
        config["KAGGLE_INAT_DATASET"],
        config["KAGGLE_INAT_CSV"],
        config["INAT_DIR"],
        overwrite,
    )


@cli.command()
def generate_sabap_inat_diff():
    """This will load up the reference bird list and join it to the
    inat dataset on species name so that we can find all of the
    missmatched names that will need to be manually filled in. Once
    this has run the inat_name column should be copied from the
    inat_SABAP_mappings.csv file into the BirdList.csv file and the
    empty cell filled in where possible."""
    generate_sabap_species_diff(
        config["INAT_DIR"], config["KAGGLE_INAT_CSV"], config["BIRD_LIST"], "inat"
    )


@cli.command()
@click.option("--use_2km_pentad", required=False, help="To rather use 2km pentad instead of 5' pentad.")
def aggregate_inat(use_2km_pentad: bool = False):
    """Once the BirdList.csv file has been populated with the inat_name
    column this method can be run to generate a pentad x SABAP2_species_id
    file"""
    inat_aggregate_file = config["INAT_AGGREGATE_FILE"]
    pentad_list = config["PENTAD_LIST"]
    aggregate_dir = config["AGGREGATE_DIR"]

    if use_2km_pentad:
        print("Using 2km pentad instead of 5' pentad")
        inat_aggregate_file = config["INAT_AGGREGATE_FILE_2KM"]
        pentad_list = config["PENTAD_LIST_2KM"]
        aggregate_dir = config["AGGREGATE_DIR_2KM"]

    aggregate_by_pentad_and_sabap_ids(
        config["INAT_DIR"],
        config["KAGGLE_INAT_CSV"],
        inat_aggregate_file,
        config["BIRD_LIST"],
        pentad_list,
        aggregate_dir,
        "inat_name",
        use_2km_pentad,
    )


@cli.command()
def sum_observations():
    """
    Sums and combines the observation files. The iNat + SABAP2 files are
    combined into a single verified observation file, while the eBirds file
    becomes the unverified observation file. At some point we may add other
    datasets to either.
    """
    _sum_observations(
        config["AGGREGATE_DIR"],
        [
            config["INAT_AGGREGATE_FILE"],
            config["SABAP2_COMBINED_FILE"],
        ],
        [config["EBIRDS_AGGREGATE_FILE"]],
        config["VERIFIED_OBSERVATIONS_FILE"],
        config["UNVERIFIED_OBSERVATIONS_FILE"],
    )


@cli.command()
def sum_2km_observations():
    """
    Sums and combines the observation files. The Birdlasser data is used as
    the verified observation file, while the eBirds + iNat files
    becomes the unverified observation file.
    """
    _sum_observations(
        config["AGGREGATE_DIR_2KM"],
        [config["BIRDLASSER_COMBINED_FILE"]],
        [
            config["INAT_AGGREGATE_FILE_2KM"],
            config["EBIRDS_AGGREGATE_FILE_2KM"]
        ],
        config["VERIFIED_OBSERVATIONS_FILE"],
        config["UNVERIFIED_OBSERVATIONS_FILE"],
    )


@cli.command()
def download_bioclim():
    """Download the BioClim data from Kaggle."""
    make_dir_if_not_exists(config["BIOCLIM_DIR"])

    download_kaggle_dataset(config["KAGGLE_BIOCLIM_DATASET"], config["BIOCLIM_DIR"])
    print(f"Downloaded bioclim to {config['BIOCLIM_DIR']}")


@cli.command()
def download_google_ee_data():
    """Download the GoogleEE data from Kaggle."""
    make_dir_if_not_exists(config["GOOGLE_EE_DIR"])

    download_kaggle_dataset(config["KAGGLE_GOOGLE_EE_DATASET"], config["GOOGLE_EE_DIR"])
    print(f"Downloaded google ee data to {config['GOOGLE_EE_DIR']}")


@cli.command()
@click.option("--use_2km_pentad", required=False, help="To rather use 2km pentad instead of 5' pentad.")
def combine_bioclim(use_2km_pentad:bool = False):
    """Combines all of the bioclim files into a single file"""
    if use_2km_pentad:
        print("Using 2km grid")
        _combine_bioclim(
            config["BIOCLIM_DIR_2KM"],
            config["AGGREGATE_DIR_2KM"],
            config["BIOCLIM_COMBINED_FILE_2KM"],
        )
    else:
        _combine_bioclim(
            config["BIOCLIM_DIR"],
            config["AGGREGATE_DIR"],
            config["BIOCLIM_COMBINED_FILE"],
        )


@cli.command()
@click.option("--use_2km_pentad", required=False, help="To rather use 2km pentad instead of 5' pentad.")
def combine_google_ee_covariates(use_2km_pentad:bool = False):
    """Combines all of the google ee covariates files into a single file"""
    if use_2km_pentad:
        print("Using 2km grid")
        _combine_google_ee_covariates(
            config["GOOGLE_EE_DIR_2KM"],
            config["AGGREGATE_DIR_2KM"],
            config["GOOGLE_EE_COMBINED_FILE_2KM"],
        )
    else:
        _combine_google_ee_covariates(
            config["GOOGLE_EE_DIR"],
            config["AGGREGATE_DIR"],
            config["GOOGLE_EE_COMBINED_FILE"],
        )


@cli.command()
@click.option("--use_2km_pentad", required=False, help="To rather use 2km pentad instead of 5' pentad.")
def combine_all_covariates(use_2km_pentad:bool = False):
    """Combines the Google EE and bioclim covariates files into a single"""
    if use_2km_pentad:
        print("Using 2km grid")
        combine_and_scale_all_covariates(
            config["GOOGLE_EE_COMBINED_FILE_2KM"],
            config["BIOCLIM_COMBINED_FILE_2KM"],
            config["AGGREGATE_DIR_2KM"],
            config["COMBINED_COVARIATES_FILE_2KM"],
        )
    else:
        combine_and_scale_all_covariates(
            config["GOOGLE_EE_COMBINED_FILE"],
            config["BIOCLIM_COMBINED_FILE"],
            config["AGGREGATE_DIR"],
            config["COMBINED_COVARIATES_FILE"],
        )


@cli.command()
def download_all_data():
    """Download all of the aggregated data needed to run the model."""
    make_dir_if_not_exists(config["AGGREGATE_DIR"])

    download_kaggle_dataset(
        config["KAGGLE_AGGREGATE_DATASET"],
        config["AGGREGATE_DIR"],
    )


@cli.command()
@click.option("--species_id", required=False, help="The SABAP2 bird id to process.")
@click.option("--use_2km_pentad", required=False, help="To rather use 2km pentad instead of 5' pentad.")
def stats(species_id: str = None, use_2km_pentad: bool = False):
    """Get all the stats for a given species"""
    print("Species: ", species_id, flush=True)

    if use_2km_pentad:
        print("Using 2km pentad instead of 5' pentad")
        get_stats(
            config["AGGREGATE_DIR_2KM"],
            config["EBIRDS_AGGREGATE_FILE_2KM"],
            config["INAT_AGGREGATE_FILE_2KM"],
            config["BIRDLASSER_COMBINED_FILE"],
            config["VERIFIED_OBSERVATIONS_FILE"],
            species_id,
            plot=True,
        )
    else:
        get_stats(
            config["AGGREGATE_DIR"],
            config["EBIRDS_AGGREGATE_FILE"],
            config["INAT_AGGREGATE_FILE"],
            config["SABAP2_COMBINED_FILE"],
            config["VERIFIED_OBSERVATIONS_FILE"],
            species_id,
            plot=True,
        )


@cli.command()
@click.option("--species_id", required=False, help="The SABAP2 bird id to process.")
@click.option("--use_2km_pentad", required=False, help="To rather use 2km pentad instead of 5' pentad.")
def generate_distribution(species_id: str, use_2km_pentad:bool = False):
    """
    Run the model for a given species. This will generate:
        1. Some maps in output/maps/species_id_...
        2. A summary file in output/stats/species_id_...
        3. The pentad probabilities file in output/models/species_id_...
    """
    if use_2km_pentad:
        print("Using 2km pentad instead of 5' pentad")
        train_and_predict(
            species_id,
            config["AGGREGATE_DIR_2KM"],
            config["VERIFIED_OBSERVATIONS_FILE"],
            config["UNVERIFIED_OBSERVATIONS_FILE"],
            config["COMBINED_COVARIATES_FILE_2KM"],
            config["OUTPUT_DIR_2KM"],
            use_2km_pentad,
        )
    else:
        train_and_predict(
            species_id,
            config["AGGREGATE_DIR"],
            config["VERIFIED_OBSERVATIONS_FILE"],
            config["UNVERIFIED_OBSERVATIONS_FILE"],
            config["COMBINED_COVARIATES_FILE"],
            config["OUTPUT_DIR"],
            use_2km_pentad
        )


@cli.command()
@click.option("--use_2km_pentad", required=False, help="To rather use 2km pentad instead of 5' pentad.")
def generate_all_distributions(use_2km_pentad:bool = False):
    """
    Run the model for all species. This will generate:
        1. Some maps in output/maps/species_id_...
        2. Summary files in output/stats/species_id_...
        3. The pentad probabilities files in output/models/species_id_...
    """
    if use_2km_pentad:
        print("Using 2km pentad instead of 5' pentad")
        train_and_predict_all(
            config["BIRD_LIST"],
            config["AGGREGATE_DIR_2KM"],
            config["VERIFIED_OBSERVATIONS_FILE"],
            config["UNVERIFIED_OBSERVATIONS_FILE"],
            config["COMBINED_COVARIATES_FILE_2KM"],
            config["OUTPUT_DIR_2KM"],
            use_2km_pentad,
        )
    else:
        train_and_predict_all(
            config["BIRD_LIST"],
            config["AGGREGATE_DIR"],
            config["VERIFIED_OBSERVATIONS_FILE"],
            config["UNVERIFIED_OBSERVATIONS_FILE"],
            config["COMBINED_COVARIATES_FILE"],
            config["OUTPUT_DIR"],
            use_2km_pentad
        )


@cli.command()
def generate_bounding_box():
    """
    Generates the 2km bounding box for the entire grid. This is used by google EE & as the
    reference pentad file for the processing pipeline.
    """
    _generate_bounding_box(
        config["BIOCLIM_DIR_2KM"] + "/Bio1.csv",
    )


@cli.command()
@click.option("--species_id", required=False, help="The SABAP2 bird id to process.")
@click.option("--data", required=False, help="ebirds or inat.")
def plot_aggregate_2km(species_id: str = None, data: str = 'inat'):
    import pandas as pd
    import numpy as np
    from .sdm.data_prep.two_km_grid import add_lat_long_from_two_km_pentad, plot_map_2km

    aggregate_file = config["INAT_AGGREGATE_FILE_2KM"]
    if data == 'ebirds':
        aggregate_file = config["EBIRDS_AGGREGATE_FILE_2KM"]

    aggregate_file = config['AGGREGATE_DIR_2KM'] + '/' + aggregate_file

    df = pd.read_feather(aggregate_file)
    df = add_lat_long_from_two_km_pentad(df)

    column = species_id
    if not species_id:
        df['total'] = df.drop(columns=['pentad', 'latitude', 'longitude']).sum(axis=1)

        column = 'total'
    df[column] = np.log(df[column])
    # print(df['total'])
    plot_map_2km(df, column)




if __name__ == "__main__":
    cli()
