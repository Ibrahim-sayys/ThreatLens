import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.naive_bayes import MultinomialNB
from xgboost import XGBClassifier
from catboost import CatBoostClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix, ConfusionMatrixDisplay
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE, RandomOverSampler
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

# Store all metrics for final summary
all_results = []  ### NEW


def preprocess_data(input_csv, balancing_choice):
    print(f"\nLoading dataset from {input_csv}...")
    data = pd.read_csv(input_csv)

    data.columns = data.columns.str.strip().str.lower()
    if 'urls' in data.columns:
        print("Dropping the 'urls' column...")
        data.drop(columns=['urls'], inplace=True)

    print("Shuffling the dataset...")
    data = data.sample(frac=1, random_state=42).reset_index(drop=True)

    keyword_cols = [col for col in data.columns if col.startswith('keyword') and not col.startswith('freq')]
    if not keyword_cols:
        raise ValueError("No keyword columns found!")

    for col in keyword_cols:
        data[col] = data[col].astype(str).str.strip().str.lower().replace('', pd.NA)

    data['category'] = data['category'].astype(str).str.strip().str.lower()

    total_missing_before = data[keyword_cols].isna().sum().sum()
    print(f" Total missing keyword values before filling: {total_missing_before}")

    for col in keyword_cols:
        data[col] = data.groupby('category')[col].transform(
            lambda x: x.fillna(x.mode().iloc[0]) if not x.mode().empty else x
        )

    total_missing_after = data[keyword_cols].isna().sum().sum()
    print(f" Total missing keyword values after filling: {total_missing_after}")
    print(f" Total filled: {total_missing_before - total_missing_after}")

    print("Combining keyword columns into one...")
    data['Keywords'] = data[keyword_cols].apply(lambda row: ' '.join(row.dropna().astype(str)), axis=1)

    print("Encoding labels...")
    label_encoder = LabelEncoder()
    data['category_label'] = label_encoder.fit_transform(data['category'])

    print("Vectorizing keywords using TF-IDF...")
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    X = vectorizer.fit_transform(data['Keywords'])
    y = data['category_label']

    print("\nClass distribution before balancing:")
    print(pd.Series(y).value_counts())

    if balancing_choice == "smote":
        print("Applying SMOTE...")
        X_balanced, y_balanced = SMOTE(random_state=42).fit_resample(X, y)
    elif balancing_choice == "random":
        print("Applying Random Oversampling...")
        X_balanced, y_balanced = RandomOverSampler(random_state=42).fit_resample(X, y)
    else:
        raise ValueError("Invalid balancing choice!")

    print("\nClass distribution after balancing:")
    print(pd.Series(y_balanced).value_counts())

    return X_balanced, y_balanced, label_encoder, vectorizer


def evaluate_model(classifier, X_test, y_test, model_filename, save_model, label_encoder, vectorizer, model_prefix, balancing_choice):  ### NEW param
    print("\nEvaluating model...")
    y_pred = classifier.predict(X_test)

    report = classification_report(y_test, y_pred, output_dict=True)
    acc = accuracy_score(y_test, y_pred)

    print("\nClassification Report:\n", classification_report(y_test, y_pred))
    print("Accuracy Score:", acc)

    # Save metrics for summary
    all_results.append({
        "Model": model_prefix,
        "Balancing": balancing_choice,
        "Accuracy": round(acc, 4),
        "Precision (macro)": round(report["macro avg"]["precision"], 4),
        "Recall (macro)": round(report["macro avg"]["recall"], 4),
        "F1-Score (macro)": round(report["macro avg"]["f1-score"], 4)
    })  ### NEW

    cm = confusion_matrix(y_test, y_pred)
    ConfusionMatrixDisplay(confusion_matrix=cm).plot(cmap=plt.cm.Blues, xticks_rotation=45)
    plt.title("Confusion Matrix")
    # Save the plot instead of showing it
    plt.savefig(f"{model_prefix}_{balancing_choice}_confusion_matrix.png")
    print(f"Confusion matrix saved as {model_prefix}_{balancing_choice}_confusion_matrix.png")
    plt.close()  # Close the figure to free memory

    if save_model:
        joblib.dump(classifier, model_filename)
        print(f"Model saved as {model_filename}")
        joblib.dump(label_encoder, f"{model_prefix}_label_encoder.pkl")
        joblib.dump(vectorizer, f"{model_prefix}_vectorizer.pkl")


