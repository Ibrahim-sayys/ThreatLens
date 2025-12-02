import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer, LabelEncoder
import os


def process_data(input_file, output_file):
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: The file '{input_file}' was not found.")
        print("Please make sure the CSV file is in the same directory as this script.")
        return

    print(f"Loading data from {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # 1. Clean Column Names
    # Remove any accidental leading/trailing spaces from column headers
    df.columns = [c.strip() for c in df.columns]

    # 2. Drop Region (country) and Month (date)
    # We check for various common names just in case
    cols_to_drop = ['date', 'month', 'country', 'region']
    existing_drop_cols = [c for c in cols_to_drop if c in df.columns]

    if existing_drop_cols:
        df = df.drop(columns=existing_drop_cols)
        print(f"Dropped columns: {existing_drop_cols}")

    # Remove any completely empty columns (often caused by trailing commas in CSVs)
    df = df.dropna(axis=1, how='all')

    # 3. Process 'departments' (One-Hot Encoding)
    print("Encoding 'departments'...")
    # Ensure all are strings, handle NaN, and split by comma
    df['departments'] = df['departments'].fillna('').astype(str)
    # Split "HR, IT, Sales" -> ["HR", "IT", "Sales"] and strip whitespace
    df['departments_split'] = df['departments'].apply(lambda x: [item.strip() for item in x.split(',') if item.strip()])

    mlb = MultiLabelBinarizer()
    departments_encoded = mlb.fit_transform(df['departments_split'])
    departments_df = pd.DataFrame(departments_encoded, columns=mlb.classes_)

    # 4. Process 'industry' (Label Encoding)
    print("Encoding 'industry'...")
    le = LabelEncoder()
    # Ensure industry is string and clean it
    df['industry'] = df['industry'].astype(str).str.strip()
    df['industry_encoded'] = le.fit_transform(df['industry'])

    # Create a mapping dictionary to show the user later
    industry_mapping = dict(zip(le.classes_, le.transform(le.classes_)))

    # 5. Create Final DataFrame
    # We want [Industry Encoded] + [Department Columns]
    # We drop the original raw text columns
    final_df = pd.concat([df[['industry_encoded']], departments_df], axis=1)

    # 6. Save to CSV
    final_df.to_csv(output_file, index=False)
    print(f"\nSuccess! Processed data saved to: {output_file}")
    print(f"New Data Shape: {final_df.shape}")

    # 7. Print Industry Mapping for Reference
    print("\nIMPORTANT: Keep this Industry Mapping to use your model later:")
    print("-" * 50)
    print(f"{'ID':<5} | {'Industry Name'}")
    print("-" * 50)
    # Sort by ID for easier reading
    sorted_mapping = sorted(industry_mapping.items(), key=lambda x: x[1])
    for name, id_num in sorted_mapping:
        print(f"{id_num:<5} | {name}")
    print("-" * 50)


if __name__ == "__main__":
    INPUT_FILENAME = '/home/ibrahim-sayys/Projects/ThreatLens/_dept_prediction_model/Dataset/department_threat_DS_v2.csv'

    OUTPUT_FILENAME = 'Dept_DS_New_shape.csv'

    process_data(INPUT_FILENAME, OUTPUT_FILENAME)