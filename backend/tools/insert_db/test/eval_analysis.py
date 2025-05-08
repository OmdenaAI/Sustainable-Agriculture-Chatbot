import json

# Path to your .jsonl file
jsonl_path = "tools/insert_db/data/eval.jsonl"

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
