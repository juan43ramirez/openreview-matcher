import json
import pandas as pd
import argparse

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--input", type=str, help="Input file")
    argparser.add_argument("--output", type=str, help="Output file")

    args = argparser.parse_args()

    dfs = []
    with open(args.input, "r") as f:
        data = json.load(f)
        for key, value in data.items():
            df = pd.DataFrame(value)
            df["paper_id"] = key
            dfs.append(df)

    df = pd.concat(dfs)
    df = df[["paper_id", "user", "aggregate_score"]]

    df.to_csv(args.output, index=False, header=False)
