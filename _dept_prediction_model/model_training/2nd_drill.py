#!/usr/bin/env python3
"""
dept_model_training_with_metrics.py

Train multi-output RandomForest and XGBoost classifiers and produce extended metrics
and class distribution artifacts.

Outputs (in --out_dir, default ./models):
- feature_transformer.joblib
- rf_multioutput.joblib
- xgb_multioutput.joblib
- target_columns.json
- metrics_detailed.json   <- expanded metrics per model
- class_distribution.json <- label counts, percentages, label cardinality/density

Usage:
    python dept_model_training_with_metrics.py --dataset /path/to/dataset.csv --out_dir ./models

Requires:
    pandas scikit-learn xgboost joblib numpy scipy (scipy optional for sparse detection)
"""
import argparse
import json
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from joblib import dump

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    hamming_loss,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
)
from sklearn.exceptions import NotFittedError

# XGBoost import (optional)
try:
    from xgboost import XGBClassifier
except Exception:
    XGBClassifier = None

# Utilities
def load_data(path):
    return pd.read_csv(path)

def get_feature_and_targets(df):
    feature_cols = ['region_encoded', 'industry_encoded', 'month_num']
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected feature columns: {missing}")
    target_cols = [c for c in df.columns if c.startswith('T_')]
    if not target_cols:
        raise ValueError("No target columns found (expected columns starting with 'T_').")
    X = df[feature_cols].copy()
    y = df[target_cols].copy().astype(int)
    return X, y, feature_cols, target_cols

def make_compatible_ohe():
    try:
        return OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown='ignore', sparse=False)

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

def to_dense_if_sparse(Xt):
    try:
        from scipy import sparse
        if sparse.issparse(Xt):
            return Xt.toarray()
    except Exception:
        if hasattr(Xt, "toarray"):
            return Xt.toarray()
    return np.asarray(Xt)

def train_models(X_tr, y_tr, random_state=42):
    models = {}
    rf = MultiOutputClassifier(RandomForestClassifier(
        n_estimators=200, random_state=random_state, n_jobs=-1
    ), n_jobs=-1)
    print("Training RandomForest...")
    rf.fit(X_tr, y_tr)
    models['rf'] = rf

    if XGBClassifier is None:
        print("XGBoost not available; skipping XGB.")
        models['xgb'] = None
    else:
        xgb_base = XGBClassifier(
            objective='binary:logistic',
            use_label_encoder=False,
            eval_metric='logloss',
            n_estimators=200,
            random_state=random_state,
            n_jobs=-1,
            verbosity=0
        )
        xgb = MultiOutputClassifier(xgb_base, n_jobs=-1)
        print("Training XGBoost...")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            xgb.fit(X_tr, y_tr)
        models['xgb'] = xgb

    return models

def get_proba_matrix(model, X_t):
    """
    Return an (n_samples, n_labels) matrix with probability of positive class for each label.
    If not available, returns None.
    """
    if model is None:
        return None
    if not hasattr(model, "predict_proba"):
        return None
    try:
        proba_list = model.predict_proba(X_t)
        # MultiOutputClassifier.predict_proba returns a list of arrays (n_samples, n_classes)
        probs = []
        for arr in proba_list:
            # if binary, second column is prob of class 1; if single-col, take that col
            if arr.shape[1] >= 2:
                probs.append(arr[:, 1])
            else:
                probs.append(arr[:, 0])
        probs = np.vstack(probs).T  # shape (n_samples, n_labels)
        return probs
    except Exception:
        return None

def compute_metrics_for_model(model, X_te, y_te, target_cols):
    res = {}
    try:
        y_pred = model.predict(X_te)
    except Exception as e:
        return {"error": str(e)}
    y_pred = np.asarray(y_pred)
    y_true = np.asarray(y_te)

    # Basic multi-label metrics
    res["hamming_loss"] = float(hamming_loss(y_true, y_pred))
    # Subset accuracy (exact match)
    res["subset_accuracy"] = float((y_pred == y_true).all(axis=1).mean())

    # Aggregated precision/recall/f1 (micro/macro/weighted)
    for avg in ("micro", "macro", "weighted"):
        try:
            res[f"precision_{avg}"] = float(precision_score(y_true, y_pred, average=avg, zero_division=0))
            res[f"recall_{avg}"] = float(recall_score(y_true, y_pred, average=avg, zero_division=0))
            res[f"f1_{avg}"] = float(f1_score(y_true, y_pred, average=avg, zero_division=0))
        except Exception:
            res[f"precision_{avg}"] = None
            res[f"recall_{avg}"] = None
            res[f"f1_{avg}"] = None

    # Per-label metrics
    per_label = {}
    for idx, col in enumerate(target_cols):
        y_t = y_true[:, idx]
        y_p = y_pred[:, idx]
        # counts
        pos = int(y_t.sum())
        neg = int(len(y_t) - pos)
        # confusion
        tn, fp, fn, tp = confusion_matrix(y_t, y_p, labels=[0,1]).ravel().tolist()
        prec = float(precision_score(y_t, y_p, zero_division=0))
        rec = float(recall_score(y_t, y_p, zero_division=0))
        f1 = float(f1_score(y_t, y_p, zero_division=0))
        per_label[col] = {
            "positive_count": pos,
            "negative_count": neg,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
            "accuracy": float((y_t == y_p).mean())
        }
    res["per_label"] = per_label

    # Prob-based metrics (AUC, average precision) if probabilities available
    proba = get_proba_matrix(model, X_te)
    aucs = {}
    aps = {}
    if proba is not None:
        for idx, col in enumerate(target_cols):
            y_t = y_true[:, idx]
            y_s = proba[:, idx]
            # Only compute if there are both positive and negative examples
            if len(np.unique(y_t)) == 2:
                try:
                    aucs[col] = float(roc_auc_score(y_t, y_s))
                except Exception:
                    aucs[col] = None
                try:
                    aps[col] = float(average_precision_score(y_t, y_s))
                except Exception:
                    aps[col] = None
            else:
                aucs[col] = None
                aps[col] = None
    else:
        for col in target_cols:
            aucs[col] = None
            aps[col] = None

    res["per_label_auc"] = aucs
    res["per_label_avg_precision"] = aps

    return res

