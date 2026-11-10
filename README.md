# Geopolitical risk portfolio

Middle East maritime chokepoint and conflict analysis using Python, IMF PortWatch data and sourced event tracking.

Live site: https://netblue-dot.github.io/

## Red Sea shipping project
Question: how did Houthi attacks change ship traffic through Suez, Bab el-Mandeb and the Cape of Good Hope?

- red_sea_shipping.py: loads IMF PortWatch daily transits and charts traffic indexed to a Jan-Oct 2023 baseline
- red_sea_tracker.py: overlays dated Houthi events from data/events.csv on the 2026 chart
- data/events.csv: events with source and confidence labels (confirmed, single-source, claim)
- red-sea.html, red-sea-live.html: the published charts

Run: pip install pandas matplotlib openbb openbb-imf, then python red_sea_tracker.py
Data: IMF PortWatch (satellite AIS, UN Global Platform).

## US-Iran escalation timeline
Question: how did the US-Iran conflict escalate from 28 February 2026, and what is happening now?

- us-iran-war.html: interactive timeline filtered by military, diplomacy, nuclear, Hormuz/maritime and economy/humanitarian events
- Each event links to its sources, labelled by type: government (CENTCOM, Treasury, State), UN (Security Council, OHCHR, OCHA, IAEA), World Bank, think tanks (ISW/CTP, CSIS, Chatham House, CFR) and news agencies (Reuters, AP, Al Jazeera)
- Includes a schematic Gulf map, a live day counter and one satellite before-and-after image

Limit: a dated snapshot (last updated 9 Nov 2026), not a live feed. Casualty and loss figures are as attributed by the named body.

## Displacement flows from Syria and Yemen
Question: where are displaced people moving, and which country is affected most?

- displacement-flows.html: animated flow map with a camera that flies between the Levant and the Gulf of Aden
- Compares displacement three ways: people displaced from their home country, refugees hosted, and 2026 surges
- Tracks Yemen's new displacement since 1 August using IOM DTM counts, with a then-and-now comparison against a 2017 baseline
- Sources: UNHCR, IOM, OCHA, the EU Agency for Asylum, Refugees International, and Reuters/AP/Al Jazeera reporting

Method: flows from Türkiye, Lebanon, Jordan, Iraq and Egypt into Syria are derived by applying UNHCR's returnee shares to 1.63 million returnees (30 April 2026). The map is a simplified vector drawing, so borders are indicative only.
Limit: a dated snapshot of published figures, not a live API feed.

## Notes
- Every figure is attributed to its source on the page. Where sources disagree, the page says so.
- Pages are single self-contained HTML files, hosted with GitHub Pages.
