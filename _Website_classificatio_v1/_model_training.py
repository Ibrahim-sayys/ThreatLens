from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.naive_bayes import MultinomialNB
from xgboost import XGBClassifier
from catboost import CatBoostClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE, RandomOverSampler
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
import numpy as np


# --------------------------------------------
# PREPROCESSING
# --------------------------------------------
def preprocess_data(input_csv):
    print("Loading dataset...")
    data = pd.read_csv(input_csv)

    # Standardize column names
    data.columns = data.columns.str.strip().str.lower()

    # Drop URLs column if exists
    if 'urls' in data.columns:
        print("Dropping 'urls' column...")
        data.drop(columns=['urls'], inplace=True)

    print("Shuffling...")
    data = data.sample(frac=1, random_state=42).reset_index(drop=True)

    # Detect keyword columns
    keyword_cols = [col for col in data.columns if col.startswith("keyword")]
    if not keyword_cols:
        raise ValueError("No keyword columns found!")

    # Clean keyword columns
    print("Cleaning keyword columns...")
    for col in keyword_cols:
        data[col] = data[col].astype(str).str.strip().str.lower().replace('', pd.NA)

    # Category
    data['category'] = data['category'].astype(str).str.strip().str.lower()

    # Filling missing keyword values (per category)
    print("Filling missing keyword values...")
    for col in keyword_cols:
        data[col] = data.groupby('category')[col].transform(
            lambda x: x.fillna(x.mode().iloc[0]) if not x.mode().empty else x
        )

    # Combine all keywords
    print("Creating combined keyword text column...")
    data['keywords_text'] = data[keyword_cols].apply(
        lambda r: ' '.join(r.dropna().astype(str)),
        axis=1
    )

    # Encode labels
    print("Encoding labels...")
    label_encoder = LabelEncoder()
    data['category_label'] = label_encoder.fit_transform(data['category'])

    # TF-IDF Vectorization
    print("Vectorizing using TF-IDF...")
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    X = vectorizer.fit_transform(data['keywords_text'])
    y = data['category_label']

    print("\nClass distribution BEFORE balancing:")
    print(pd.Series(y).value_counts())

    return X, y, label_encoder, vectorizer


# --------------------------------------------
# EVALUATION
# --------------------------------------------
def evaluate_model(classifier, X_test, y_test, label_encoder):
    """Evaluate model and return metrics dictionary"""
    y_pred = classifier.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    conf_matrix = confusion_matrix(y_test, y_pred)
    class_report = classification_report(y_test, y_pred, output_dict=True)

    return {
        'accuracy': accuracy,
        'confusion_matrix': conf_matrix,
        'classification_report': class_report,
        'y_test': y_test,
        'y_pred': y_pred
    }


# --------------------------------------------
# TRAINING WITH BOTH BALANCING TECHNIQUES
# --------------------------------------------
def train_model_both_techniques(X, y, classifier_class, classifier_params, model_name):
    """Train model with both SMOTE and Random Oversampling"""
    print(f"\n{'=' * 60}")
    print(f"Training {model_name}...")
    print(f"{'=' * 60}")

    results = {}

    # Split data first
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    for technique in ['SMOTE', 'Random Oversampling']:
        print(f"\n--- Using {technique} ---")

        # Apply balancing
        if technique == 'SMOTE':
            X_train_balanced, y_train_balanced = SMOTE(random_state=42).fit_resample(X_train, y_train)
        else:
            X_train_balanced, y_train_balanced = RandomOverSampler(random_state=42).fit_resample(X_train, y_train)

        print(f"Training samples after {technique}: {X_train_balanced.shape[0]}")

        # Train model
        clf = classifier_class(**classifier_params)
        clf.fit(X_train_balanced, y_train_balanced)

        # Evaluate
        metrics = evaluate_model(clf, X_test, y_test, None)

        print(f"Accuracy with {technique}: {metrics['accuracy']:.4f}")

        results[technique] = {
            'classifier': clf,
            'metrics': metrics
        }

    return results


