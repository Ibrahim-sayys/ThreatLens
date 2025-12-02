import pandas as pd
import numpy as np
import os

# ==========================================
# CONFIGURATION
# ==========================================
# Path to your existing dataset (based on your logs)
INPUT_FILE = '/home/ibrahim-sayys/Projects/ThreatLens/_dept_prediction_model/Preprocessing_on_DS/dataset_b_departments_v1.csv'

# Path where the new, augmented dataset will be saved
OUTPUT_FILE = '/home/ibrahim-sayys/Projects/ThreatLens/_dept_prediction_model/Preprocessing_on_DS/dataset_b_departments_augmented.csv'

# The minimum number of examples every department should have.
# If 'T_ADMIN' has 3 rows, we will duplicate them until we have 100.
MIN_SAMPLES_PER_LABEL = 100


def perform_random_oversampling(input_path, output_path, min_samples):
    print("========================================================")
    print("STARTING DATA AUGMENTATION (RANDOM OVERSAMPLING)")
    print("========================================================")

    # 1. Load Data
    if not os.path.exists(input_path):
        print(f"Error: File not found at {input_path}")
        return

    df = pd.read_csv(input_path)
    print(f"Loaded dataset: {df.shape[0]} rows, {df.shape[1]} columns")

    # 2. Identify Target Columns (Assuming they start with 'T_')
    target_cols = [col for col in df.columns if col.startswith('T_')]
    print(f"Identified {len(target_cols)} target labels: {target_cols}")

    # List to hold all the new rows we generate
    new_rows_list = []

    # 3. Iterate through each label and check if it needs boosting
    print("\n--- Checking Class Distribution ---")

    for label in target_cols:
        # Get all rows where this specific label is active (1)
        positive_rows = df[df[label] == 1]
        current_count = len(positive_rows)

        # If the label has 0 samples, we can't augment it (nothing to copy)
        if current_count == 0:
            print(f"Warning: Label '{label}' has 0 samples. Cannot augment.")
            continue

        # If the label is 'rare' (less than our threshold)
        if current_count < min_samples:
            # Calculate how many duplicates we need to add
            needed = min_samples - current_count

            # Sample with replacement (allows picking the same row multiple times)
            augmented_samples = positive_rows.sample(n=needed, replace=True, random_state=42)

            # Add these new rows to our list
            new_rows_list.append(augmented_samples)

            print(f" >> Augmenting {label}: Original={current_count} | Added {needed} copies | New Total={min_samples}")
        else:
            # Uncomment below if you want to see counts for healthy labels too
            # print(f"    OK: {label} has {current_count} samples.")
            pass

    # 4. Combine original data with new rows
    if len(new_rows_list) > 0:
        # Concatenate all new rows into a dataframe
        all_new_rows = pd.concat(new_rows_list, axis=0)

        # Merge with original dataframe
        df_augmented = pd.concat([df, all_new_rows], axis=0)

        # 5. Shuffle the dataset
        # This is crucial so that all the 'T_ADMIN' rows aren't stuck at the bottom
        df_augmented = df_augmented.sample(frac=1, random_state=42).reset_index(drop=True)

        print("\n========================================================")
        print(f"AUGMENTATION COMPLETE")
        print(f"Original Rows:  {len(df)}")
        print(f"Rows Added:     {len(all_new_rows)}")
        print(f"Final Rows:     {len(df_augmented)}")
        print("========================================================")

        # 6. Save to CSV
        df_augmented.to_csv(output_path, index=False)
        print(f"Saved augmented dataset to:\n{output_path}")

    else:
        print("\nNo augmentation needed! All classes met the minimum threshold.")


if __name__ == "__main__":
    perform_random_oversampling(INPUT_FILE, OUTPUT_FILE, MIN_SAMPLES_PER_LABEL)