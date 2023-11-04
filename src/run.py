import click


from .sdm.data_prep.abap import download_saba2_species, download_all, combine
from .sdm.data_prep.observations import (
    aggregate_by_pentad_and_sabap_ids,
    combine_all as _combine_all,
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


@click.group()
def cli():
    """Main entry point for the CLI."""
    print("CLI group is being executed.")


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
    # Combine all of the datasets into observations per dataset
    combine(
        config["SABAP2_DATA_DIR"],
        config["PENTAD_LIST"],
        config["AGGREGATE_DIR"],
        config["SABAP2_COMBINED_FILE"],
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
def aggregate_ebirds():
    """Once the BirdList.csv file has been populated with the EBIRDS_name
    column this method can be run to generate a pentad x SABAP2_species_id
    file"""
    aggregate_by_pentad_and_sabap_ids(
        config["EBIRDS_DIR"],
        config["KAGGLE_EBIRDS_CSV"],
        config["EBIRDS_AGGREGATE_FILE"],
        config["BIRD_LIST"],
        config["PENTAD_LIST"],
        config["AGGREGATE_DIR"],
        "ebirds_name",
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
def aggregate_inat():
    """Once the BirdList.csv file has been populated with the EBIRDS_name
    column this method can be run to generate a pentad x SABAP2_species_id
    file"""
    aggregate_by_pentad_and_sabap_ids(
        config["INAT_DIR"],
        config["KAGGLE_INAT_CSV"],
        config["INAT_AGGREGATE_FILE"],
        config["BIRD_LIST"],
        config["PENTAD_LIST"],
        config["AGGREGATE_DIR"],
        "inat_name",
    )


@cli.command()
def download_inat():
    """Download the iNat data from Kaggle."""
    dataset_path = "manatok/bird-observations"
    file_name = "inat_aves_africa.feather"
    target_path = "./data/inat/"

    download_kaggle_dataset(dataset_path, target_path, file_name)
    print(f"Downloaded {file_name} to {target_path}")


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
def combine_bioclim():
    _combine_bioclim(
        config["BIOCLIM_DIR"],
        config["AGGREGATE_DIR"],
        config["BIOCLIM_COMBINED_FILE"],
    )


@cli.command()
def combine_google_ee_covariates():
    _combine_google_ee_covariates(
        config["GOOGLE_EE_DIR"],
        config["AGGREGATE_DIR"],
        config["GOOGLE_EE_COMBINED_FILE"],
    )


@cli.command()
def combine_all_covariates():
    combine_and_scale_all_covariates(
        config["GOOGLE_EE_COMBINED_FILE"],
        config["BIOCLIM_COMBINED_FILE"],
        config["AGGREGATE_DIR"],
        config["COMBINED_COVARIATES_FILE"],
    )


@cli.command()
def combine_all():
    """"""
    _combine_all(
        config["AGGREGATE_DIR"],
        config["EBIRDS_AGGREGATE_FILE"],
        config["INAT_AGGREGATE_FILE"],
        config["SABAP2_COMBINED_FILE"],
        config["COMBINED_OBSERVATIONS_FILE"],
    )


@cli.command()
@click.option("--species_id", required=False, help="The SABAP2 bird id to process.")
def stats(species_id: str = None):
    """Get all the stats for a given species"""
    get_stats(
        config["AGGREGATE_DIR"],
        config["EBIRDS_AGGREGATE_FILE"],
        config["INAT_AGGREGATE_FILE"],
        config["SABAP2_COMBINED_FILE"],
        config["COMBINED_OBSERVATIONS_FILE"],
        species_id,
        plot=True
    )


if __name__ == "__main__":
    cli()
