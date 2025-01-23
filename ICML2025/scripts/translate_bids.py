import pandas as pd
import argparse

TRANSLATE_MAP = {
    "Very High": 1,
    "High": 0.75,
    "Neutral": 0,
    "Low": -0.5,
    "Very Low": -1,
}

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--input", type=str, help="Input file")
    argparser.add_argument("--output", type=str, help="Output file")

    args = argparser.parse_args()

    print(f"\nTranslating bids to numerical values")

    # Load the data
    data = pd.read_csv(args.input, header=None)

    if data.iloc[0, 0] == "paper id":
        data = data.iloc[1:]

    data[2] = data[2].map(TRANSLATE_MAP)

    # Save the translated data
    data.to_csv(args.output, index=False, header=False)


    print(f"Done. Translated {len(data)} bids")