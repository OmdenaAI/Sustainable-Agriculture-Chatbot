import json
import argparse

def compute_averages(jsonl_path):
    # Metrics to average
    metrics = [
        "ncdg",
        "mrr",
        "best_match_score",
        "average_f1",
        "average_precision",
        "average_recall"
    ]

    # Accumulators
    sums = {metric: 0.0 for metric in metrics}
    counts = 0

    # Read and process file
    with open(jsonl_path, "r") as f:
        for line in f:
            data = json.loads(line)

            if all(metric in data for metric in metrics):
                for metric in metrics:
                    sums[metric] += data[metric]
                counts += 1
            else:
                print("Skipping entry due to missing metrics")

    # Compute and print averages
    if counts == 0:
        print("No valid entries found.")
    else:
        print(f"\nAveraged over {counts} entries:")
        for metric in metrics:
            avg = sums[metric] / counts
            print(f"{metric}: {avg:.4f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute average evaluation metrics from a .jsonl file.")
    parser.add_argument(
        "--path",
        type=str,
        default="tools/evaluate_qdrant/data/eval_output/ws1-wosmallparagraphs_eval.jsonl",
        help="Path to the .jsonl file (default: tools/insert_db/data/eval_rerank.jsonl)"
    )
    args = parser.parse_args()
    compute_averages(args.path)