def train_and_evaluate_model(model_func, model_name, X, y, save_model, label_encoder, vectorizer, balancing_choice):  ### NEW param
    print(f"\nTraining {model_name}...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    classifier = model_func()
    classifier.fit(X_train, y_train)
    evaluate_model(classifier, X_test, y_test, f"{model_name}.pkl", save_model, label_encoder, vectorizer, model_name, balancing_choice)  ### NEW


def generate_pdf_report(filename="model_performance_summary.pdf"):
    if not all_results:
        print("No results to save.")
        return

    df = pd.DataFrame(all_results)
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Model Performance Summary With Initial OnionMapper DS", styles["Title"]))
    elements.append(Spacer(1, 12))

    # Table data
    data = [df.columns.tolist()] + df.values.tolist()
    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F81BD")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey])
    ]))
    elements.append(table)
    doc.build(elements)

    print(f"\n📄 PDF report saved as: {filename}")


def model_random_forest():
    return RandomForestClassifier(random_state=42)


def model_naive_bayes():
    return MultinomialNB()


def model_xgboost():
    return XGBClassifier(random_state=42, n_estimators=100, learning_rate=0.1, max_depth=6)


def model_catboost():
    return CatBoostClassifier(random_state=42, iterations=100, learning_rate=0.1, depth=6, verbose=False)


def model_sgb():
    return GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, subsample=0.8, random_state=42)


if __name__ == "__main__":
    input_csv = "/home/ibrahim-sayys/Projects/ThreatLens/Dataset_Generation_from_urls/output_keywords.csv"

    while True:
        print("\nWhich option do you want?")
        print("[1] Train one model")
        print("[2] Run ALL models once with SMOTE and once with Random Oversampling")
        choice = input("Enter 1 or 2: ").strip()

        save_prompt = input("\nSave models? (yes/no): ").strip().lower()
        save_model = save_prompt == "yes"

        if choice == "1":
            print("\nBalancing methods:")
            print("[1] SMOTE")
            print("[2] Random Oversampling")
            bal_choice = "smote" if input("Enter 1 or 2: ").strip() == "1" else "random"

            X_balanced, y_balanced, label_encoder, vectorizer = preprocess_data(input_csv, bal_choice)

            print("\nModels:")
            print("[1] Random Forest")
            print("[2] Naive Bayes")
            print("[3] XGBoost")
            print("[4] CatBoost")
            print("[5] Stochastic Gradient Boosting")
            model_choice = input("Choose model: ").strip()

            models_map = {
                "1": (model_random_forest, "random_forest"),
                "2": (model_naive_bayes, "naive_bayes"),
                "3": (model_xgboost, "xgboost"),
                "4": (model_catboost, "catboost"),
                "5": (model_sgb, "stochastic_gradient_boosting"),
            }

            if model_choice in models_map:
                model_func, model_name = models_map[model_choice]
                train_and_evaluate_model(model_func, model_name, X_balanced, y_balanced, save_model, label_encoder, vectorizer, bal_choice)  ### NEW
            else:
                print("Invalid choice.")

        elif choice == "2":
            for bal_choice in ["smote", "random"]:
                print(f"\n=== Running all models with {bal_choice.upper()} ===")
                X_balanced, y_balanced, label_encoder, vectorizer = preprocess_data(input_csv, bal_choice)

                models_list = [
                    (model_random_forest, "random_forest"),
                    (model_naive_bayes, "naive_bayes"),
                    (model_xgboost, "xgboost"),
                    (model_catboost, "catboost"),
                    (model_sgb, "stochastic_gradient_boosting"),
                ]

                for model_func, model_name in models_list:
                    train_and_evaluate_model(model_func, model_name, X_balanced, y_balanced, save_model, label_encoder, vectorizer, bal_choice)  ### NEW

        else:
            print("Invalid choice.")

        # Generate PDF summary after each run
        generate_pdf_report("model_performance_summary.pdf")  ### NEW

        rerun = input("\nRun again? (yes/no): ").strip().lower()
        if rerun != "yes":
            print("Exiting...")
            break
