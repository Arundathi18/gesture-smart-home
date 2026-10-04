import os

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

from gesture_features import GESTURES

HERE = os.path.dirname(__file__)
DATA_FILE = os.path.join(HERE, "gesture_data.csv")
MODEL_FILE = os.path.join(HERE, "gesture_model.pkl")


def main():
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        print("No gesture data yet. Run `python3 collect_data.py` first and record each gesture.")
        return

    labels, features = [], []
    with open(DATA_FILE) as f:
        for line in f:
            row = line.strip().split(",")
            labels.append(row[0])
            features.append([float(v) for v in row[1:]])
    X, y = np.array(features), np.array(labels)

    present = [g for g in GESTURES if g in set(y)]
    print("Samples per gesture:", {g: int((y == g).sum()) for g in present})

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=0)
    model = RandomForestClassifier(n_estimators=200, random_state=0)
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    print(classification_report(y_test, pred, labels=present, zero_division=0))
    print("Confusion matrix (rows = actual, columns = predicted):", present)
    print(confusion_matrix(y_test, pred, labels=present))

    model.fit(X, y)  # retrain on everything for the final model
    joblib.dump(model, MODEL_FILE)
    print(f"Saved model to {MODEL_FILE}")


if __name__ == "__main__":
    main()
