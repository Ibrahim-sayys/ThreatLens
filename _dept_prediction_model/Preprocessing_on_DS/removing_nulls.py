# python
import os
import math
import random
import pandas as pd

def main():
    input_path = '/home/ibrahim-sayys/Projects/ThreatLens/_dept_prediction_model/Dataset/department_threat_DS_v1.csv'
    output_name = 'department_threat_DS_v2.csv'
    output_path = os.path.join(os.path.dirname(input_path), output_name)

    random.seed(42)
    df = pd.read_csv(input_path)

    # Lowercase only non-null strings, keep NaNs intact
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].mask(df[col].isna(), df[col]).str.lower()

    # Ensure country column exists
    if 'country' not in df.columns:
        df['country'] = pd.NA

    # Normalize "fake nulls" in country to real NaN
    df['country'] = df['country'].astype('string')
    fake_nulls = df['country'].str.strip().isin(['', 'nan', 'none', 'null'])
    df.loc[fake_nulls, 'country'] = pd.NA

    # python
    cols_to_drop = [f'Unnamed: {i}' for i in range(4, 11)]
    df = df.drop(columns=cols_to_drop, errors='ignore')
    # python
    date_fill_value = '10/09/2020'
    date_cols = [col for col in df.columns if 'date' in col.lower()]
    for col in date_cols:
        df[col] = df[col].fillna(date_fill_value)


    # Remove "usa", "america", "united states" if other countries exist in cell
    def clean_country(cell):
        if pd.isna(cell):
            return pd.NA
        countries = [c.strip() for c in cell.split(',')]
        # Remove unwanted
        unwanted = {'usa', 'america', 'united states'}
        filtered = [c for c in countries if c not in unwanted]
        if filtered:
            return filtered[0]
        # If only unwanted present, set as NA
        return pd.NA

    df['country'] = df['country'].apply(clean_country)

    # Fill nulls as before
    country_null_mask = df['country'].isna()
    null_count = int(country_null_mask.sum())
    if null_count > 0:
        countries_pool = ['germany', 'france', 'italy', 'spain', 'russia', 'israel', 'europe']
        n_fill_pool = math.floor(null_count * 0.7)
        n_fill_usa = null_count - n_fill_pool

        null_indices = df.index[country_null_mask].tolist()
        random.shuffle(null_indices)
        pool_indices = null_indices[:n_fill_pool]
        usa_indices = null_indices[n_fill_pool:]

        if n_fill_pool > 0:
            assigned = [random.choice(countries_pool) for _ in range(n_fill_pool)]
            df.loc[pool_indices, 'country'] = assigned
        if n_fill_usa > 0:
            df.loc[usa_indices, 'country'] = 'usa'

    df.to_csv(output_path, index=False)
    print(f"Saved: {output_path}")

    # Show nulls for all columns
    print("Nulls per column:")
    print(df.isna().sum())

if __name__ == '__main__':
    main()
