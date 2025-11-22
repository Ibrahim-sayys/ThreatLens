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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image, KeepTogether
from reportlab.lib.units import inch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import os

# Set high DPI for all matplotlib figures
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300


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
# VISUALIZATION FUNCTIONS
# --------------------------------------------
def create_confusion_matrix_image(conf_matrix, class_names, model_name, technique):
    """Create high-quality confusion matrix heatmap and save as image"""
    # Adjust figure size based on number of classes
    fig_size = max(8, len(class_names) * 0.8)
    plt.figure(figsize=(fig_size, fig_size))

    # Create heatmap
    sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues',
                xticklabels=class_names, yticklabels=class_names,
                cbar_kws={'label': 'Count'}, linewidths=0.5, linecolor='gray',
                annot_kws={'size': 10})

    plt.title(f'Confusion Matrix - {model_name}\n({technique})', fontsize=14, fontweight='bold', pad=15)
    plt.ylabel('True Label', fontsize=11, fontweight='bold')
    plt.xlabel('Predicted Label', fontsize=11, fontweight='bold')
    plt.xticks(rotation=45, ha='right', fontsize=9)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout()

    # Save to file with 300 DPI
    filename = f"cm_{model_name.replace(' ', '_')}_{technique.replace(' ', '_')}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    return filename


def create_classification_report_image(class_report, class_names, model_name, technique):
    """Create classification report as a table image"""
    # Adjust figure size based on number of classes
    fig_height = max(6, len(class_names) * 0.4 + 2)
    fig, ax = plt.subplots(figsize=(11, fig_height))
    ax.axis('tight')
    ax.axis('off')

    # Prepare data for table
    table_data = [['Class', 'Precision', 'Recall', 'F1-Score', 'Support']]

    for i, class_name in enumerate(class_names):
        class_key = str(i)
        if class_key in class_report:
            metrics = class_report[class_key]
            table_data.append([
                class_name,
                f"{metrics['precision']:.4f}",
                f"{metrics['recall']:.4f}",
                f"{metrics['f1-score']:.4f}",
                f"{int(metrics['support'])}"
            ])

    # Add separator
    table_data.append(['---', '---', '---', '---', '---'])

    # Add macro average
    table_data.append([
        'Macro Avg',
        f"{class_report['macro avg']['precision']:.4f}",
        f"{class_report['macro avg']['recall']:.4f}",
        f"{class_report['macro avg']['f1-score']:.4f}",
        f"{int(class_report['macro avg']['support'])}"
    ])

    # Add weighted average
    table_data.append([
        'Weighted Avg',
        f"{class_report['weighted avg']['precision']:.4f}",
        f"{class_report['weighted avg']['recall']:.4f}",
        f"{class_report['weighted avg']['f1-score']:.4f}",
        f"{int(class_report['weighted avg']['support'])}"
    ])

    # Create table
    table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                     colWidths=[0.35, 0.15, 0.15, 0.15, 0.15])

    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.8)

    # Style header row
    for i in range(5):
        cell = table[(0, i)]
        cell.set_facecolor('#3498DB')
        cell.set_text_props(weight='bold', color='white')

    # Style average rows
    for i in range(5):
        cell = table[(len(table_data) - 2, i)]
        cell.set_facecolor('#E8F8F5')
        cell.set_text_props(weight='bold')

        cell = table[(len(table_data) - 1, i)]
        cell.set_facecolor('#D5F4E6')
        cell.set_text_props(weight='bold')

    # Style separator row
    for i in range(5):
        cell = table[(len(table_data) - 3, i)]
        cell.set_facecolor('#BDC3C7')

    # Alternate row colors for class rows
    for row in range(1, len(class_names) + 1):
        for col in range(5):
            if row % 2 == 0:
                table[(row, col)].set_facecolor('#F8F9F9')
            else:
                table[(row, col)].set_facecolor('#FFFFFF')

    plt.title(f'Classification Report - {model_name}\n({technique})',
              fontsize=13, fontweight='bold', pad=15)

    # Save to file with 300 DPI
    filename = f"cr_{model_name.replace(' ', '_')}_{technique.replace(' ', '_')}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    return filename


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
def train_model_both_techniques(X, y, classifier_class, classifier_params, model_name, label_encoder):
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
        metrics = evaluate_model(clf, X_test, y_test, label_encoder)

        print(f"Accuracy with {technique}: {metrics['accuracy']:.4f}")

        # Generate visualizations
        class_names = label_encoder.classes_

        print(f"Generating confusion matrix image...")
        cm_image = create_confusion_matrix_image(
            metrics['confusion_matrix'],
            class_names,
            model_name,
            technique
        )

        print(f"Generating classification report image...")
        cr_image = create_classification_report_image(
            metrics['classification_report'],
            class_names,
            model_name,
            technique
        )

        results[technique] = {
            'classifier': clf,
            'metrics': metrics,
            'cm_image': cm_image,
            'cr_image': cr_image
        }

    return results


