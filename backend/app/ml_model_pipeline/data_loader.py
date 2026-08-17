"""
backend/training/data_loader.py
================================
Block 1 — Load the NSL-KDD-style network connection dataset.

Priority order
--------------
1. Explicit csv_path supplied by the caller (e.g. --data flag on the CLI).
2. 'data.csv' in the project root directory (cached from a previous download).
3. Download from Google Drive as a last resort.

The Google Drive file ID is the same one used by the original pipeline.
"""

import os
import pandas as pd

GDRIVE_FILE_ID = "1AlZak8gC27ntWFR0-ZJ0tMxVWFac-XPf"
_DEFAULT_CSV   = "data.csv"


def load_data(csv_path: str | None = None, project_dir: str = ".") -> pd.DataFrame:
    """
    Load network connection data and return a raw DataFrame.

    Parameters
    ----------
    csv_path : str | None
        Explicit path to a local CSV file.  If supplied and the file
        exists it is used immediately — no download is attempted.
    project_dir : str
        Project root; used to resolve the default 'data.csv' cache path
        and the download target.

    Returns
    -------
    pd.DataFrame  — raw data as stored in the CSV, no transformations applied.
    """
    # 1. Explicit path
    if csv_path and os.path.exists(csv_path):
        print(f"[data_loader] Using local file: {csv_path}")
        df = pd.read_csv(csv_path)
        _report(df)
        return df

    # 2. Cached default
    default = os.path.join(project_dir, _DEFAULT_CSV)
    if os.path.exists(default):
        print(f"[data_loader] Using cached local file: {default}")
        df = pd.read_csv(default)
        _report(df)
        return df

    # 3. Google Drive download
    print("[data_loader] No local file found — downloading from Google Drive…")
    import requests as _req
    url  = f"https://drive.google.com/uc?export=download&id={GDRIVE_FILE_ID}"
    resp = _req.get(url, timeout=120)
    resp.raise_for_status()
    with open(default, "wb") as fh:
        fh.write(resp.content)
    print(f"[data_loader] Download complete. Saved to: {default}")
    df = pd.read_csv(default)
    _report(df)
    return df


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _report(df: pd.DataFrame) -> None:
    print(f"[data_loader] Shape: {df.shape}  |  Columns: {list(df.columns)[:5]}…")
    print(df.dtypes.to_string())
    print(df.head(2).to_string())
