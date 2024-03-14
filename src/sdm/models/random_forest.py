import numpy as np
import pandas as pd
import random
from sklearn.metrics import roc_auc_score, accuracy_score, average_precision_score
from sklearn.model_selection import train_test_split

from sklearn.ensemble import RandomForestClassifier
from ..plot import plot_map
from ..utils import get_species_name
from sklearn.metrics import f1_score, precision_recall_curve, auc

random.seed(42)
np.random.seed(42)

drop_cols = [
    "target",
    "latitude",
    "longitude",
    "pentad",
]


def train(balanced_df):
    balanced_df = balanced_df.sample(frac=1, random_state=42)

    X = balanced_df.drop(columns=drop_cols)
    y = balanced_df["target"].to_numpy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=0
    )

    positive_observations = len(X_train[y_train == 1])

    print("Number of positive observations: ", positive_observations, flush=True)

    clf = RandomForestClassifier(random_state=42)

    # Fit the model on the training data
    clf.fit(X_train, y_train)

    # Use the model for evaluation on the test set
    y_pred = clf.predict(X_test)
    roc_auc = roc_auc_score(y_test, y_pred)
    average_precision = average_precision_score(y_test, y_pred, average="weighted")
    accuracy = accuracy_score(y_test, y_pred)
    threshold = 0.5
    y_pred_binary = (y_pred >= threshold).astype(int)
    f1 = f1_score(y_test, y_pred_binary)
    precision, recall, _ = precision_recall_curve(y_test, y_pred)
    pr_auc = auc(recall, precision)

    # Train on all the data
    clf.fit(X, y)

    results = {
        "total_training_presence_pentads": len(balanced_df[balanced_df["target"] == 1]),
        "total_training_absence_pentads": len(balanced_df[balanced_df["target"] == 0]),
        "roc_auc": roc_auc,
        "average_precision": average_precision,
        "accuracy": accuracy,
        "f1": f1,
        "precision_recall_auc": pr_auc,
    }

    print(results, flush=True)
    return clf, results


def predict(clf, training_data_df, positive_df, negative_df, species_id, output_dir):
    to_predict_df = training_data_df[training_data_df["target"] == -1].copy()

    proba_predictions = clf.predict_proba(to_predict_df.drop(columns=drop_cols))
    # Extract the probability of class 1
    class_1_probabilities = proba_predictions[:, 1]

    to_predict_df["target"] = class_1_probabilities

    known_df = pd.concat([positive_df, negative_df])

    combined_df = pd.concat([known_df, to_predict_df])

    pentad_probabilities = combined_df[["pentad", "target"]]

    plot_map(
        combined_df,
        "target",
        filename=f"{output_dir}/maps/{species_id}_{get_species_name(species_id)}_species_distribution",
        alongside=False,
    )

    combined_df.loc[combined_df["target"] < 0.7, "target"] = 0

    plot_map(
        combined_df,
        "target",
        filename=f"{output_dir}/maps/{species_id}_{get_species_name(species_id)}_species_distribution_abs",
        alongside=False,
    )

    return pentad_probabilities
