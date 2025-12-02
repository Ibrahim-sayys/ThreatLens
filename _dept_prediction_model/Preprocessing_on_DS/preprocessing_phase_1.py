import pandas as pd
import numpy as np

# 1. LOAD DATA
# We specifically read the 'departments' column as text to avoid errors
df = pd.read_csv('/home/ibrahim-sayys/Projects/ThreatLens/_dept_prediction_model/Dataset/department_threat_DS_v2.csv', usecols=['date', 'country', 'industry', 'departments'])

print(f"Loaded {len(df)} raw records.")

# ==========================================
# 2. DATE PARSING
# ==========================================
# Convert DD/MM/YYYY to datetime objects
df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
# Extract Month (Seasonality matters for departments too)
df['month_num'] = df['date'].dt.month

# ==========================================
# 3. REGION & INDUSTRY STANDARDIZATION (Must match Model A)
# ==========================================

# A. Region Logic
def get_region_id(country_name):
    c = str(country_name).lower().strip()
    # Region 0: North America
    if any(k in c for k in ['usa', 'united states', 'america', 'canada', 'mexico']):
        return 0
    # Region 1: EMEA
    elif any(k in c for k in ['uk', 'united kingdom', 'germany', 'france', 'italy', 'spain', 'russia', 'israel', 'europe']):
        return 1
    # Region 2: APAC/Other (Default)
    else:
        return 2

df['region_encoded'] = df['country'].apply(get_region_id)

# B. Industry Logic (Map to Integers)
# We need a manual map to turn strings into numbers consistently
industry_map = {
    'Healthcare': 0, 'Healthcare and Medical': 0,
    'Finance': 1, 'Financial Services': 1, 'Banking': 1, 'FinTech': 1,
    'Retail': 2, 'Retail and E-commerce': 2,
    'Tech': 3, 'Technology': 3, 'Technology and Software': 3, 'IT': 3,
    'Education': 4, 'Education and Training': 4,
    'Government': 5, 'Government and Public Sector': 5,
    'Manufacturing': 6, 'Manufacturing and Industrial': 6,
    'Energy': 7, 'Oil and Gas': 7, 'Energy and Utilities': 7,
    # Catch-all for others to avoid errors
}

def clean_industry(ind):
    ind = str(ind).strip()
    # Try direct match first
    if ind in industry_map: return industry_map[ind]
    # Try partial match (e.g. "Security Services" -> "Services")
    # For this demo, we'll default unknown industries to a specific ID (e.g., 8)
    return 8

df['industry_encoded'] = df['industry'].apply(clean_industry)

# ==========================================
# 4. DEPARTMENT EXPLOSION (Multi-Label)
# ==========================================

# A. Standardize Text
def clean_dept_text(text):
    if pd.isna(text): return ""
    text = str(text).lower().strip()
    # Fix separators (some might use ' ; ' or just ',')
    text = text.replace(';', ',')
    return text

df['Clean_Depts'] = df['departments'].apply(clean_dept_text)

# B. The Explosion
# Splits "HR, IT" into separate columns
dept_targets = df['Clean_Depts'].str.get_dummies(sep=', ')

# Prefix columns so we know they are targets (e.g., "T_IT")
dept_targets.columns = ['T_' + c.replace(' ', '_').upper() for c in dept_targets.columns]

# ==========================================
# 5. MERGE & SAVE
# ==========================================
# Combine Inputs (Region, Industry, Month) with Outputs (T_IT, T_HR...)
final_df = pd.concat([df[['region_encoded', 'industry_encoded', 'month_num']], dept_targets], axis=1)

# Drop rows with missing values (if date parsing failed)
final_df = final_df.dropna()

output_filename = 'dataset_b_departments_v1.csv'
final_df.to_csv(output_filename, index=False)

print(f"\nProcessing Complete!")
print(f"Saved {len(final_df)} rows to '{output_filename}'")
print("\n--- Target Columns Created ---")
print(dept_targets.columns.tolist())
