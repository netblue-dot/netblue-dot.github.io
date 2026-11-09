"""
Adds Houthi event markers to the PortWatch transit chart.

Run after red_sea_shipping.py is in the same folder:
    python red_sea_tracker.py

Needs data/events.csv with columns: date, type, label, source, confidence.
Add new rows as you track incidents (check UKMTO / JMIC advisories and ACLED).
Types used for styling: ship_attack, policy, escalation, incident.

Outputs (./output):
    events_on_transits.png   transit index since SINCE with numbered event markers
    events_table.csv         numbered event list for the project page
    events_monthly.csv       ship attacks per month, for Tableau Public
    monthly_index.csv        monthly average index per route since SINCE
    data/portwatch_snapshot.json   saved copy of the data for red-sea-live.html
"""

import json
from datetime import date
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

import red_sea_shipping as rs

EVENTS_FILE = Path("data/events.csv")
SINCE = "2026-01-01"
STYLE = {
    "ship_attack": ("#c2410c", "v", "Ship attack"),
    "policy": ("#1d4e66", "s", "Declaration or policy"),
    "escalation": ("#6b21a8", "D", "Escalation"),
    "incident": ("#7a8890", "o", "Unattributed incident"),
}


def load_events() -> pd.DataFrame:
    if not EVENTS_FILE.exists():
        raise SystemExit(f"Missing {EVENTS_FILE}.")
    ev = pd.read_csv(EVENTS_FILE, parse_dates=["date"]).sort_values("date")
    missing = {"date", "type", "label", "source", "confidence"} - set(ev.columns)
    if missing:
        raise SystemExit(f"events.csv is missing columns: {missing}")
    return ev.reset_index(drop=True)


def plot_events(index: pd.DataFrame, ev: pd.DataFrame) -> None:
    rs.OUT.mkdir(exist_ok=True)
    recent = index.loc[SINCE:]
    ev_recent = ev[ev["date"] >= SINCE].reset_index(drop=True)
    colours = {"Suez Canal": "#1d4e66", "Bab el-Mandeb Strait": "#c2410c", "Cape of Good Hope": "#55656f"}

    fig, ax = plt.subplots(figsize=(11, 5.8))
    for name in rs.CHOKEPOINTS:
        if name in recent:
            ax.plot(recent.index, recent[name], label=name, color=colours[name], linewidth=1.8)
    ax.axhline(100, color="#c9d2d3", linewidth=1)

    ref = recent["Bab el-Mandeb Strait"].dropna()
    seen_types = set()
    placed = {}   # events that land on the same point share one label, e.g. "7, 8"
    for i, row in ev_recent.iterrows():
        colour, marker, name = STYLE.get(row["type"], ("black", "o", row["type"]))
        # place the marker on the Bab el-Mandeb line at the nearest date with data
        pos = ref.index.get_indexer([row["date"]], method="nearest")[0]
        x, y = ref.index[pos], ref.iloc[pos]
        ax.scatter([x], [y], marker=marker, s=70, color=colour, zorder=5,
                   label=name if row["type"] not in seen_types else None)
        seen_types.add(row["type"])
        placed.setdefault((x, y), []).append(i + 1)
    for (x, y), nums in placed.items():
        ax.annotate(", ".join(map(str, nums)), (x, y), textcoords="offset points", xytext=(0, 9),
                    ha="center", fontsize=9, fontweight="bold")

    ax.set_title(f"Daily transits since {SINCE[:4]} (index, 100 = Jan-Oct 2023) with Houthi events", loc="left")
    ax.set_ylabel("Index, 7-day average")
    ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.08))
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, "Sources: IMF PortWatch (AIS); events from events.csv. Numbers match events_table.csv.",
             fontsize=8, color="#55656f")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(rs.OUT / "events_on_transits.png", dpi=160)
    print(f"Saved {rs.OUT / 'events_on_transits.png'}")

    table = ev_recent.copy()
    table.insert(0, "no", table.index + 1)
    table.to_csv(rs.OUT / "events_table.csv", index=False)
    print(f"Saved {rs.OUT / 'events_table.csv'}")


def export_snapshot(df: pd.DataFrame) -> None:
    """Saved copy of the data for the live page, used when the PortWatch server cannot be reached."""
    d = df[df["date"] >= "2023-01-01"]
    rows = [{"date": r.date.strftime("%Y-%m-%d"), "portname": r.chokepoint, "n_total": float(r.transits)}
            for r in d.itertuples()]
    Path("data").mkdir(exist_ok=True)
    out = Path("data/portwatch_snapshot.json")
    out.write_text(json.dumps({"fetched": date.today().isoformat(), "rows": rows}), encoding="utf-8")
    print(f"Saved {out} ({len(rows)} rows)")


def print_stats(index: pd.DataFrame) -> None:
    """Monthly average index since SINCE: the exact numbers to quote on the project page."""
    m = index.loc[SINCE:].resample("MS").mean().round(0)
    m.index = m.index.strftime("%Y-%m")
    print(f"\nAverage index by month (100 = Jan-Oct 2023 average):")
    print(m.to_string())
    m.to_csv(rs.OUT / "monthly_index.csv")
    print(f"Saved {rs.OUT / 'monthly_index.csv'}")


def monthly_attacks(ev: pd.DataFrame) -> None:
    attacks = ev[ev["type"] == "ship_attack"]
    counts = attacks.groupby(attacks["date"].dt.to_period("M")).size().rename("ship_attacks")
    counts.to_csv(rs.OUT / "events_monthly.csv")
    print(f"Saved {rs.OUT / 'events_monthly.csv'}")


def main() -> None:
    df = rs.load_raw()
    export_snapshot(df)
    index, summary = rs.analyse(df)
    ev = load_events()
    plot_events(index, ev)
    print_stats(index)
    monthly_attacks(ev)


if __name__ == "__main__":
    main()
