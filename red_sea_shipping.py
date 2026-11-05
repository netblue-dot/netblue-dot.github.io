"""
Red Sea shipping after the Houthi attacks: IMF PortWatch chokepoint analysis.

Question: how far did daily transits through Suez and Bab el-Mandeb fall after
the Houthi attacks on commercial ships began in late 2023, and how much traffic
moved to the Cape of Good Hope?

Data: IMF PortWatch daily chokepoint transit calls (satellite AIS data).

Setup:
    pip install pandas matplotlib requests

Data sources, tried in order:
  A) Automatic: the PortWatch ArcGIS service (needs only pandas, matplotlib, requests), then OpenBB.
  B) Manual: download the daily chokepoint data from portwatch.imf.org, save it
     as data/chokepoints.csv. The script finds the date, name and transit-count
     columns by keyword, so exact column names do not matter.

Outputs (in ./output):
    transits_index.png   chart for your portfolio thumbnail
    monthly_summary.csv  load this into Tableau Public for an interactive version
"""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

CHOKEPOINTS = ["Suez Canal", "Bab el-Mandeb Strait", "Cape of Good Hope"]
BASELINE_START = "2023-01-01"
BASELINE_END = "2023-10-31"      # before the attacks on commercial shipping
EVENT_DATE = "2023-11-19"        # Galaxy Leader seizure; edit if you prefer another marker
START_DATE = "2019-01-01"

DATA_FILE = Path("data/chokepoints.csv")
OUT = Path("output")


ARCGIS_URL = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
              "Daily_Chokepoints_Data/FeatureServer/0/query")


def load_arcgis() -> pd.DataFrame:
    """Download daily chokepoint data straight from the PortWatch service (1000 rows per call)."""
    import requests
    where = "portid='CHOKEPOINT1' OR portid='CHOKEPOINT4' OR portid='CHOKEPOINT7'"
    rows, offset = [], 0
    for _ in range(100):  # safety limit
        r = requests.get(ARCGIS_URL, params={
            "where": where, "outFields": "date,portid,portname,n_total", "outSR": 4326,
            "f": "json", "orderByFields": "portid,date",
            "resultOffset": offset, "resultRecordCount": 1000,
        }, timeout=60)
        r.raise_for_status()
        feats = r.json().get("features", [])
        if not feats:
            break
        rows += [f["attributes"] for f in feats]
        offset += len(feats)
    if not rows:
        raise ValueError("service returned no rows")
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], unit="ms")
    return df


def load_raw() -> pd.DataFrame:
    """Return a dataframe with columns: date, chokepoint, transits."""
    df = None
    try:
        df = load_arcgis()
        print("Loaded data from the PortWatch ArcGIS service.")
    except Exception as err:
        print(f"ArcGIS download failed ({err}).")

    if df is None:
        try:
            from openbb import obb
            res = obb.economy.shipping.chokepoint_volume(
                provider="imf",
                chokepoint="suez_canal,bab_el_mandeb_strait,cape_of_good_hope",
                start_date=START_DATE,
            )
            df = res.to_df().reset_index()
            print("Loaded data through OpenBB.")
        except Exception as err:
            print(f"OpenBB load failed ({err}). Trying {DATA_FILE}.")

    if df is None:
        if not DATA_FILE.exists():
            raise SystemExit(
                f"No data. Download PortWatch daily chokepoint data to {DATA_FILE}."
            )
        df = pd.read_csv(DATA_FILE)

    return normalise(df)


def find_col(df: pd.DataFrame, keywords: list[str]) -> str:
    for col in df.columns:
        low = str(col).lower()
        if any(k in low for k in keywords):
            return col
    raise KeyError(f"No column matching {keywords}. Columns found: {list(df.columns)}")


