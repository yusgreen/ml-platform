"""Exploratory data analysis helpers."""

import numpy as np
import pandas as pd

try:
    import matplotlib

    matplotlib.use("Agg")
except Exception:
    pass


def _num(v):
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    return v


def compute_summary(df: pd.DataFrame) -> dict:
    df = df.copy()
    rows, cols = df.shape
    columns = [str(c) for c in df.columns]
    dtypes = {str(c): str(t) for c, t in df.dtypes.items()}
    missing = {str(c): int(df[c].isna().sum()) for c in df.columns}

    numeric_summary = {}
    try:
        desc = df.describe()
        for col in desc.columns:
            s = desc[col]
            numeric_summary[str(col)] = {
                "count": _num(s.get("count")),
                "mean": _num(s.get("mean")),
                "std": _num(s.get("std")),
                "min": _num(s.get("min")),
                "25%": _num(s.get("25%")),
                "50%": _num(s.get("50%")),
                "75%": _num(s.get("75%")),
                "max": _num(s.get("max")),
            }
    except Exception:
        numeric_summary = {}

    categorical_summary = {}
    try:
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        for col in cat_cols:
            vc = df[col].value_counts(dropna=False).head(10)
            categorical_summary[str(col)] = {str(k): int(v) for k, v in vc.items()}
    except Exception:
        categorical_summary = {}

    correlation = []
    try:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(num_cols) >= 2:
            corr_df = df[num_cols].corr()
            all_pairs = len(df.columns) <= 10
            for i in range(len(num_cols)):
                for j in range(i + 1, len(num_cols)):
                    a = num_cols[i]
                    b = num_cols[j]
                    try:
                        val = corr_df.loc[a, b]
                    except Exception:
                        continue
                    if pd.isna(val):
                        continue
                    val = float(val)
                    if all_pairs or abs(val) > 0.3:
                        correlation.append({"a": str(a), "b": str(b), "value": val})
    except Exception:
        correlation = []

    return {
        "shape": [int(rows), int(cols)],
        "columns": columns,
        "dtypes": dtypes,
        "missing": missing,
        "numeric_summary": numeric_summary,
        "categorical_summary": categorical_summary,
        "correlation": correlation,
    }


def generate_plots(df: pd.DataFrame, out_dir) -> list:
    from pathlib import Path

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    filenames = []

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import seaborn as sns
    except Exception:
        return filenames

    # Missing values bar
    try:
        missing_counts = df.isna().sum()
        missing_counts = missing_counts[missing_counts > 0]
        if not missing_counts.empty:
            fig, ax = plt.subplots(figsize=(8, 4))
            missing_counts.plot(kind="bar", ax=ax, color="salmon")
            ax.set_title("Missing Values by Column")
            ax.set_ylabel("Count")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            fn = "missing_values.png"
            fig.savefig(out_dir / fn, dpi=100)
            plt.close(fig)
            filenames.append(fn)
    except Exception:
        try:
            plt.close("all")
        except Exception:
            pass

    # Correlation heatmap
    try:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(num_cols) >= 2:
            corr = df[num_cols].corr()
            size = max(6, len(num_cols))
            fig, ax = plt.subplots(figsize=(size, size - 1))
            sns.heatmap(
                corr,
                annot=len(num_cols) <= 12,
                fmt=".2f",
                cmap="coolwarm",
                center=0,
                ax=ax,
            )
            ax.set_title("Correlation Heatmap")
            plt.tight_layout()
            fn = "correlation_heatmap.png"
            fig.savefig(out_dir / fn, dpi=100)
            plt.close(fig)
            filenames.append(fn)
    except Exception:
        try:
            plt.close("all")
        except Exception:
            pass

    # Histograms
    try:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()[:6]
        if num_cols:
            n = len(num_cols)
            ncols = 3
            nrows = (n + ncols - 1) // ncols
            fig, axes = plt.subplots(nrows, ncols, figsize=(12, 3 * nrows))
            axes = np.atleast_1d(axes).reshape(-1)
            for idx, c in enumerate(num_cols):
                ax = axes[idx]
                try:
                    sns.histplot(df[c].dropna(), kde=False, ax=ax, bins=20)
                except Exception:
                    ax.hist(df[c].dropna(), bins=20)
                ax.set_title(str(c))
            for idx in range(n, len(axes)):
                axes[idx].set_visible(False)
            plt.tight_layout()
            fn = "histograms.png"
            fig.savefig(out_dir / fn, dpi=100)
            plt.close(fig)
            filenames.append(fn)
    except Exception:
        try:
            plt.close("all")
        except Exception:
            pass

    # Categorical bars
    try:
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()[:6]
        if cat_cols:
            n = len(cat_cols)
            ncols = 2
            nrows = (n + ncols - 1) // ncols
            fig, axes = plt.subplots(nrows, ncols, figsize=(12, 4 * nrows))
            axes = np.atleast_1d(axes).reshape(-1)
            for idx, c in enumerate(cat_cols):
                ax = axes[idx]
                vc = df[c].astype(str).value_counts().head(10)
                try:
                    sns.barplot(x=vc.values, y=vc.index, ax=ax, orient="h")
                except Exception:
                    ax.barh(vc.index.astype(str), vc.values)
                ax.set_title(str(c))
            for idx in range(n, len(axes)):
                axes[idx].set_visible(False)
            plt.tight_layout()
            fn = "categorical_bars.png"
            fig.savefig(out_dir / fn, dpi=100)
            plt.close(fig)
            filenames.append(fn)
    except Exception:
        try:
            plt.close("all")
        except Exception:
            pass

    return filenames