def compute_class_distribution(y_df, target_cols):
    dist = {}
    total_samples = len(y_df)
    positives_per_sample = y_df.sum(axis=1).sum()
    label_cardinality = float(positives_per_sample / total_samples) if total_samples > 0 else 0.0
    label_density = float(label_cardinality / len(target_cols)) if len(target_cols) > 0 else 0.0

    for col in target_cols:
        pos = int(y_df[col].sum())
        neg = int(len(y_df) - pos)
        pct = float(pos / len(y_df)) if len(y_df) > 0 else 0.0
        dist[col] = {
            "positive_count": pos,
            "negative_count": neg,
            "positive_percentage": pct
        }
    return {
        "total_samples": int(total_samples),
        "n_labels": int(len(target_cols)),
        "label_cardinality": label_cardinality,
        "label_density": label_density,
        "per_label": dist
    }

def save_artifacts(out_dir, transformer, models, target_cols, metrics, class_dist):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    dump(transformer, out_dir / "feature_transformer.joblib")
    if models.get('rf') is not None:
        dump(models['rf'], out_dir / "rf_multioutput.joblib")
    if models.get('xgb') is not None:
        dump(models['xgb'], out_dir / "xgb_multioutput.joblib")

    with open(out_dir / "target_columns.json", "w") as f:
        json.dump(target_cols, f, indent=2)

    with open(out_dir / "metrics_detailed.json", "w") as f:
        json.dump(metrics, f, indent=2)

    with open(out_dir / "class_distribution.json", "w") as f:
        json.dump(class_dist, f, indent=2)

    print(f"Artifacts saved to: {out_dir}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset",
                        default="/home/ibrahim-sayys/Projects/ThreatLens/_dept_prediction_model/Preprocessing_on_DS/dataset_b_departments_v1.csv")
    parser.add_argument("--out_dir", default="./models")
    parser.add_argument("--test_size", type=float, default=0.2)
    parser.add_argument("--random_state", type=int, default=42)
    args = parser.parse_args()

    print("Loading dataset:", args.dataset)
    df = load_data(args.dataset)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns.")

    X, y, feature_cols, target_cols = get_feature_and_targets(df)
    print("Feature cols:", feature_cols)
    print("Number of target labels:", len(target_cols))

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.random_state, shuffle=True
    )
    print(f"Train rows: {len(X_train)}, Test rows: {len(X_test)}")

    transformer = build_and_fit_transformer(X_train)
    X_train_t = to_dense_if_sparse(transformer.transform(X_train))
    X_test_t = to_dense_if_sparse(transformer.transform(X_test))

    models = train_models(X_train_t, y_train, random_state=args.random_state)

    print("Evaluating models on test set...")
    metrics = {}
    for name, model in models.items():
        if model is None:
            metrics[name] = {"skipped": True}
            continue
        print(f"Computing metrics for: {name}")
        try:
            metrics[name] = compute_metrics_for_model(model, X_test_t, y_test, target_cols)
        except Exception as e:
            metrics[name] = {"error": str(e)}

    class_dist = compute_class_distribution(pd.concat([y_train, y_test], axis=0).reset_index(drop=True), target_cols)

    # Print concise summary to stdout
    print("\n--- Class distribution summary ---")
    print(f"Total samples: {class_dist['total_samples']}")
    print(f"Number of labels: {class_dist['n_labels']}")
    print(f"Label cardinality (avg labels/sample): {class_dist['label_cardinality']:.4f}")
    print(f"Label density: {class_dist['label_density']:.6f}")
    print("\nPer-label positive percentages (top 10 shown):")
    sorted_labels = sorted(class_dist['per_label'].items(), key=lambda kv: kv[1]['positive_percentage'], reverse=True)
    for col, info in sorted_labels[:10]:
        print(f"  {col}: {info['positive_count']} positives ({info['positive_percentage']*100:.2f}%)")

    # Save artifacts
    save_artifacts(args.out_dir, transformer, models, target_cols, metrics, class_dist)

if __name__ == "__main__":
    main()