def normalise(df: pd.DataFrame) -> pd.DataFrame:
    date_col = find_col(df, ["date"])
    name_col = find_col(df, ["portname", "chokepoint", "name"])
    # Prefer a total-transit count; fall back to any column with "transit" or "calls".
    try:
        val_col = find_col(df, ["n_total", "ntotal", "total"])
    except KeyError:
        val_col = find_col(df, ["transit", "calls", "count"])

    out = pd.DataFrame({
        "date": pd.to_datetime(df[date_col], errors="coerce", utc=True).dt.tz_localize(None).dt.normalize(),
        "chokepoint": df[name_col].astype(str).str.replace("_", " ").str.strip(),
        "transits": pd.to_numeric(df[val_col], errors="coerce"),
    }).dropna()

    # Match names loosely so "suez_canal" and "Suez Canal" both work.
    def canon(name: str) -> str | None:
        n = name.lower().replace("-", " ").replace("strait", "").strip()
        for target in CHOKEPOINTS:
            if target.lower().replace("-", " ").replace("strait", "").strip() == n:
                return target
        return None

    out["chokepoint"] = out["chokepoint"].map(canon)
    out = out.dropna(subset=["chokepoint"])
    return out[out["date"] >= START_DATE].sort_values(["chokepoint", "date"])


def analyse(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    wide = df.pivot_table(index="date", columns="chokepoint", values="transits", aggfunc="sum")
    wide = wide.asfreq("D")
    smooth = wide.rolling(7, min_periods=4).mean()

    baseline = wide.loc[BASELINE_START:BASELINE_END].mean()
    index = smooth.divide(baseline) * 100   # 100 = average daily transits, Jan-Oct 2023

    monthly = wide.resample("MS").mean().round(1)
    monthly_idx = (wide.resample("MS").mean().divide(baseline) * 100).round(1)
    monthly_idx.columns = [f"{c} (index)" for c in monthly_idx.columns]
    summary = monthly.join(monthly_idx)
    return index, summary


def plot(index: pd.DataFrame) -> None:
    OUT.mkdir(exist_ok=True)
    colours = {"Suez Canal": "#1d4e66", "Bab el-Mandeb Strait": "#c2410c", "Cape of Good Hope": "#55656f"}

    fig, ax = plt.subplots(figsize=(11, 5.5))
    for name in CHOKEPOINTS:
        if name in index:
            ax.plot(index.index, index[name], label=name, color=colours[name], linewidth=1.8)

    ax.axhline(100, color="#c9d2d3", linewidth=1)
    ax.axvline(pd.Timestamp(EVENT_DATE), color="black", linestyle="--", linewidth=1)
    ax.text(pd.Timestamp(EVENT_DATE), ax.get_ylim()[1] * 0.97, "  Attacks on shipping begin",
            va="top", fontsize=9)

    ax.set_title("Daily ship transits through three routes, indexed to Jan-Oct 2023 (= 100)", loc="left")
    ax.set_ylabel("Index, 7-day average")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, "Source: IMF PortWatch, satellite AIS data (UN Global Platform).", fontsize=8, color="#55656f")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / "transits_index.png", dpi=160)
    print(f"Saved {OUT / 'transits_index.png'}")


def print_findings(index: pd.DataFrame) -> None:
    """Prints the numbers to quote in your write-up. Nothing is hard-coded."""
    post = index.loc["2024-01-01":]
    print("\nAverage index since Jan 2024 (100 = Jan-Oct 2023 average):")
    for name in CHOKEPOINTS:
        if name in post:
            print(f"  {name}: {post[name].mean():.0f}")
    print(f"Latest 7-day averages (date {index.dropna(how='all').index[-1].date()}):")
    print(index.dropna(how="all").iloc[-1].round(0).to_string())


def main() -> None:
    df = load_raw()
    index, summary = analyse(df)
    OUT.mkdir(exist_ok=True)
    summary.to_csv(OUT / "monthly_summary.csv")
    print(f"Saved {OUT / 'monthly_summary.csv'}")
    plot(index)
    print_findings(index)


if __name__ == "__main__":
    main()
