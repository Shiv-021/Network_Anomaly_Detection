"""
backend/training/eda/hypothesis_tests.py
==========================================
Step 4 — Five statistical hypothesis tests.

H1: srcbytes/dstbytes differ between normal and anomalous connections (Welch t-test)
H2: protocoltype distribution differs for normal vs anomaly (chi-square)
H3: service is associated with anomalies (chi-square)
H4: flag (connection status) is associated with anomalies (chi-square + logistic)
H5: urgent packets increase anomaly likelihood (logistic regression)
"""
import pandas as pd
from scipy import stats
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression


def run_tests(df: pd.DataFrame) -> dict:
    """Run all five tests. Returns dict of p-values."""
    ht: dict = {}

    # H1
    print("\n" + "=" * 70)
    print("HYPOTHESIS 1: srcbytes/dstbytes differ between normal and anomaly")
    print("=" * 70)
    t1, p1 = stats.ttest_ind(
        df[df["is_anomaly"] == 0]["srcbytes"],
        df[df["is_anomaly"] == 1]["srcbytes"],
        equal_var=False,
    )
    print(f"srcbytes  t-stat={t1:.3f}, p-value={p1:.6f}")
    ht["srcbytes_pval"] = float(p1)

    t2, p2 = stats.ttest_ind(
        df[df["is_anomaly"] == 0]["dstbytes"],
        df[df["is_anomaly"] == 1]["dstbytes"],
        equal_var=False,
    )
    print(f"dstbytes  t-stat={t2:.3f}, p-value={p2:.6f}")
    print("-> p < 0.05 means statistically significant difference")
    ht["dstbytes_pval"] = float(p2)

    # H2
    print("\n" + "=" * 70)
    print("HYPOTHESIS 2: protocoltype distribution differs for normal vs anomaly")
    print("=" * 70)
    ct_proto = pd.crosstab(df["protocoltype"], df["is_anomaly"])
    print(ct_proto)
    chi2, p, dof, _ = stats.chi2_contingency(ct_proto)
    print(f"Chi-square={chi2:.3f}, p-value={p:.6f}, dof={dof}")
    ht["protocoltype_pval"] = float(p)

    # H3
    print("\n" + "=" * 70)
    print("HYPOTHESIS 3: service is associated with anomalies")
    print("=" * 70)
    ct_svc = pd.crosstab(df["service"], df["is_anomaly"])
    chi2_s, p_s, dof_s, _ = stats.chi2_contingency(ct_svc)
    print(f"Chi-square={chi2_s:.3f}, p-value={p_s:.6f}, dof={dof_s}")
    print("\nTop 10 services by anomaly rate:")
    print(df.groupby("service")["is_anomaly"].mean().sort_values(ascending=False).head(10))
    ht["service_pval"] = float(p_s)

    # H4
    print("\n" + "=" * 70)
    print("HYPOTHESIS 4: flag (connection status) is associated with anomalies")
    print("=" * 70)
    ct_flag = pd.crosstab(df["flag"], df["is_anomaly"])
    print(ct_flag)
    chi2_f, p_f, dof_f, _ = stats.chi2_contingency(ct_flag)
    print(f"Chi-square={chi2_f:.3f}, p-value={p_f:.6f}, dof={dof_f}")
    ht["flag_pval"] = float(p_f)

    le_flag = LabelEncoder()
    tmp = df.copy()
    tmp["flag_encoded"] = le_flag.fit_transform(tmp["flag"])
    lr_flag = LogisticRegression()
    lr_flag.fit(tmp[["flag_encoded"]], tmp["is_anomaly"])
    print(f"Logistic regression coefficient for flag: {lr_flag.coef_[0][0]:.4f}")

    # H5
    print("\n" + "=" * 70)
    print("HYPOTHESIS 5: urgent packets increase anomaly likelihood")
    print("=" * 70)
    print(df.groupby("urgent")["is_anomaly"].mean())
    if df["urgent"].sum() > 0:
        lr_urgent = LogisticRegression()
        lr_urgent.fit(df[["urgent"]], df["is_anomaly"])
        print(f"Logistic regression coefficient for urgent: {lr_urgent.coef_[0][0]:.4f}")
    else:
        print("No urgent packets — feature may be near-constant in this dataset")

    return ht
