import os
import pandas as pd
from kaggle.api.kaggle_api_extended import KaggleApi

import zipfile


def make_dir_if_not_exists(dir):
    # Create the target directory and log file if they don't exist
    if not os.path.exists(dir):
        os.makedirs(dir)


def download_kaggle_dataset(dataset_path, target_path, file_name=None):
    api = KaggleApi()
    api.authenticate()

    if file_name:
        # Download specific file
        api.dataset_download_file(dataset_path, file_name, path=target_path)
        file_path = os.path.join(target_path, f"{file_name}.zip")

        # Unzip if necessary
        if os.path.exists(file_path):
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(target_path)
            os.remove(file_path)

    else:
        # Download all files in the dataset
        api.dataset_download_files(dataset_path, path=target_path, unzip=True)


def download_csv(dataset_path, file_name, target_path, overwrite=False):
    make_dir_if_not_exists(target_path)

    file_path = f"{target_path}/{file_name}"

    if not overwrite and os.path.exists(file_path):
        print("File already exists. Skipping download.", flush=True)
        return

    download_kaggle_dataset(dataset_path, target_path, file_name)


def make_pentad(x, y):
    # Determine the separator based on the signs of x and y
    separator = (
        "_"
        if x < 0 and y >= 0
        else "a"
        if x < 0 and y < 0
        else "b"
        if x >= 0 and y < 0
        else "c"
    )

    x = abs(x)
    y = abs(y)
    # get the first digit (the tens) of the minutes
    x1 = int(6 * (x - int(x)))
    y1 = int(6 * (y - int(y)))

    # Get the second digit (the units) of the minutes
    x2 = int(60 * (x - int(x))) % (x1 * 10) if x1 != 0 else int(60 * (x - int(x)))
    y2 = int(60 * (y - int(y))) % (y1 * 10) if y1 != 0 else int(60 * (y - int(y)))

    # round the units into their 5min pentad
    x2 = 0 if x2 < 5 else 5
    y2 = 0 if y2 < 5 else 5

    # Use zfill to ensure the strings are at least 4 characters, padded with '0' if they are not
    xx = f"{int(x)}{x1}{x2}".zfill(4)
    yy = f"{int(y)}{y1}{y2}".zfill(4)

    return f"{xx}{separator}{yy}"


def parse_pentad(pentad_str):
    # Determine the separator based on the pentad string
    if "_" in pentad_str:
        separator = "_"
        x_sign = -1
        y_sign = 1
    elif "a" in pentad_str:
        separator = "a"
        x_sign = -1
        y_sign = -1
    elif "b" in pentad_str:
        separator = "b"
        x_sign = 1
        y_sign = -1
    else:
        separator = "c"
        x_sign = 1
        y_sign = 1

    # Extract the latitude and longitude components from the pentad string
    xx, yy = pentad_str.split(separator)
    x_degrees = int(xx[0:-2])
    x_minutes = int(xx[-2:])

    x = x_sign * (x_degrees + x_minutes / 60)

    y_degrees = int(yy[0:-2])
    y_minutes = int(yy[-2:])
    y = y_sign * (y_degrees + y_minutes / 60)

    return x, y


def add_pentad_from_lat_long(
    df: pd.core.frame.DataFrame,
    lat_column_name: str = "latitude",
    lng_column_name: str = "longitude",
    pentad_column_name: str = "pentad",
) -> pd.core.frame.DataFrame:
    """
    Add a pentad column to the dataframe based on the latitude and longitude
    """

    # Create the pentad column based on latitude and longitude values
    df[pentad_column_name] = df.apply(
        lambda row: make_pentad(row[lat_column_name], row[lng_column_name]), axis=1
    )

    return df


def add_lat_long_from_pentad(
    df: pd.core.frame.DataFrame,
    lat_column_name: str = "latitude",
    lng_column_name: str = "longitude",
    pentad_column_name: str = "pentad",
) -> pd.core.frame.DataFrame:
    """
    Add a latitude and longitude column to the dataframe based on the pentad
    """
    lat_long_df = df[pentad_column_name].apply(
        lambda x: pd.Series(parse_pentad(x), index=[lat_column_name, lng_column_name])
    )

    # Add latitude and longitude columns to the input DataFrame
    df[lat_column_name] = lat_long_df[lat_column_name]
    df[lng_column_name] = lat_long_df[lng_column_name]

    return df
