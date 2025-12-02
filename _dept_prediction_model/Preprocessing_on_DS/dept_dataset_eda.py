"""Exploratory analysis for the department dataset.

Reads the preprocessed CSV, prints structural statistics, highlights missing data,
reports the distribution of encoded metadata columns, and quantifies class
imbalance for all `T_` targets.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.switch_backend("Agg")

SCRIPT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET = SCRIPT_ROOT / "dataset_b_departments_v1.csv"
TARGET_PREFIX = "T_"


def load_dataset(dataset_path: Path) -> pd.DataFrame:
    """Load the dataset and ensure the path exists."""
    dataset_path = dataset_path.expanduser().resolve()
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")
    return pd.read_csv(dataset_path)


def print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def dataset_overview(df: pd.DataFrame) -> None:
    print_section("Dataset overview")
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print("Memory usage: {:.2f} MB".format(df.memory_usage(deep=True).sum() / 1_048_576))
    print("Columns:", ", ".join(df.columns.tolist()))
    print("\nData types:")
    print(df.dtypes.value_counts())
    print("\nNumeric summary:")
    print(df.describe(include="number").T)
    print("\nPreview:")
    print(df.head())


def inspect_encoded_columns(df: pd.DataFrame, encoded_columns: Sequence[str]) -> None:
    available = [col for col in encoded_columns if col in df.columns]
    if not available:
        return
    print_section("Encoded columns and value counts")
    for col in available:
        print(f"\n{col} ({df[col].nunique()} unique values):")
        print(df[col].value_counts().sort_index())


def report_missing(df: pd.DataFrame) -> None:
    missing = df.isna().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    if missing.empty:
        print_section("Missing values")
        print("No missing values detected.")
        return
    print_section("Missing values")
    print(missing)


def summarize_label_balance(
    df: pd.DataFrame, prefix: str = TARGET_PREFIX
) -> pd.DataFrame:
    label_columns = [col for col in df.columns if col.startswith(prefix)]
    if not label_columns:
        raise ValueError(f"No columns starting with '{prefix}' found.")
    total = len(df)
    positives = df[label_columns].sum()
    summary = (
        pd.DataFrame(
            {
                "positive": positives,
                "negative": total - positives,
                "positive_ratio_%": positives / total * 100,
            }
        )
        .assign(
            imbalance_ratio=lambda frame: frame["positive"]
            / frame["negative"].replace({0: np.nan})
        )
        .sort_values(by="positive_ratio_%")
    )
    print_section("Class imbalance report")
    print(
        summary[
            ["positive", "negative", "positive_ratio_%", "imbalance_ratio"]
        ]
    )
    return summary


def save_class_distribution_plot(summary: pd.DataFrame, artifacts_dir: Path) -> Path:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, max(5, len(summary) * 0.3)))
    summary_sorted = summary.sort_values("positive_ratio_%")
    ax.barh(summary_sorted.index, summary_sorted["positive_ratio_%"], color="#2c7fb8")
    ax.set_xlabel("Positive ratio (%)")
    ax.set_title("Target-wise positive rate (class imbalance)")
    ax.grid(axis="x", alpha=0.5)
    plt.tight_layout()
    target_plot = artifacts_dir / "class_imbalance_positive_rate.png"
    fig.savefig(target_plot)
    plt.close(fig)
    print(f"Saved class imbalance chart to {target_plot}")
    return target_plot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run EDA and class imbalance reporting for the department dataset."
    )
    parser.add_argument(
        "-d",
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
        help="Path to the department dataset CSV file.",
    )
    parser.add_argument(
        "-o",
        "--artifacts-dir",
        type=Path,
        default=None,
        help="Directory to dump plots or other artifacts. Defaults to the dataset parent.",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        type=str,
        default=TARGET_PREFIX,
        help="Prefix string to select label columns (default: %(default)s).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_dataset(args.dataset)
    dataset_overview(df)
    inspect_encoded_columns(df, ["region_encoded", "industry_encoded"])
    report_missing(df)
    label_summary = summarize_label_balance(df, prefix=args.prefix)
    artifacts_root = args.artifacts_dir or args.dataset.parent
    save_class_distribution_plot(label_summary, artifacts_root)


if __name__ == "__main__":
    main()

