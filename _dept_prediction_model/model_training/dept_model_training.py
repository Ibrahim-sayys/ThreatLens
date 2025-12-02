import pandas as pd
import numpy as np
import argparse
import json
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import hamming_loss, precision_score, recall_score, f1_score
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from joblib import dump

# XGBoost import
try:
    from xgboost import XGBClassifier
except ImportError:
    XGBClassifier = None


def load_data(path):
    df = pd.read_csv(path)
    return df


def get_feature_and_targets(df):
    feature_cols = ['region_encoded', 'industry_encoded', 'month_num']
    missing_features = [c for c in feature_cols if c not in df.columns]
    if missing_features:
        raise ValueError(f"Missing expected feature columns in CSV: {missing_features}")

    target_cols = [c for c in df.columns if c.startswith('T_')]
    if not target_cols:
        raise ValueError("No target columns found.  Expected columns starting with 'T_'")

    X = df[feature_cols].copy()
    y = df[target_cols].copy().astype(int)

    return X, y, feature_cols, target_cols


def make_compatible_ohe():
    try:
        ohe = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    except TypeError:
        ohe = OneHotEncoder(handle_unknown='ignore', sparse=False)
    return ohe


def build_and_fit_transformer(X):
    cat_cols = ['region_encoded', 'industry_encoded']
    num_cols = ['month_num']
    ohe = make_compatible_ohe()
    transformer = ColumnTransformer(transformers=[
        ('cat', ohe, cat_cols),
        ('num', StandardScaler(), num_cols),
    ], remainder='drop')
    transformer.fit(X)
    return transformer


def transform_to_array(transformer, X):
    Xt = transformer.transform(X)
    try:
        from scipy import sparse
        if sparse.issparse(Xt):
            Xt = Xt.toarray()
    except Exception:
        if hasattr(Xt, "toarray"):
            Xt = Xt.toarray()
    Xt = np.asarray(Xt)
    return Xt


def train_models(X_tr, y_tr, random_state=42):
    models = {}

    # RandomForest with balanced class weights
    rf = MultiOutputClassifier(RandomForestClassifier(
        n_estimators=200,
        random_state=random_state,
        n_jobs=-1,
        class_weight='balanced'
    ), n_jobs=-1)
    print("Training RandomForest with class_weight='balanced'...")
    rf.fit(X_tr, y_tr)
    models['rf'] = rf

    if XGBClassifier is None:
        print("XGBoost not available; skipping XGB training.")
        models['xgb'] = None
    else:
        xgb_base = XGBClassifier(
            objective='binary:logistic',
            eval_metric='logloss',
            n_estimators=200,
            random_state=random_state,
            n_jobs=-1,
            verbosity=0
        )
        xgb = MultiOutputClassifier(xgb_base, n_jobs=-1)
        print("Training XGBoost...")
        xgb.fit(X_tr, y_tr)
        models['xgb'] = xgb

    return models


