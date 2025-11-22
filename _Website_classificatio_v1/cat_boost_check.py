import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from catboost import CatBoostClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from imblearn.over_sampling import RandomOverSampler
from imblearn.pipeline import Pipeline as ImbPipeline

# Set styling for plots
plt.rcParams['figure.dpi'] = 300
sns.set_style("whitegrid")


# --------------------------------------------
# 1. PREPROCESSING (Copied from your script)
# --------------------------------------------
def preprocess_data(input_csv):
    print("Loading and preprocessing dataset...")
    data = pd.read_csv(input_csv)
    data.columns = data.columns.str.strip().str.lower()

    if 'urls' in data.columns:
        data.drop(columns=['urls'], inplace=True)

    # Detect keyword columns
    keyword_cols = [col for col in data.columns if col.startswith("keyword")]

    # Clean strings
    for col in keyword_cols:
        data[col] = data[col].astype(str).str.strip().str.lower().replace('nan', '')
    data['category'] = data['category'].astype(str).str.strip().str.lower()

    # Fill missing
    for col in keyword_cols:
        data[col] = data.groupby('category')[col].transform(
            lambda x: x.fillna(x.mode().iloc[0]) if not x.mode().empty else x
        )

    # Combine text
    data['keywords_text'] = data[keyword_cols].apply(
        lambda r: ' '.join(r.dropna().astype(str)), axis=1
    )

    # Encode
    label_encoder = LabelEncoder()
    data['category_label'] = label_encoder.fit_transform(data['category'])

    # TF-IDF
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    X = vectorizer.fit_transform(data['keywords_text'])
    y = data['category_label']

    return X, y, label_encoder, vectorizer


# --------------------------------------------
# 2. THE "IS IT LUCK?" AUDIT
# --------------------------------------------
def audit_catboost_stability(X, y, label_encoder):
    print("\n" + "=" * 60)
    print("STARTING CATBOOST STABILITY AUDIT")
    print("=" * 60)

    # Define the exact model configuration from your report
    cat_model = CatBoostClassifier(
        iterations=100,
        learning_rate=0.1,
        depth=6,
        verbose=False,
        random_seed=42,
        allow_writing_files=False
    )

    # Create a Pipeline:
    # 1. Oversample the training data (Random OS)
    # 2. Train CatBoost
    # Note: The pipeline ensures validation data is NEVER oversampled (Crucial!)
    pipeline = ImbPipeline([
        ('balancing', RandomOverSampler(random_state=42)),
        ('classification', cat_model)
    ])

    # 5-Fold Stratified Cross Validation
    # This splits data into 5 chunks and runs the model 5 times
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    print("Running 5-Fold Cross-Validation (this may take a moment)...")

    # Get accuracy scores for all 5 runs
    scores = cross_val_score(pipeline, X, y, cv=cv, scoring='accuracy')

    # --------------------------------------------
    # 3. REPORTING THE TRUTH
    # --------------------------------------------
    mean_score = np.mean(scores)
    std_dev = np.std(scores)

    print("\n" + "-" * 40)
    print(f"AUDIT RESULTS (Based on 5 distinct test runs)")
    print("-" * 40)
    print(f"Run 1: {scores[0]:.4f}")
    print(f"Run 2: {scores[1]:.4f}")
    print(f"Run 3: {scores[2]:.4f}")
    print(f"Run 4: {scores[3]:.4f}")
    print(f"Run 5: {scores[4]:.4f}")
    print("-" * 40)
    print(f"AVERAGE ACCURACY:  {mean_score:.2%}")
    print(f"VOLATILITY (STD):  ±{std_dev:.2%}")
    print("-" * 40)

    # Interpretation
    print("\nVERDICT:")
    if std_dev < 0.05:
        print(">> STABLE. The model is consistent. It likely learned real patterns.")
    elif std_dev < 0.10:
        print(">> SOMEWHAT UNSTABLE. Performance varies depending on the data split.")
    else:
        print(">> UNSTABLE / LUCKY. The model creates wildy different results.")

    # --------------------------------------------
    # 4. VISUALIZATION
    # --------------------------------------------
    plt.figure(figsize=(10, 6))

    # Plot individual scores
    plt.plot(range(1, 6), scores, marker='o', linestyle='-', color='#2ecc71', linewidth=2, label='Run Score')

    # Plot average line
    plt.axhline(y=mean_score, color='#e74c3c', linestyle='--', label=f'Mean ({mean_score:.2f})')

    plt.fill_between(range(1, 6),
                     mean_score - std_dev,
                     mean_score + std_dev,
                     color='#e74c3c', alpha=0.1, label='Volatility Zone')

    plt.title('CatBoost Reliability Check (5-Fold CV)', fontsize=14, fontweight='bold')
    plt.xlabel('Test Run #')
    plt.ylabel('Accuracy Score')
    plt.ylim(0, 1.05)
    plt.legend()
    plt.xticks([1, 2, 3, 4, 5])

    plt.savefig('catboost_stability_audit.png')
    print("\n✓ Stability chart saved as 'catboost_stability_audit.png'")


if __name__ == "__main__":
    # File name
    input_csv = "features_output_data.csv"

    try:
        # Run Process
        X, y, enc, vec = preprocess_data(input_csv)
        audit_catboost_stability(X, y, enc)

    except FileNotFoundError:
        print(f"Error: Could not find {input_csv}. Please make sure the file is in the folder.")