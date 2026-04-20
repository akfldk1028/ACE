"""
Experiment 06: Cost Prediction from Topology Features
======================================================
Direction C — predict runtime cost (tokens, turns, duration) from
pre-execution topology features using regression models.

Train: exp01 summary_all.csv (v1, 13 patterns, ~1300 rows)
Holdout: exp05 summary.csv baseline rows (v2, 8 patterns, ~200 rows)

No additional experiments needed — pure analysis of existing data.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats as sp_stats

from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import r2_score, mean_absolute_error

from config import (
    PATTERN_CATEGORY,
    PATTERN_AGENT_COUNT,
    PATTERN_MAX_MESSAGES,
    RESULTS_DIR,
    BASE_DIR,
)

OUTPUT_DIR = RESULTS_DIR / "exp06"
FIGURES_DIR = BASE_DIR / "figures"

# v1 task_id prefix -> category mapping
V1_TASK_CATEGORY = {
    "fact": "factual",
    "anal": "analytical",
    "crea": "creative",
    "tech": "technical",
}

TARGETS = ["total_tokens", "turn_count", "duration_sec"]
TARGET_LABELS = {
    "total_tokens": "Total Tokens",
    "turn_count": "Turn Count",
    "duration_sec": "Duration (sec)",
}

MODEL_NAMES = ["LinearRegression", "Ridge", "Lasso", "RandomForest"]


def load_exp01() -> pd.DataFrame:
    """Load v1 data (exp01 summary_all.csv)."""
    path = RESULTS_DIR / "exp01" / "summary_all.csv"
    if not path.exists():
        path = RESULTS_DIR / "exp01" / "summary.csv"
    df = pd.read_csv(path)
    # Infer task_category from task_id prefix
    df["task_category"] = df["task_id"].str.split("_").str[0].map(V1_TASK_CATEGORY)
    # Drop error rows and zero-token rows
    df = df[df["error"].isna() | (df["error"] == "")].copy()
    df = df.dropna(subset=TARGETS)
    for col in TARGETS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=TARGETS)
    df = df[df["total_tokens"] > 0].copy()
    return df


def load_exp05_baseline() -> pd.DataFrame:
    """Load v2 baseline data (exp05 summary.csv, baseline rows only)."""
    path = RESULTS_DIR / "exp05" / "summary.csv"
    df = pd.read_csv(path)
    df = df[df["experiment_id"].str.contains("baseline", case=False)].copy()
    # Map task_id to category using task_suite.json
    task_suite_path = BASE_DIR / "task_suite.json"
    if task_suite_path.exists():
        with open(task_suite_path, encoding="utf-8") as f:
            tasks = json.load(f)
        task_map = {t["id"]: t.get("category", "unknown") for t in tasks}
        df["task_category"] = df["task_id"].map(task_map)
    else:
        df["task_category"] = df["task_id"].str.split("_").str[0]
    # Drop error rows
    df = df[df["error"].isna() | (df["error"] == "")].copy()
    for col in TARGETS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=TARGETS)
    return df


def build_features(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """Build feature matrix from topology + task metadata.

    Features:
    - pattern_category one-hot (S, A, B1, B2, C, D)
    - agent_count (int)
    - max_messages (int)
    - task_category one-hot (factual, analytical, creative, technical)
    """
    # Ensure pattern_category is populated
    if "pattern_category" not in df.columns or df["pattern_category"].isna().any():
        df["pattern_category"] = df["pattern"].map(PATTERN_CATEGORY)

    # Ensure max_messages column
    if "max_messages" not in df.columns:
        df["max_messages"] = df["pattern"].map(PATTERN_MAX_MESSAGES)

    feature_cols = []
    feature_arrays = []

    # pattern_category one-hot
    pat_cats = ["S", "A", "B1", "B2", "C", "D"]
    for cat in pat_cats:
        col_name = f"pat_{cat}"
        feature_cols.append(col_name)
        feature_arrays.append((df["pattern_category"] == cat).astype(int).values)

    # agent_count
    feature_cols.append("agent_count")
    feature_arrays.append(df["agent_count"].values.astype(float))

    # max_messages
    feature_cols.append("max_messages")
    feature_arrays.append(df["max_messages"].values.astype(float))

    # task_category one-hot
    task_cats = sorted(df["task_category"].dropna().unique())
    for cat in task_cats:
        col_name = f"task_{cat}"
        feature_cols.append(col_name)
        feature_arrays.append((df["task_category"] == cat).astype(int).values)

    # Interaction: agent_count * max_messages
    feature_cols.append("agents_x_maxmsg")
    feature_arrays.append(
        df["agent_count"].values.astype(float) * df["max_messages"].values.astype(float)
    )

    X = np.column_stack(feature_arrays)
    return X, feature_cols


def align_features(X_train: np.ndarray, cols_train: list[str],
                   X_test: np.ndarray, cols_test: list[str]) -> np.ndarray:
    """Align holdout features to training feature columns (handle missing/extra cols)."""
    test_df = pd.DataFrame(X_test, columns=cols_test)
    aligned = pd.DataFrame(0, index=range(len(test_df)), columns=cols_train)
    for col in cols_train:
        if col in test_df.columns:
            aligned[col] = test_df[col].values
    return aligned.values.astype(float)


def run_cv(X: np.ndarray, y: np.ndarray, target_name: str) -> list[dict]:
    """5-fold CV with 4 models. Returns list of result dicts."""
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    results = []

    models = {
        "LinearRegression": LinearRegression(),
        "Ridge": Ridge(alpha=1.0),
        "Lasso": Lasso(alpha=0.1, max_iter=5000),
        "RandomForest": RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
        ),
    }

    for name, model in models.items():
        r2_scores = cross_val_score(model, X, y, cv=kf, scoring="r2")
        mae_scores = -cross_val_score(model, X, y, cv=kf, scoring="neg_mean_absolute_error")

        results.append({
            "target": target_name,
            "model": name,
            "r2_mean": round(float(np.mean(r2_scores)), 4),
            "r2_std": round(float(np.std(r2_scores)), 4),
            "mae_mean": round(float(np.mean(mae_scores)), 2),
            "mae_std": round(float(np.std(mae_scores)), 2),
        })

    return results


def compute_feature_importance(X: np.ndarray, y: np.ndarray,
                                feature_names: list[str], target_name: str) -> pd.DataFrame:
    """Compute feature importance from RF and Ridge coefficients."""
    # RandomForest importances
    rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    rf_imp = rf.feature_importances_

    # Ridge coefficients (normalized)
    ridge = Ridge(alpha=1.0)
    ridge.fit(X, y)
    ridge_coef = np.abs(ridge.coef_)
    ridge_norm = ridge_coef / (ridge_coef.sum() + 1e-10)

    rows = []
    for i, feat in enumerate(feature_names):
        rows.append({
            "target": target_name,
            "feature": feat,
            "rf_importance": round(float(rf_imp[i]), 4),
            "ridge_importance": round(float(ridge_norm[i]), 4),
        })

    return pd.DataFrame(rows)


def predict_holdout(X_train: np.ndarray, y_train: np.ndarray,
                    X_test: np.ndarray, y_test: np.ndarray,
                    target_name: str) -> tuple[dict, np.ndarray]:
    """Train on v1, predict v2 holdout. Returns (metrics_dict, predictions)."""
    rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    y_pred = rf.predict(X_test)

    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    metrics = {
        "target": target_name,
        "holdout_r2": round(float(r2), 4),
        "holdout_mae": round(float(mae), 2),
        "n_train": len(y_train),
        "n_test": len(y_test),
    }
    return metrics, y_pred


def plot_composite(cv_results_df: pd.DataFrame,
                   importance_df: pd.DataFrame,
                   holdout_data: dict) -> None:
    """Create composite 4-panel figure (fig9_cost_prediction.png)."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    fig.suptitle("Cost Prediction from Topology Features (Direction C)", fontsize=14, fontweight="bold")

    # Panel A: CV R² comparison (bar chart)
    ax = axes[0, 0]
    pivot = cv_results_df.pivot(index="model", columns="target", values="r2_mean")
    pivot = pivot.reindex(MODEL_NAMES)
    pivot.plot(kind="bar", ax=ax, rot=15, width=0.7)
    ax.set_ylabel("R² (5-fold CV)")
    ax.set_title("(a) Cross-Validation R² by Model")
    ax.set_ylim(0, 1.0)
    ax.legend(title="Target", fontsize=8)
    ax.axhline(y=0.7, color="red", linestyle="--", alpha=0.5, label="R²=0.7 threshold")

    # Panel B: Feature importance (RF, for total_tokens)
    ax = axes[0, 1]
    imp_tokens = importance_df[importance_df["target"] == "total_tokens"].copy()
    imp_tokens = imp_tokens.sort_values("rf_importance", ascending=True)
    colors = ["#E45756" if v > 0.1 else "#4C78A8" for v in imp_tokens["rf_importance"]]
    ax.barh(imp_tokens["feature"], imp_tokens["rf_importance"], color=colors)
    ax.set_xlabel("RF Feature Importance")
    ax.set_title("(b) Feature Importance (Total Tokens)")

    # Panel C: Predicted vs Actual scatter (holdout, total_tokens)
    ax = axes[1, 0]
    if "total_tokens" in holdout_data:
        hd = holdout_data["total_tokens"]
        ax.scatter(hd["actual"], hd["predicted"], alpha=0.5, s=20, c="#4C78A8")
        lims = [
            min(min(hd["actual"]), min(hd["predicted"])),
            max(max(hd["actual"]), max(hd["predicted"])),
        ]
        ax.plot(lims, lims, "r--", alpha=0.5)
        ax.set_xlabel("Actual Total Tokens")
        ax.set_ylabel("Predicted Total Tokens")
        r2 = r2_score(hd["actual"], hd["predicted"])
        ax.set_title(f"(c) Holdout: Predicted vs Actual (R²={r2:.3f})")
    else:
        ax.text(0.5, 0.5, "No holdout data", ha="center", va="center", transform=ax.transAxes)
        ax.set_title("(c) Holdout: Predicted vs Actual")

    # Panel D: Predicted vs Actual scatter (holdout, duration_sec)
    ax = axes[1, 1]
    if "duration_sec" in holdout_data:
        hd = holdout_data["duration_sec"]
        ax.scatter(hd["actual"], hd["predicted"], alpha=0.5, s=20, c="#72B7B2")
        lims = [
            min(min(hd["actual"]), min(hd["predicted"])),
            max(max(hd["actual"]), max(hd["predicted"])),
        ]
        ax.plot(lims, lims, "r--", alpha=0.5)
        ax.set_xlabel("Actual Duration (sec)")
        ax.set_ylabel("Predicted Duration (sec)")
        r2 = r2_score(hd["actual"], hd["predicted"])
        ax.set_title(f"(d) Holdout: Duration Predicted vs Actual (R²={r2:.3f})")
    else:
        ax.text(0.5, 0.5, "No holdout data", ha="center", va="center", transform=ax.transAxes)
        ax.set_title("(d) Holdout: Duration Predicted vs Actual")

    plt.tight_layout()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FIGURES_DIR / "fig9_cost_prediction.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Figure saved: {out_path}")


