import pandas as pd


def generate_training(
    target_species_id: str,
    observations_df: pd.core.frame.DataFrame,
    covariates_df: pd.core.frame.DataFrame,
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

    pd.set_option("display.max_columns", None)

    # Set option to display all rows
    pd.set_option("display.max_rows", None)

    print(observations_df.columns)
    print(observations_df.head())
    print(covariates_df.columns)
    print(covariates_df.head())

    # Add the 'target' column to the new dataframe
    # observations_df[target_column] = np.where(
    #     observations_df[target_species_total_column] > 0, 1,
    #         np.where(
    #             np.bitwise_and(
    #                 observations_df[target_species_total_column] == 0,
    #                 observations_df[total_column] >= absence_observations
    #             ), 0, -1
    #         )
    #     )

    # return observations_df
