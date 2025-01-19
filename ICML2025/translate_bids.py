"""Doing this translation manually for the tests"""

import pandas as pd

TRANSLATE_MAP = {
    "Very High": 1,
    "High": 0.75,
    "Neutral": 0,
    "Low": -0.5,
    "Very Low": -1,
}

if __name__ == "__main__":
    # Load the data
    data = pd.read_csv("ICML2025/data/bids100.csv")

    data["bid"] = data["bid"].map(TRANSLATE_MAP)

    # Save the translated data
    data.to_csv("ICML2025/data/numeric_bids100.csv", index=False, header=False)