def main():
    """Run full cost prediction analysis."""
    print("=" * 60)
    print("Exp06: Cost Prediction from Topology Features")
    print("=" * 60)

    # Load data
    print("\n[1] Loading data...")
    df_train = load_exp01()
    print(f"  exp01 (train): {len(df_train)} rows, "
          f"patterns={df_train['pattern'].nunique()}, "
          f"tasks={df_train['task_id'].nunique()}")

    try:
        df_holdout = load_exp05_baseline()
        print(f"  exp05 baseline (holdout): {len(df_holdout)} rows, "
              f"patterns={df_holdout['pattern'].nunique()}, "
              f"tasks={df_holdout['task_id'].nunique()}")
        has_holdout = len(df_holdout) > 0
    except Exception as e:
        print(f"  exp05 holdout not available: {e}")
        df_holdout = None
        has_holdout = False

    # Build features
    print("\n[2] Building features...")
    X_train, feat_cols_train = build_features(df_train)
    print(f"  Features ({len(feat_cols_train)}): {feat_cols_train}")
    print(f"  X_train shape: {X_train.shape}")

    # 5-fold CV
    print("\n[3] Running 5-fold CV (4 models x 3 targets)...")
    all_cv_results = []
    for target in TARGETS:
        y = df_train[target].values
        results = run_cv(X_train, y, target)
        all_cv_results.extend(results)
        best = max(results, key=lambda r: r["r2_mean"])
        print(f"  {target}: best R²={best['r2_mean']:.4f} ({best['model']})")

    cv_df = pd.DataFrame(all_cv_results)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cv_df.to_csv(OUTPUT_DIR / "cv_results.csv", index=False)
    print(f"  Saved: {OUTPUT_DIR / 'cv_results.csv'}")

    # Feature importance
    print("\n[4] Computing feature importance...")
    all_importance = []
    for target in TARGETS:
        y = df_train[target].values
        imp_df = compute_feature_importance(X_train, y, feat_cols_train, target)
        all_importance.append(imp_df)

    importance_df = pd.concat(all_importance, ignore_index=True)
    importance_df.to_csv(OUTPUT_DIR / "feature_importance.csv", index=False)
    print(f"  Saved: {OUTPUT_DIR / 'feature_importance.csv'}")

    # Top features per target
    for target in TARGETS:
        sub = importance_df[importance_df["target"] == target].nlargest(3, "rf_importance")
        top_feats = ", ".join(f"{r['feature']}({r['rf_importance']:.3f})"
                              for _, r in sub.iterrows())
        print(f"  {target} top-3: {top_feats}")

    # Holdout validation (v1 -> v2)
    print("\n[5] Holdout validation (train=exp01, test=exp05_baseline)...")
    holdout_data = {}
    holdout_metrics = []

    if has_holdout:
        X_test, feat_cols_test = build_features(df_holdout)
        X_test_aligned = align_features(X_train, feat_cols_train, X_test, feat_cols_test)

        for target in TARGETS:
            y_train = df_train[target].values
            y_test = df_holdout[target].values
            metrics, y_pred = predict_holdout(X_train, y_train, X_test_aligned, y_test, target)
            holdout_metrics.append(metrics)
            holdout_data[target] = {"actual": y_test.tolist(), "predicted": y_pred.tolist()}
            print(f"  {target}: R²={metrics['holdout_r2']:.4f}, MAE={metrics['holdout_mae']:.1f}")

        holdout_df = pd.DataFrame(holdout_metrics)
        holdout_df.to_csv(OUTPUT_DIR / "predictions_holdout.csv", index=False)
        print(f"  Saved: {OUTPUT_DIR / 'predictions_holdout.csv'}")
    else:
        print("  Skipped (no holdout data)")

    # Generate figure
    print("\n[6] Generating composite figure...")
    plot_composite(cv_df, importance_df, holdout_data)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    best_overall = cv_df.loc[cv_df.groupby("target")["r2_mean"].idxmax()]
    for _, row in best_overall.iterrows():
        status = "PASS" if row["r2_mean"] >= 0.7 else "BELOW 0.7"
        print(f"  {row['target']}: R²={row['r2_mean']:.4f} ({row['model']}) [{status}]")

    if holdout_metrics:
        print("\n  Holdout (v1->v2):")
        for m in holdout_metrics:
            status = "PASS" if m["holdout_r2"] >= 0.5 else "BELOW 0.5"
            print(f"    {m['target']}: R²={m['holdout_r2']:.4f} [{status}]")

    print(f"\n  All outputs: {OUTPUT_DIR}")
    print(f"  Figure: {FIGURES_DIR / 'fig9_cost_prediction.png'}")


if __name__ == "__main__":
    main()
