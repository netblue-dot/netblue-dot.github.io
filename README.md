# Geopolitical risk portfolio

Middle East maritime chokepoint and conflict analysis using Python, IMF PortWatch data and sourced event tracking.

## Red Sea shipping project
Question: how did Houthi attacks change ship traffic through Suez, Bab el-Mandeb and the Cape of Good Hope?

- red_sea_shipping.py: loads IMF PortWatch daily transits and charts traffic indexed to a Jan-Oct 2023 baseline
- red_sea_tracker.py: overlays dated Houthi events from data/events.csv on the 2026 chart
- data/events.csv: events with source and confidence labels (confirmed, single-source, claim)

Run: pip install pandas matplotlib openbb openbb-imf, then python red_sea_tracker.py
Data: IMF PortWatch (satellite AIS, UN Global Platform).
