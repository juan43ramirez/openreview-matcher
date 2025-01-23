import argparse
import pandas as pd

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--output", type=str, help="Output file")
    argparser.add_argument("--assignments", type=str, help="Assignments file")

    args = argparser.parse_args()

    # TODO

    df = pd.DataFrame([["0bpM5H69Dj", "Yang_Jiao5", 0]])
    df.to_csv(args.output, index=False, header=False)