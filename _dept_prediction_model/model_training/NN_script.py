import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from sklearn.model_selection import train_test_split
import os

# 1. Load the processed dataset
INPUT_FILE = 'Dept_DS_New_shape.csv'
if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(f"Could not find {INPUT_FILE}. Please run process_dataset.py first.")

print("Loading dataset...")
df = pd.read_csv(INPUT_FILE)

# 2. Separate Features (X) and Targets (Y)
# X is just the 'industry_encoded' column
X = df['industry_encoded'].values

# Y is everything else (the departments)
department_columns = [col for col in df.columns if col != 'industry_encoded']
y = df[department_columns].values

print(f"Features (X) shape: {X.shape}")
print(f"Targets (Y) shape: {y.shape}")
print(f"Number of distinct Industries: {df['industry_encoded'].max() + 1}")
print(f"Number of Departments to predict: {len(department_columns)}")

# 3. Split into Train and Test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Build the Neural Network
# We use an Embedding layer because 'industry_encoded' is a categorical integer, not a quantity.
num_unique_industries = int(df['industry_encoded'].max()) + 1
num_outputs = y.shape[1]

model = models.Sequential([
    # Input Layer: Expects 1 integer (the industry ID)
    layers.Input(shape=(1,)),

    # Embedding Layer: Turns the integer ID into a vector of size 16
    # This helps the model learn relationships between industries better than just raw numbers
    layers.Embedding(input_dim=num_unique_industries, output_dim=16),

    # Flatten: Collapses the embedding to feed into Dense layers
    layers.Flatten(),

    # Hidden Layer: Learns patterns
    layers.Dense(64, activation='relu'),
    layers.Dropout(0.2),  # Prevents overfitting

    # Output Layer: One neuron per department
    # Sigmoid activation allows multiple departments to be "active" ( > 0.5) at once
    layers.Dense(num_outputs, activation='sigmoid')
])

# 5. Compile the Model
model.compile(optimizer='adam',
              loss='binary_crossentropy',  # Standard loss for multi-label classification
              metrics=['accuracy'])

print("\nStarting training...")
history = model.fit(X_train, y_train,
                    epochs=50,
                    batch_size=32,
                    validation_split=0.2,
                    verbose=1)

# 6. Evaluate
print("\nEvaluating on Test set...")
loss, accuracy = model.evaluate(X_test, y_test)
print(f"Test Accuracy: {accuracy:.4f}")

# 7. Save the Model
model.save('department_risk_model.keras')
print("\nModel saved as 'department_risk_model.keras'")

# --- DEMONSTRATION: How to use it ---
print("\n--- TEST PREDICTION ---")
# Let's pick a random industry ID from the test set to see what happens
sample_id = X_test[0]
print(f"Predicting for Industry ID: {sample_id}")

# Predict
prediction = model.predict(np.array([sample_id]))[0]

# Show results
print("Departments with > 50% Risk:")
for i, prob in enumerate(prediction):
    if prob > 0.5:
        print(f" - {department_columns[i]}: {prob * 100:.1f}% confidence")