# --------------------------------------------
# PDF REPORT GENERATOR
# --------------------------------------------
def create_pdf_report(all_results, label_encoder, output_filename="model_comparison_report.pdf"):
    """Create PDF report comparing all models with both balancing techniques"""
    print("\n" + "=" * 60)
    print("Generating PDF Report...")
    print("=" * 60)

    doc = SimpleDocTemplate(output_filename, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=1  # Center
    )

    title = Paragraph("Model Performance Comparison Report", title_style)
    elements.append(title)

    # Timestamp
    timestamp = Paragraph(
        f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles['Normal']
    )
    elements.append(timestamp)
    elements.append(Spacer(1, 0.3 * inch))

    # Summary Table
    summary_data = [['Model', 'Balancing Technique', 'Accuracy', 'Precision', 'Recall', 'F1-Score']]

    for model_name, techniques in all_results.items():
        for technique, data in techniques.items():
            metrics = data['metrics']
            report = metrics['classification_report']

            # Get weighted averages
            precision = report['weighted avg']['precision']
            recall = report['weighted avg']['recall']
            f1 = report['weighted avg']['f1-score']

            summary_data.append([
                model_name,
                technique,
                f"{metrics['accuracy']:.4f}",
                f"{precision:.4f}",
                f"{recall:.4f}",
                f"{f1:.4f}"
            ])

    summary_table = Table(summary_data,
                          colWidths=[1.5 * inch, 1.5 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))

    elements.append(Paragraph("<b>Performance Summary</b>", styles['Heading2']))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(summary_table)
    elements.append(PageBreak())

    # Detailed reports for each model
    for model_name, techniques in all_results.items():
        elements.append(Paragraph(f"<b>{model_name}</b>", styles['Heading2']))
        elements.append(Spacer(1, 0.2 * inch))

        for technique, data in techniques.items():
            metrics = data['metrics']
            report = metrics['classification_report']
            conf_matrix = metrics['confusion_matrix']

            elements.append(Paragraph(f"<b>Balancing Technique: {technique}</b>", styles['Heading3']))
            elements.append(Spacer(1, 0.1 * inch))

            # Accuracy
            elements.append(Paragraph(f"<b>Accuracy:</b> {metrics['accuracy']:.4f}", styles['Normal']))
            elements.append(Spacer(1, 0.1 * inch))

            # Classification Report Table
            class_data = [['Class', 'Precision', 'Recall', 'F1-Score', 'Support']]

            for class_label, class_metrics in report.items():
                if class_label not in ['accuracy', 'macro avg', 'weighted avg']:
                    class_name = label_encoder.inverse_transform([int(class_label)])[
                        0] if class_label.isdigit() else class_label
                    class_data.append([
                        str(class_name),
                        f"{class_metrics['precision']:.4f}",
                        f"{class_metrics['recall']:.4f}",
                        f"{class_metrics['f1-score']:.4f}",
                        str(int(class_metrics['support']))
                    ])

            # Add averages
            class_data.append(['Macro Avg',
                               f"{report['macro avg']['precision']:.4f}",
                               f"{report['macro avg']['recall']:.4f}",
                               f"{report['macro avg']['f1-score']:.4f}",
                               str(int(report['macro avg']['support']))])
            class_data.append(['Weighted Avg',
                               f"{report['weighted avg']['precision']:.4f}",
                               f"{report['weighted avg']['recall']:.4f}",
                               f"{report['weighted avg']['f1-score']:.4f}",
                               str(int(report['weighted avg']['support']))])

            class_table = Table(class_data, colWidths=[2 * inch, 1 * inch, 1 * inch, 1 * inch, 1 * inch])
            class_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ECC71')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))

            elements.append(class_table)
            elements.append(Spacer(1, 0.2 * inch))

            # Confusion Matrix
            elements.append(Paragraph("<b>Confusion Matrix:</b>", styles['Normal']))
            elements.append(Spacer(1, 0.1 * inch))

            # Create confusion matrix table
            cm_data = [[''] + [f'Pred {i}' for i in range(len(conf_matrix))]]
            for i, row in enumerate(conf_matrix):
                cm_data.append([f'True {i}'] + [str(val) for val in row])

            cm_table = Table(cm_data)
            cm_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('BACKGROUND', (0, 0), (0, -1), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (1, 1), (-1, -1), colors.lightblue),
            ]))

            elements.append(cm_table)
            elements.append(Spacer(1, 0.3 * inch))

        elements.append(PageBreak())

    # Build PDF
    doc.build(elements)
    print(f"\n✓ PDF Report saved as: {output_filename}")


# --------------------------------------------
# MAIN
# --------------------------------------------
if __name__ == "__main__":

    input_csv = "features_output_data.csv"
    X, y, label_encoder, vectorizer = preprocess_data(input_csv)

    print("\n" + "=" * 60)
    print("Select models to train:")
    print("=" * 60)
    print("[1] Random Forest")
    print("[2] Naive Bayes")
    print("[3] XGBoost")
    print("[4] CatBoost")
    print("[5] Gradient Boosting")
    print("[6] ALL MODELS")
    print("=" * 60)

    choice = input("Enter choice: ").strip()
    save_prompt = input("Save models? (yes/no): ").strip().lower()
    save_model = save_prompt == "yes"

    # Model configurations
    models_config = {
        'Random Forest': (RandomForestClassifier, {'random_state': 42}, 'random_forest'),
        'Naive Bayes': (MultinomialNB, {}, 'naive_bayes'),
        'XGBoost': (XGBClassifier, {
            'random_state': 42,
            'n_estimators': 100,
            'learning_rate': 0.1,
            'max_depth': 6,
            'use_label_encoder': False,
            'eval_metric': 'mlogloss'
        }, 'xgboost'),
        'CatBoost': (CatBoostClassifier, {
            'random_state': 42,
            'iterations': 100,
            'learning_rate': 0.1,
            'depth': 6,
            'verbose': False
        }, 'catboost'),
        'Gradient Boosting': (GradientBoostingClassifier, {
            'n_estimators': 100,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'random_state': 42
        }, 'gradient_boosting')
    }

    # Determine which models to train
    if choice == "6":
        selected_models = models_config
    elif choice in ["1", "2", "3", "4", "5"]:
        model_names = list(models_config.keys())
        selected_model_name = model_names[int(choice) - 1]
        selected_models = {selected_model_name: models_config[selected_model_name]}
    else:
        print("Invalid choice. Exiting...")
        exit()

    # Train all selected models
    all_results = {}

    for model_name, (clf_class, params, model_prefix) in selected_models.items():
        results = train_model_both_techniques(X, y, clf_class, params, model_name)
        all_results[model_name] = results

        # Save models if requested
        if save_model:
            for technique, data in results.items():
                technique_suffix = technique.replace(' ', '_').lower()
                filename = f"{model_prefix}_{technique_suffix}.pkl"
                joblib.dump(data['classifier'], filename)
                print(f"✓ Saved: {filename}")

            # Save label encoder and vectorizer once per model
            joblib.dump(label_encoder, f"{model_prefix}_label_encoder.pkl")
            joblib.dump(vectorizer, f"{model_prefix}_vectorizer.pkl")
            print(f"✓ Saved: {model_prefix}_label_encoder.pkl")
            print(f"✓ Saved: {model_prefix}_vectorizer.pkl")

    # Generate PDF Report
    create_pdf_report(all_results, label_encoder)

    print("\n" + "=" * 60)
    print("All tasks completed successfully!")
    print("=" * 60)