def evaluate_models(models, X_te, y_te, target_cols):
    results = {}

    for name, model in models.items():
        if model is None:
            results[name] = {"skipped": True}
            continue

        print(f"\n{'=' * 80}")
        print(f"EVALUATING: {name.upper()}")
        print(f"{'=' * 80}")

        y_pred = model.predict(X_te)
        y_pred = np.asarray(y_pred)
        y_true = np.asarray(y_te)

        # Overall metrics
        h_loss = float(hamming_loss(y_true, y_pred))
        subset_acc = float((y_pred == y_true).all(axis=1).mean())

        precision_micro = float(precision_score(y_true, y_pred, average='micro', zero_division=0))
        recall_micro = float(recall_score(y_true, y_pred, average='micro', zero_division=0))
        f1_micro = float(f1_score(y_true, y_pred, average='micro', zero_division=0))

        precision_macro = float(precision_score(y_true, y_pred, average='macro', zero_division=0))
        recall_macro = float(recall_score(y_true, y_pred, average='macro', zero_division=0))
        f1_macro = float(f1_score(y_true, y_pred, average='macro', zero_division=0))

        print(f"\nOVERALL METRICS:")
        print(f"  Hamming Loss:       {h_loss:.4f}")
        print(f"  Subset Accuracy:    {subset_acc:.4f}")
        print(f"\n  Micro Precision:    {precision_micro:.4f}")
        print(f"  Micro Recall:       {recall_micro:.4f}")
        print(f"  Micro F1:           {f1_micro:.4f}")
        print(f"\n  Macro Precision:    {precision_macro:.4f}")
        print(f"  Macro Recall:       {recall_macro:.4f}")
        print(f"  Macro F1:           {f1_macro:.4f}")

        # Per-label metrics
        print(f"\nPER-LABEL METRICS:")
        print(f"{'Label':<25} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Support':>10}")
        print(f"{'-' * 80}")

        per_label_metrics = {}
        for idx, col in enumerate(target_cols):
            y_t = y_true[:, idx]
            y_p = y_pred[:, idx]

            prec = float(precision_score(y_t, y_p, zero_division=0))
            rec = float(recall_score(y_t, y_p, zero_division=0))
            f1 = float(f1_score(y_t, y_p, zero_division=0))
            support = int(y_t.sum())

            per_label_metrics[col] = {
                "precision": prec,
                "recall": rec,
                "f1": f1,
                "support": support
            }

            print(f"{col:<25} {prec:>10.4f} {rec:>10.4f} {f1:>10.4f} {support:>10}")

        results[name] = {
            "hamming_loss": h_loss,
            "subset_accuracy": subset_acc,
            "precision_micro": precision_micro,
            "recall_micro": recall_micro,
            "f1_micro": f1_micro,
            "precision_macro": precision_macro,
            "recall_macro": recall_macro,
            "f1_macro": f1_macro,
            "per_label": per_label_metrics
        }

    return results


def save_artifacts(out_dir, transformer, models, target_cols, metrics):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    dump(transformer, out_dir / "feature_transformer.joblib")
    print(f"\nSaved feature transformer -> {out_dir / 'feature_transformer.joblib'}")

    if models.get('rf') is not None:
        dump(models['rf'], out_dir / "rf_multioutput.joblib")
        print(f"Saved RandomForest model -> {out_dir / 'rf_multioutput.joblib'}")

    if models.get('xgb') is not None:
        dump(models['xgb'], out_dir / "xgb_multioutput.joblib")
        print(f"Saved XGBoost model -> {out_dir / 'xgb_multioutput.joblib'}")

    with open(out_dir / "target_columns.json", "w") as f:
        json.dump(target_cols, f, indent=2)
    print(f"Saved target columns -> {out_dir / 'target_columns.json'}")

    with open(out_dir / "metrics_detailed.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved detailed metrics -> {out_dir / 'metrics_detailed.json'}")


def main():
    parser = argparse.ArgumentParser(description="Train multi-output RF and XGB on department dataset.")
    parser.add_argument("--dataset",
                        default="/home/ibrahim-sayys/Projects/ThreatLens/_dept_prediction_model/Preprocessing_on_DS/dataset_b_departments_v1.csv",
                        help="Path to processed dataset CSV")
    parser.add_argument("--out_dir", default="./models", help="Directory to save transformers and models")
    parser.add_argument("--test_size", type=float, default=0.2, help="Test split fraction")
    parser.add_argument("--random_state", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    print(f"\n{'=' * 80}")
    print(f"DEPARTMENT PREDICTION MODEL TRAINING")
    print(f"{'=' * 80}")
    print(f"Loading dataset from: {args.dataset}")

    try:
        df = load_data(args.dataset)
    except FileNotFoundError:
        print(f"Error: Dataset file not found at {args.dataset}")
        return

    print(f"Loaded {len(df)} rows and {len(df.columns)} columns.")

    X, y, feature_cols, target_cols = get_feature_and_targets(df)
    print(f"Feature columns: {feature_cols}")
    print(f"Number of target labels: {len(target_cols)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.random_state, shuffle=True
    )
    print(f"Train rows: {len(X_train)}, Test rows: {len(X_test)}")

    transformer = build_and_fit_transformer(X_train)
    X_train_t = transform_to_array(transformer, X_train)
    X_test_t = transform_to_array(transformer, X_test)

    models = train_models(X_train_t, y_train, random_state=args.random_state)

    metrics = evaluate_models(models, X_test_t, y_test, target_cols)

    save_artifacts(args.out_dir, transformer, models, target_cols, metrics)

    print(f"\n{'=' * 80}")
    print(f"ALL DONE!  Artifacts saved in: {args.out_dir}")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()