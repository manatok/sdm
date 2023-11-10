import pandas as pd
from ..data_prep.utils import add_lat_long_from_pentad
from .random_forest import train, predict


def plot(df):
    colors = df["target"].map({1: "green", -1: "gray", 0: "red"}).values

    plot_map(
        df,
        "target",
        colors=colors,
        filename=f"tmp_presence_absence_{species_id}",
        alongside=False,
    )


def run_model_pipeline(training_data_df, species_id: str):
    training_data_df = add_lat_long_from_pentad(training_data_df)

    positive_df = training_data_df.query("target == 1")

    print("Total observations: ", positive_df.shape[0])
    # Get all rows where target = 0
    negative_df = training_data_df.query("target == 0")
    print("Total pseudo-absence: ", negative_df.shape[0])

    balanced_df = pd.concat([positive_df, negative_df])
    print(balanced_df.columns)
    print(balanced_df.shape)

    model = train(balanced_df)
    predict(model, training_data_df, positive_df, negative_df, species_id)
