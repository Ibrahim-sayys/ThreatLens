import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, hamming_loss, f1_score
import joblib
import os

# 1. Load Data
INPUT_FILE = '/home/ibrahim-sayys/Projects/ThreatLens/_dept_prediction_model/Preprocessing_on_DS/Dept_DS_New_shape.csv'
if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(f"Could not find {INPUT_FILE}. Please run process_dataset.py first.")

print("Loading dataset...")
df = pd.read_csv(INPUT_FILE)

# 2. Prepare X and Y
X = df['industry_encoded'].values.reshape(-1, 1)
department_columns = [col for col in df.columns if col != 'industry_encoded']
y = df[department_columns].values

print(f"Training with {len(X)} rows.")
print(f"Predicting {len(department_columns)} departments.")

# 3. Split Data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Initialize and Train Random Forest
print("Training Random Forest...")
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

# 5. Evaluate (The BETTER way)
y_pred = rf_model.predict(X_test)

# Hamming Loss: The fraction of labels that are incorrectly predicted.
# Lower is better. 0 is perfect.
h_loss = hamming_loss(y_test, y_pred)
accuracy_per_label = 1 - h_loss

# F1 Score: A weighted average of Precision and Recall.
# Higher is better. 1 is perfect.
f1 = f1_score(y_test, y_pred, average='micro')

print("\n--- MODEL PERFORMANCE ---")
print(f"Label Accuracy (1 - Hamming Loss): {accuracy_per_label:.2%}")
print(f"F1 Score (Micro Average):          {f1:.2%}")
print(f"Exact Match Ratio (The harsh one): {accuracy_score(y_test, y_pred):.2%}")
print("-------------------------")
print("Interpretation: 'Label Accuracy' is the chance the model gets any single department right.")

# 6. Save the Model
joblib.dump(rf_model, 'department_rf_model.pkl')
joblib.dump(department_columns, 'department_names.pkl')
print("\nModel saved as 'department_rf_model.pkl'")

# --- DEMONSTRATION ---
print("\n--- TEST PREDICTION ---")
# Pick a random industry ID from the test set
sample_id = X_test[0][0]
print(f"Predicting for Industry ID: {sample_id}")

predictions_proba = rf_model.predict_proba([[sample_id]])

print("Departments with > 50% Risk:")
for i, dept_name in enumerate(department_columns):
    # Handle cases where a department might be constant (0 variance)
    if predictions_proba[i].shape[1] > 1:
        prob = predictions_proba[i][0][1]
    else:
        prob = 0.0

    if prob > 0.5:
        print(f" - {dept_name}: {prob * 100:.1f}%")