# --------------------------------------------
# PDF REPORT GENERATOR WITH IMAGES
# --------------------------------------------
def create_pdf_report(all_results, label_encoder, output_filename="model_comparison_report.pdf"):
    """Create PDF report comparing all models with both balancing techniques"""
    print("\n" + "=" * 60)
    print("Generating PDF Report...")
    print("=" * 60)

    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch
    )
    elements = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=20,
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
    elements.append(Spacer(1, 0.2 * inch))

    # Summary Table
    summary_data = [['Model', 'Balancing', 'Accuracy', 'Precision', 'Recall', 'F1-Score']]

    for model_name, techniques in all_results.items():
        for technique, data in techniques.items():
            metrics = data['metrics']
            report = metrics['classification_report']

            # Get weighted averages
            precision = report['weighted avg']['precision']
            recall = report['weighted avg']['recall']
            f1 = report['weighted avg']['f1-score']

            # Shorten technique name for table
            technique_short = "SMOTE" if technique == "SMOTE" else "Random OS"

            summary_data.append([
                model_name,
                technique_short,
                f"{metrics['accuracy']:.4f}",
                f"{precision:.4f}",
                f"{recall:.4f}",
                f"{f1:.4f}"
            ])

    summary_table = Table(summary_data,
                          colWidths=[1.4 * inch, 1.0 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
    ]))

    elements.append(Paragraph("<b>Performance Summary</b>", styles['Heading2']))
    elements.append(Spacer(1, 0.15 * inch))
    elements.append(summary_table)
    elements.append(PageBreak())

    # Detailed reports for each model WITH IMAGES
    for model_name, techniques in all_results.items():
        elements.append(Paragraph(f"<b>{model_name}</b>", styles['Heading2']))
        elements.append(Spacer(1, 0.15 * inch))

        for technique, data in techniques.items():
            metrics = data['metrics']

            elements.append(Paragraph(f"<b>Balancing: {technique}</b>", styles['Heading3']))
            elements.append(Paragraph(f"<b>Accuracy:</b> {metrics['accuracy']:.4f}", styles['Normal']))
            elements.append(Spacer(1, 0.1 * inch))

            # Classification Report Image with smart sizing
            elements.append(Paragraph("<b>Classification Report:</b>", styles['Heading4']))
            elements.append(Spacer(1, 0.05 * inch))

            # Calculate appropriate size to fit on page (max 5.5 inches height)
            cr_img = Image(data['cr_image'])
            aspect_ratio = cr_img.imageWidth / cr_img.imageHeight

            # Set width and calculate height maintaining aspect ratio
            img_width = 5.5 * inch
            img_height = img_width / aspect_ratio

            # If height is too large, scale down
            if img_height > 4.5 * inch:
                img_height = 4.5 * inch
                img_width = img_height * aspect_ratio

            cr_img.drawWidth = img_width
            cr_img.drawHeight = img_height
            cr_img.hAlign = 'CENTER'
            elements.append(cr_img)
            elements.append(Spacer(1, 0.15 * inch))

            # Confusion Matrix Image with smart sizing
            elements.append(Paragraph("<b>Confusion Matrix:</b>", styles['Heading4']))
            elements.append(Spacer(1, 0.05 * inch))

            cm_img = Image(data['cm_image'])
            cm_aspect_ratio = cm_img.imageWidth / cm_img.imageHeight

            # Set dimensions for confusion matrix (slightly smaller)
            cm_width = 4.5 * inch
            cm_height = cm_width / cm_aspect_ratio

            if cm_height > 4.5 * inch:
                cm_height = 4.5 * inch
                cm_width = cm_height * cm_aspect_ratio

            cm_img.drawWidth = cm_width
            cm_img.drawHeight = cm_height
            cm_img.hAlign = 'CENTER'
            elements.append(cm_img)
            elements.append(Spacer(1, 0.2 * inch))

        elements.append(PageBreak())

    # Build PDF
    try:
        doc.build(elements)
        print(f"\n✓ PDF Report saved as: {output_filename}")
        print(f"✓ All confusion matrix and classification report images saved at 300 DPI")
    except Exception as e:
        print(f"\n✗ Error building PDF: {e}")
        print("Images have been saved successfully. You can view them individually.")


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
        results = train_model_both_techniques(X, y, clf_class, params, model_name, label_encoder)
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