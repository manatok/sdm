import numpy as np
import pandas as pd
import random
from sklearn.metrics import roc_auc_score, accuracy_score
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score

# from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from ..plot import plot_map

random.seed(42)
np.random.seed(42)

drop_cols = [
    "target",
    "latitude",
    "longitude",
    "pentad",
    "target_observations",
    "total_observations",
]


def train(balanced_df):
    # Oversampling using SMOTE (if needed)
    balanced_df = balanced_df.sample(frac=1, random_state=42)

    # split the dataframe into features (X) and target (y)

    X = balanced_df.drop(columns=drop_cols)
    y = balanced_df["target"].to_numpy()

    # Split the data into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=0
    )

    # smote = SMOTE()
    # X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
    X_train_balanced, y_train_balanced = X_train, y_train

    # Define the model
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        bootstrap=True,
        random_state=42,
        n_jobs=1,
    )

    # Perform cross-validation
    cv = StratifiedKFold(n_splits=2)
    scores = cross_val_score(
        clf, X_train_balanced, y_train_balanced, cv=cv, scoring="roc_auc"
    )
    print(
        "Cross-validation ROC AUC: %0.4f (+/- %0.2f)"
        % (scores.mean(), scores.std() * 2)
    )

    # Fit the model on the training data
    clf.fit(X_train_balanced, y_train_balanced)

    # Use the model for evaluation on the test set
    y_pred = clf.predict(X_test)
    roc_auc = roc_auc_score(y_test, y_pred)
    accuracy = accuracy_score(y_test, y_pred)
    print("Test ROC AUC: {:.4f}".format(roc_auc))
    print("Test Accuracy: {:.4f}".format(accuracy))

    clf.fit(X, y)

    return clf


def predict(clf, training_data_df, positive_df, negative_df, species_id):
    to_predict_df = training_data_df[training_data_df["target"] == -1]

    proba_predictions = clf.predict_proba(to_predict_df.drop(columns=drop_cols))
    # Extract the probability of class 1
    class_1_probabilities = proba_predictions[:, 1]

    to_predict_df["target"] = class_1_probabilities
    # to_predict_df['target'] = proba_predictions

    known_df = pd.concat([positive_df, negative_df])
    # known_df['target'] = np.where(known_df['target']==0, -1, np.where(known_df['target']==1, 2, known_df['target']))

    combined_df = pd.concat([known_df, to_predict_df])

    plot_map(
        combined_df,
        "target",
        filename=f"species_distribution_{species_id}",
        alongside=False,
    )

    combined_df.loc[combined_df["target"] < 0.7, "target"] = 0
    # colors = combined_df['target'].map({1:'lightgreen', 0:'lightcoral', 2:'green', -1: 'red'}).values

    plot_map(
        combined_df,
        "target",
        filename=f"species_distribution_abs_{species_id}",
        alongside=False,
    )
